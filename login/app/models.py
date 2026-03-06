"""
Database models for OAuth user management and candidate data collection
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class User(Base):
    """
    User model to store authenticated OAuth users.
    Supports multiple OAuth providers (Google, GitHub, etc.)
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User information from OAuth provider
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    picture = Column(String(512), nullable=True)  # Profile picture URL

    # OAuth provider information
    provider = Column(String(50), nullable=False)  # e.g., "google", "github"
    provider_user_id = Column(String(255), nullable=False)  # Provider's unique ID for user

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps (automatically managed)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profiles = relationship("Candidate", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, provider={self.provider})>"

    def to_dict(self):
        """Convert user object to dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "provider": self.provider,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class TargetRole(str, enum.Enum):
    """Enum for target job roles"""
    ML_ENGINEER = "ML Engineer"
    DATA_ANALYST = "Data Analyst"
    DATA_ENGINEER = "Data Engineer"
    DATA_SCIENTIST = "Data Scientist"
    SOFTWARE_ENGINEER = "Software Engineer"
    DEVOPS_ENGINEER = "DevOps Engineer"


class ProcessingStatus(str, enum.Enum):
    """Enum for candidate profile processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    CV_PARSED = "cv_parsed"
    LINKEDIN_SCRAPED = "linkedin_scraped"
    GITHUB_ANALYZED = "github_analyzed"
    SKILLS_EXTRACTED = "skills_extracted"
    READY_FOR_RECOMMENDATIONS = "ready_for_recommendations"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    """Enum for document types"""
    CV = "cv"
    LINKEDIN_DATA = "linkedin_data"
    GITHUB_DATA = "github_data"


class Candidate(Base):
    """
    Candidate model to store candidate profile and data collection status.
    Links to User for authentication, stores URLs and target role.
    """
    __tablename__ = "candidates"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key to users table
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Profile information
    target_role = Column(SQLEnum(TargetRole), nullable=False, index=True)
    linkedin_url = Column(String(512), nullable=True)
    github_url = Column(String(512), nullable=True)

    # Processing status
    status = Column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Processing metadata
    error_message = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Extracted data (JSON stored as text)
    extracted_skills = Column(Text, nullable=True)  # JSON string of skills
    linkedin_profile_data = Column(Text, nullable=True)  # JSON string of LinkedIn data
    github_profile_data = Column(Text, nullable=True)  # JSON string of GitHub data
    
    # Analysis results from Personalized Learning Path module
    latest_analysis_date = Column(DateTime(timezone=True), nullable=True)  # Last analysis timestamp
    readiness_score = Column(Integer, nullable=True)  # 0-100 readiness score
    skill_gap_index = Column(Text, nullable=True)  # JSON string of skill gap metrics
    ai_explanation = Column(Text, nullable=True)  # AI-generated explanation from Qwen model
    matched_skills = Column(Text, nullable=True)  # JSON array of skills candidate has
    missing_skills = Column(Text, nullable=True)  # JSON array of skills candidate needs
    analysis_summary = Column(Text, nullable=True)  # Brief summary of analysis results

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="candidate_profiles")
    documents = relationship("CandidateDocument", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate(id={self.id}, user_id={self.user_id}, role={self.target_role}, status={self.status})>"

    def to_dict(self):
        """Convert candidate object to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_role": self.target_role.value if self.target_role else None,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "status": self.status.value if self.status else None,
            "error_message": self.error_message,
            "processing_started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "processing_completed_at": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CandidateDocument(Base):
    """
    CandidateDocument model to store uploaded documents and scraped data.
    Supports CV PDFs, LinkedIn data, GitHub data.
    """
    __tablename__ = "candidate_documents"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key to candidates table
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document metadata
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    original_filename = Column(String(512), nullable=True)
    stored_filename = Column(String(512), nullable=False)  # Unique filename in storage
    file_path = Column(String(1024), nullable=False)  # Full path to file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(128), nullable=True)

    # Processing status for this document
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Extracted content (for text extraction from CV)
    extracted_text = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="documents")

    def __repr__(self):
        return f"<CandidateDocument(id={self.id}, candidate_id={self.candidate_id}, type={self.document_type})>"

    def to_dict(self):
        """Convert document object to dictionary for API responses"""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "document_type": self.document_type.value if self.document_type else None,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "is_processed": self.is_processed,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
