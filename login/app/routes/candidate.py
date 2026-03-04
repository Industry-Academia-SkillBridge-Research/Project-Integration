"""
Candidate API Routes - Data collection and status endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, Candidate, TargetRole
from app.auth_utils import get_current_user
from app.services.candidate_service import CandidateService
from app.workers.candidate_processor import CandidateProcessor


router = APIRouter(prefix="/candidate", tags=["Candidate"])


@router.post("/init", status_code=status.HTTP_201_CREATED)
async def initialize_candidate_profile(
    cv_file: UploadFile = File(...),
    target_role: str = Form(...),
    linkedin_url: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize candidate profile with CV upload and data collection.
    
    Accepts:
    - cv_file: PDF file upload (multipart/form-data)
    - target_role: Target job role (ML Engineer, Data Analyst, Data Engineer, etc.)
    - linkedin_url: Optional LinkedIn profile URL
    - github_url: Optional GitHub profile URL
    
    Returns:
    - Candidate profile with status
    - Processing starts in background
    
    Authentication: Required (JWT Bearer token)
    """
    try:
        # Validate target role
        try:
            role_enum = TargetRole(target_role)
        except ValueError:
            valid_roles = [role.value for role in TargetRole]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_role. Must be one of: {', '.join(valid_roles)}"
            )

        # Validate CV file
        if not cv_file.content_type or "pdf" not in cv_file.content_type.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV file must be a PDF"
            )

        # Validate file size (max 10MB)
        cv_file.file.seek(0, 2)  # Seek to end
        file_size = cv_file.file.tell()
        cv_file.file.seek(0)  # Reset to beginning
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV file size must be less than 10MB"
            )

        # Create or update candidate profile
        candidate = CandidateService.get_or_create_candidate(
            db=db,
            user_id=current_user.id,
            target_role=role_enum,
            linkedin_url=linkedin_url,
            github_url=github_url
        )

        # Save CV file
        try:
            stored_filename, file_path, file_size = await CandidateService.save_cv_file(
                file=cv_file,
                candidate_id=candidate.id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Save CV document metadata
        CandidateService.save_cv_document(
            db=db,
            candidate_id=candidate.id,
            original_filename=cv_file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=cv_file.content_type
        )

        # Start background processing
        CandidateProcessor.start_processing_in_background(candidate.id)

        # Return response
        return {
            "status": "success",
            "message": "Candidate profile created successfully. Processing started in background.",
            "candidate": candidate.to_dict(),
            "processing": {
                "status": candidate.status.value,
                "message": "Your CV is being processed. Check status endpoint for updates."
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing candidate profile: {str(e)}"
        )


@router.get("/{candidate_id}/status")
async def get_candidate_status(
    candidate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get candidate profile processing status.
    
    Returns:
    - Current processing status
    - Progress details
    - Timestamps
    - Extracted data (when ready)
    
    Authentication: Required (JWT Bearer token)
    """
    try:
        # Get candidate
        candidate = CandidateService.get_candidate_by_id(db, candidate_id)
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found"
            )

        # Check authorization - user can only view their own profile
        if candidate.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this candidate profile"
            )

        # Get comprehensive status summary
        status_summary = CandidateService.get_candidate_status_summary(db, candidate_id)

        return {
            "status": "success",
            "data": status_summary
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching candidate status: {str(e)}"
        )


@router.get("/me")
async def get_my_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's candidate profile.
    
    Returns:
    - Candidate profile if exists
    - null if profile doesn't exist
    
    Authentication: Required (JWT Bearer token)
    """
    try:
        candidate = CandidateService.get_candidate_by_user_id(db, current_user.id)
        
        if not candidate:
            return {
                "status": "success",
                "data": None,
                "message": "No candidate profile found. Please create one."
            }

        # Get comprehensive status
        status_summary = CandidateService.get_candidate_status_summary(db, candidate.id)

        return {
            "status": "success",
            "data": status_summary
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching candidate profile: {str(e)}"
        )


@router.delete("/me")
async def delete_my_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's candidate profile and all associated data.
    
    WARNING: This will permanently delete:
    - Candidate profile
    - Uploaded CV file
    - All extracted data
    
    Authentication: Required (JWT Bearer token)
    """
    try:
        candidate = CandidateService.get_candidate_by_user_id(db, current_user.id)
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No candidate profile found"
            )

        # Delete candidate and all data
        success = CandidateService.delete_candidate_data(db, candidate.id)

        if success:
            return {
                "status": "success",
                "message": "Candidate profile and all associated data deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting candidate profile"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting candidate profile: {str(e)}"
        )


@router.get("/health")
async def candidate_health_check():
    """
    Health check endpoint for candidate service
    """
    return {
        "status": "healthy",
        "service": "candidate-service",
        "endpoints": {
            "init": "POST /candidate/init",
            "status": "GET /candidate/{candidate_id}/status",
            "my_profile": "GET /candidate/me",
            "delete": "DELETE /candidate/me"
        }
    }
