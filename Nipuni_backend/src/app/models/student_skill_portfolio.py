"""
Student Skill Portfolio Model

Stores persistent skill portfolio data for each student across all quiz attempts.
Uses flat skill structure - no parent/child hierarchy.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from ..db import Base


class StudentSkillPortfolio(Base):
    __tablename__ = "student_skill_portfolio"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)  # flat skill (e.g., "SQL", "Python")
    claimed_score = Column(Float, nullable=False, default=0.0)
    verified_score = Column(Float, nullable=False, default=0.0)
    quiz_weight = Column(Float, nullable=False, default=0.7)
    claimed_weight = Column(Float, nullable=False, default=0.3)
    final_score = Column(Float, nullable=False, default=0.0)
    final_level = Column(String(50), nullable=False, default="Beginner")
    correct_count = Column(Integer, nullable=False, default=0)
    total_questions = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('student_id', 'skill_name', name='uix_student_skill'),
    )

