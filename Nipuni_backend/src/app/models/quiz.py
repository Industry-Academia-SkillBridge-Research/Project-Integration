"""
Quiz planning and generation models.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime
from ..db import Base


class QuizPlan(Base):
    __tablename__ = "quiz_plan"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    skill_type = Column(String(50), nullable=False)  # "parent" or "child"
    skills_json = Column(Text, nullable=False)  # JSON list of skill names
    questions_per_skill = Column(Integer, nullable=False, default=4)
    difficulty_mix_json = Column(Text, nullable=False)  # JSON dict of difficulty mix
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempt"
    
    attempt_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    model_used = Column(String(100), nullable=False)  # e.g., "llama3.1:8b"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QuizQuestion(Base):
    __tablename__ = "quiz_question"
    
    question_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempt.attempt_id"), nullable=False, index=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)  # parent skill
    difficulty = Column(String(20), nullable=False)  # easy, medium, hard
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON dict {A, B, C, D}
    correct_option = Column(String(1), nullable=False)  # A, B, C, or D
    explanation = Column(Text, nullable=False)
