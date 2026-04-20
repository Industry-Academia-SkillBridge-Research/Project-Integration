from sqlalchemy import Column, String, Text
from ..db import Base


class Student(Base):
    __tablename__ = "students"
    
    student_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    program = Column(String(255), nullable=True)
    intake = Column(String(50), nullable=True)
    specialization = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)  # URL or base64 image
    bio = Column(Text, nullable=True)
