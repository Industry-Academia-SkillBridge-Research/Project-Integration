"""
Candidate Service - Business logic for candidate data collection and processing
"""
import os
import uuid
import shutil
import json
from datetime import datetime
from typing import Optional, BinaryIO, Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models import Candidate, CandidateDocument, User, ProcessingStatus, DocumentType, TargetRole
from app.config import settings


class CandidateService:
    """Service class for candidate profile management"""

    @staticmethod
    def create_storage_directories():
        """Create necessary storage directories if they don't exist"""
        cv_dir = Path(settings.CV_STORAGE_PATH)
        cv_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (cv_dir / "temp").mkdir(exist_ok=True)
        (cv_dir / "processed").mkdir(exist_ok=True)
        
        return cv_dir

    @staticmethod
    def generate_unique_filename(original_filename: str, candidate_id: int) -> str:
        """
        Generate a unique filename for storage
        Format: candidate_{id}_{uuid}_{original_name}
        """
        file_extension = Path(original_filename).suffix
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"candidate_{candidate_id}_{timestamp}_{unique_id}{file_extension}"

    @staticmethod
    async def save_cv_file(
        file: UploadFile,
        candidate_id: int
    ) -> tuple[str, str, int]:
        """
        Save uploaded CV file to storage
        
        Returns:
            tuple: (stored_filename, full_file_path, file_size)
        """
        # Validate file type
        if not file.content_type or "pdf" not in file.content_type.lower():
            raise ValueError("Only PDF files are allowed for CV upload")

        # Create storage directory
        storage_dir = CandidateService.create_storage_directories()

        # Generate unique filename
        stored_filename = CandidateService.generate_unique_filename(
            file.filename or "cv.pdf",
            candidate_id
        )
        
        file_path = storage_dir / stored_filename

        # Save file
        file_size = 0
        with open(file_path, "wb") as buffer:
            content = await file.read()
            file_size = len(content)
            buffer.write(content)

        return stored_filename, str(file_path), file_size

    @staticmethod
    def get_or_create_candidate(
        db: Session,
        user_id: int,
        target_role: TargetRole,
        linkedin_url: Optional[str] = None,
        github_url: Optional[str] = None
    ) -> Candidate:
        """
        Get existing candidate or create new one for a user
        """
        # Check if candidate already exists
        candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()

        if candidate:
            # Update existing candidate
            candidate.target_role = target_role
            candidate.linkedin_url = linkedin_url
            candidate.github_url = github_url
            candidate.status = ProcessingStatus.PENDING
            candidate.error_message = None
            candidate.processing_started_at = None
            candidate.processing_completed_at = None
            candidate.updated_at = datetime.utcnow()
        else:
            # Create new candidate
            candidate = Candidate(
                user_id=user_id,
                target_role=target_role,
                linkedin_url=linkedin_url,
                github_url=github_url,
                status=ProcessingStatus.PENDING
            )
            db.add(candidate)

        db.commit()
        db.refresh(candidate)
        return candidate

    @staticmethod
    def save_cv_document(
        db: Session,
        candidate_id: int,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str
    ) -> CandidateDocument:
        """
        Save CV document metadata to database
        """
        # Check if CV document already exists for this candidate
        existing_doc = db.query(CandidateDocument).filter(
            CandidateDocument.candidate_id == candidate_id,
            CandidateDocument.document_type == DocumentType.CV
        ).first()

        if existing_doc:
            # Delete old file if it exists
            if os.path.exists(existing_doc.file_path):
                os.remove(existing_doc.file_path)
            
            # Update existing document
            existing_doc.original_filename = original_filename
            existing_doc.stored_filename = stored_filename
            existing_doc.file_path = file_path
            existing_doc.file_size = file_size
            existing_doc.mime_type = mime_type
            existing_doc.is_processed = False
            existing_doc.processed_at = None
            existing_doc.extracted_text = None
            existing_doc.updated_at = datetime.utcnow()
            document = existing_doc
        else:
            # Create new document record
            document = CandidateDocument(
                candidate_id=candidate_id,
                document_type=DocumentType.CV,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                is_processed=False
            )
            db.add(document)

        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def get_candidate_by_user_id(db: Session, user_id: int) -> Optional[Candidate]:
        """Get candidate profile by user ID"""
        return db.query(Candidate).filter(Candidate.user_id == user_id).first()

    @staticmethod
    def get_candidate_by_id(db: Session, candidate_id: int) -> Optional[Candidate]:
        """Get candidate profile by candidate ID"""
        return db.query(Candidate).filter(Candidate.id == candidate_id).first()

    @staticmethod
    def update_candidate_status(
        db: Session,
        candidate_id: int,
        status: ProcessingStatus,
        error_message: Optional[str] = None
    ) -> Candidate:
        """Update candidate processing status"""
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            raise ValueError(f"Candidate with id {candidate_id} not found")

        candidate.status = status
        candidate.error_message = error_message
        candidate.updated_at = datetime.utcnow()

        # Update processing timestamps
        if status == ProcessingStatus.PROCESSING and not candidate.processing_started_at:
            candidate.processing_started_at = datetime.utcnow()
        
        if status in [ProcessingStatus.READY_FOR_RECOMMENDATIONS, ProcessingStatus.FAILED]:
            candidate.processing_completed_at = datetime.utcnow()

        db.commit()
        db.refresh(candidate)
        return candidate

    @staticmethod
    def get_candidate_status_summary(db: Session, candidate_id: int) -> dict:
        """
        Get comprehensive status summary for a candidate including analysis results
        """
        candidate = CandidateService.get_candidate_by_id(db, candidate_id)
        
        if not candidate:
            raise ValueError(f"Candidate with id {candidate_id} not found")

        # Get document counts
        documents = db.query(CandidateDocument).filter(
            CandidateDocument.candidate_id == candidate_id
        ).all()

        cv_document = next((d for d in documents if d.document_type == DocumentType.CV), None)
        
        # Parse JSON fields
        extracted_skills = json.loads(candidate.extracted_skills) if candidate.extracted_skills else None
        matched_skills = json.loads(candidate.matched_skills) if candidate.matched_skills else None
        missing_skills = json.loads(candidate.missing_skills) if candidate.missing_skills else None
        skill_gap_index = json.loads(candidate.skill_gap_index) if candidate.skill_gap_index else None
        recommended_courses = json.loads(candidate.recommended_courses) if getattr(candidate, 'recommended_courses', None) else None
        
        return {
            "candidate_id": candidate.id,
            "user_id": candidate.user_id,
            "target_role": candidate.target_role.value,
            "status": candidate.status.value,
            "error_message": candidate.error_message,
            "progress": {
                "cv_uploaded": cv_document is not None,
                "cv_processed": cv_document.is_processed if cv_document else False,
                "linkedin_url_provided": candidate.linkedin_url is not None,
                "linkedin_scraped": candidate.linkedin_profile_data is not None,
                "github_url_provided": candidate.github_url is not None,
                "github_analyzed": candidate.github_profile_data is not None,
                "skills_extracted": candidate.extracted_skills is not None,
            },
            "timestamps": {
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                "processing_started_at": candidate.processing_started_at.isoformat() if candidate.processing_started_at else None,
                "processing_completed_at": candidate.processing_completed_at.isoformat() if candidate.processing_completed_at else None,
            },
            "documents_count": len(documents),
            "ready_for_recommendations": candidate.status == ProcessingStatus.READY_FOR_RECOMMENDATIONS,
            # Analysis results (new fields)
            "analysis": {
                "latest_analysis_date": candidate.latest_analysis_date.isoformat() if candidate.latest_analysis_date else None,
                "readiness_score": candidate.readiness_score,
                "skill_gap_index": skill_gap_index,
                "ai_explanation": candidate.ai_explanation,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "analysis_summary": candidate.analysis_summary,
                "extracted_skills": extracted_skills,
                "recommended_courses": recommended_courses
            }
        }

    @staticmethod
    def delete_candidate_data(db: Session, candidate_id: int) -> bool:
        """
        Delete all candidate data including files
        """
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            return False

        # Delete all associated files
        documents = db.query(CandidateDocument).filter(
            CandidateDocument.candidate_id == candidate_id
        ).all()

        for doc in documents:
            if os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception as e:
                    print(f"Error deleting file {doc.file_path}: {e}")

        # Delete candidate (cascade will delete documents)
        db.delete(candidate)
        db.commit()
        
        return True

    @staticmethod
    def update_analysis_data(
        db: Session,
        user_id: int,
        readiness_score: Optional[int] = None,
        skill_gap_index: Optional[Any] = None,
        ai_explanation: Optional[str] = None,
        matched_skills: Optional[List[Dict]] = None,
        missing_skills: Optional[List[Dict]] = None,
        analysis_summary: Optional[str] = None,
        extracted_skills: Optional[List[str]] = None,
        recommended_courses: Optional[List[Dict]] = None
    ) -> Candidate:
        """
        Update candidate profile with analysis results from Personalized Learning Path module.
        
        Args:
            db: Database session
            user_id: User ID to find candidate
            readiness_score: Overall readiness score (0-100)
            skill_gap_index: Skill gap metrics
            ai_explanation: AI-generated explanation text
            matched_skills: List of skills candidate has
            missing_skills: List of skills candidate needs
            analysis_summary: Brief summary of analysis
            extracted_skills: Skills extracted from CV/profile
            recommended_courses: List of recommended courses
            
        Returns:
            Updated Candidate object
        """
        candidate = db.query(Candidate).filter(Candidate.user_id == user_id).first()
        
        if not candidate:
            # Auto-create a basic candidate record so analysis results can be stored
            # even if the user never did the traditional CV-upload onboarding flow
            candidate = Candidate(
                user_id=user_id,
                target_role=TargetRole.SOFTWARE_ENGINEER,  # default; updated later
                status=ProcessingStatus.READY_FOR_RECOMMENDATIONS
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

        # Update analysis fields
        candidate.latest_analysis_date = datetime.utcnow()
        
        if readiness_score is not None:
            candidate.readiness_score = readiness_score
            
        if skill_gap_index is not None:
            candidate.skill_gap_index = json.dumps(skill_gap_index)
            
        if ai_explanation is not None:
            candidate.ai_explanation = ai_explanation
            
        if matched_skills is not None:
            candidate.matched_skills = json.dumps(matched_skills)
            
        if missing_skills is not None:
            candidate.missing_skills = json.dumps(missing_skills)
            
        if analysis_summary is not None:
            candidate.analysis_summary = analysis_summary
            
        if extracted_skills is not None:
            candidate.extracted_skills = json.dumps(extracted_skills)
            
        if recommended_courses is not None:
            candidate.recommended_courses = json.dumps(recommended_courses)

        candidate.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(candidate)
        return candidate
