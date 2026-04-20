"""
Question Bank models for pre-generated MCQs.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from datetime import datetime
from ..db import Base


class QuestionBank(Base):
    __tablename__ = "question_bank"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_name = Column(String(255), nullable=False, index=True)  # parent skill
    difficulty = Column(String(20), nullable=False, index=True)  # easy|medium|hard
    question_text = Column(Text, nullable=False)  # Using TEXT for longer questions
    options_json = Column(Text, nullable=False)  # JSON string {"A":.."B":.."C":.."D":..}
    correct_option = Column(String(1), nullable=False)  # A|B|C|D
    explanation = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=False)  # e.g., "llama3.1:8b"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Note: Removed question_text from unique constraint for MySQL compatibility
    # Multiple questions per skill/difficulty are allowed
