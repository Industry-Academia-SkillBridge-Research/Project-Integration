"""
Quiz Answer model.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from ..db import Base


class QuizAnswer(Base):
    __tablename__ = "quiz_answer"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempt.attempt_id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("quiz_question.question_id"), nullable=False, index=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    selected_option = Column(String(1), nullable=False)  # A, B, C, or D
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
