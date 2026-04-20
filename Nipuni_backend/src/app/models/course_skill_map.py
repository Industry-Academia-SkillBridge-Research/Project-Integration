"""
Course-Skill Mapping Model

Stores direct course to skill mappings with weights.
No parent/child hierarchy - flat skill structure.
"""

from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from ..db import Base


class CourseSkillMap(Base):
    __tablename__ = "course_skill_map"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_code = Column(String(50), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    map_weight = Column(Float, nullable=False)  # 0.0 to 1.0
    
    __table_args__ = (
        UniqueConstraint('course_code', 'skill_name', name='uq_course_skill'),
    )
