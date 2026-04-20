"""
Unit tests for transcript parsing.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..services.transcript_service import parse_courses_from_text


def test_sliit_style_parsing():
    """Test parsing of SLIIT-style block format transcript."""
    
    # Sample SLIIT-style transcript text
    sample_text = """
IT1010
Introduction to Programming
1
4
A
IT1020
Computer Systems
1
3
B+
IT1030
Mathematics for Computing
1
4
A-
"""
    
    parsed_courses, warnings = parse_courses_from_text(sample_text)
    
    print("Parsed Courses:")
    print("-" * 60)
    for course in parsed_courses:
        print(f"Code: {course['course_code']}")
        print(f"  Title: {course.get('course_name', 'N/A')}")
        print(f"  Grade: {course['grade']}")
        print(f"  Credits: {course.get('credits', 'N/A')}")
        print(f"  Academic Year: {course.get('academic_year', 'N/A')}")
        print()
    
    print(f"Total courses parsed: {len(parsed_courses)}")
    if warnings:
        print(f"Warnings: {warnings}")
    
    # Assertions
    assert len(parsed_courses) == 3, f"Expected 3 courses, got {len(parsed_courses)}"
    
    # Check IT1010
    it1010 = next((c for c in parsed_courses if c['course_code'] == 'IT1010'), None)
    assert it1010 is not None, "IT1010 not found"
    assert it1010['grade'] == 'A', f"Expected grade A, got {it1010['grade']}"
    assert it1010['credits'] == 4.0, f"Expected credits 4.0, got {it1010['credits']}"
    assert it1010['academic_year'] == 1, f"Expected academic_year 1, got {it1010.get('academic_year')}"
    assert 'Introduction to Programming' in it1010.get('course_name', ''), \
        f"Expected title to contain 'Introduction to Programming', got {it1010.get('course_name')}"
    
    # Check IT1020
    it1020 = next((c for c in parsed_courses if c['course_code'] == 'IT1020'), None)
    assert it1020 is not None, "IT1020 not found"
    assert it1020['grade'] == 'B+', f"Expected grade B+, got {it1020['grade']}"
    assert it1020['credits'] == 3.0, f"Expected credits 3.0, got {it1020['credits']}"
    assert it1020['academic_year'] == 1, f"Expected academic_year 1, got {it1020.get('academic_year')}"
    
    # Check IT1030
    it1030 = next((c for c in parsed_courses if c['course_code'] == 'IT1030'), None)
    assert it1030 is not None, "IT1030 not found"
    assert it1030['grade'] == 'A-', f"Expected grade A-, got {it1030['grade']}"
    assert it1030['credits'] == 4.0, f"Expected credits 4.0, got {it1030['credits']}"
    assert it1030['academic_year'] == 1, f"Expected academic_year 1, got {it1030.get('academic_year')}"
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_sliit_style_parsing()
