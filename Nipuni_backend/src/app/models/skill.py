from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from ..db import Base


class SkillProfileClaimed(Base):
    """Student skill profile from transcript analysis (claimed skills)"""
    __tablename__ = "skill_profile_claimed"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    claimed_score = Column(Float, nullable=False)
    claimed_level = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SkillEvidence(Base):
    """Individual course contributions to skill scores"""
    __tablename__ = "skill_evidence"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    course_code = Column(String(50), nullable=False)
    map_weight = Column(Float, nullable=False)
    credits = Column(Float, nullable=False)
    grade = Column(String(10), nullable=False)
    grade_norm = Column(Float, nullable=False)
    academic_year = Column(Integer, nullable=True)
    recency = Column(Float, nullable=False)
    evidence_weight = Column(Float, nullable=False)
    contribution = Column(Float, nullable=False)

