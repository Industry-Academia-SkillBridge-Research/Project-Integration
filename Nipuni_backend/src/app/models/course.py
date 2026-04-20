from sqlalchemy import Column, Integer, String, Float, ForeignKey
from ..db import Base


class CourseTaken(Base):
    __tablename__ = "courses_taken"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False, index=True)
    course_code = Column(String(50), nullable=False, index=True)
    course_name = Column(String(255), nullable=True)
    grade = Column(String(10), nullable=False)
    year_taken = Column(Integer, nullable=True)
    credits = Column(Float, nullable=True)
    academic_year = Column(Integer, nullable=True)


class CourseCatalog(Base):
    __tablename__ = "course_catalog"
    
    course_code = Column(String(50), primary_key=True, index=True)
    course_name = Column(String(255), nullable=False)
    main_skill = Column(String(255), nullable=True)
    course_level = Column(String(50), nullable=True)
    credits = Column(Float, nullable=True)
    year = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)


class CourseSkillMap(Base):
    __tablename__ = "course_skill_map"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_code = Column(String(50), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    map_weight = Column(Float, nullable=False)
