"""
Service for handling transcript file uploads and parsing.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile
import fitz  # PyMuPDF
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pdfplumber not installed, table extraction unavailable")
from ..models.course import CourseTaken
from ..models.student import Student

logger = logging.getLogger(__name__)

# Resolve upload directory
BACKEND_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = BACKEND_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Debug output directory
OUTPUT_DIR = BACKEND_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_student_info(text: str) -> Dict:
    """
    Parse student information from transcript header.
    
    Args:
        text: Extracted text from transcript
        
    Returns:
        Dictionary with student information
    """
    student_info = {
        "name": None,
        "program": None,
        "intake": None,
        "specialization": None
    }
    
    # Split into lines
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for NAME OF CANDIDATE
        if 'NAME OF CANDIDATE' in line.upper():
            # Name might be on the same line or next line
            if len(line.split()) > 3:  # Name on same line
                student_info["name"] = ' '.join(line.split()[3:])
            elif i + 1 < len(lines):  # Name on next line
                student_info["name"] = lines[i + 1].strip()
        
        # Look for PROGRAMME
        if 'PROGRAMME' in line.upper() and 'NAME' not in line.upper():
            # Program might be on the same line or next line
            if len(line.split()) > 1:  # Program on same line
                student_info["program"] = ' '.join(line.split()[1:])
            elif i + 1 < len(lines):  # Program on next line
                student_info["program"] = lines[i + 1].strip()
        
        # Look for FIELD OF SPECIALIZATION
        if 'FIELD OF SPECIALIZATION' in line.upper():
            # Specialization might be on the same line or next line
            if len(line.split()) > 3:  # Specialization on same line
                student_info["specialization"] = ' '.join(line.split()[3:])
            elif i + 1 < len(lines):  # Specialization on next line
                student_info["specialization"] = lines[i + 1].strip()
        
        # Look for MONTH & YEAR OF ADMISSION or REGISTRATION DATE
        if ('MONTH' in line.upper() and 'YEAR' in line.upper() and 'ADMISSION' in line.upper()) or \
           ('REGISTRATION' in line.upper() and 'DATE' not in line.upper() and 'NO' not in line.upper()):
            # Intake might be on the same line or next line
            # Look for month/year pattern
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Check if next line has a date pattern (e.g., "October, 2020")
                if re.search(r'[A-Za-z]+,?\s*\d{4}', next_line):
                    student_info["intake"] = next_line
    
    logger.info(f"Parsed student info: {student_info}")
    return student_info


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text from PDF using PyMuPDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        logger.info(f"Extracted {len(text)} characters from PDF using PyMuPDF")
        return text
    except Exception as e:
        logger.error(f"PyMuPDF extraction failed: {e}")
        return ""


def extract_text_with_ocr(file_path: Path) -> str:
    """
    Extract text from PDF using OCR (pytesseract).
    Fallback when direct text extraction yields insufficient content.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        OCR extracted text
    """
    try:
        import pytesseract
        from PIL import Image
        
        text = ""
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image and OCR
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img)
                text += page_text + "\n"
                logger.debug(f"OCR extracted {len(page_text)} chars from page {page_num + 1}")
        
        logger.info(f"OCR extracted {len(text)} characters total")
        return text
    except ImportError:
        logger.warning("pytesseract not installed, OCR unavailable")
        return ""
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""


def extract_courses_from_tables(file_path: Path) -> Tuple[List[Dict], List[str]]:
    """
    Extract courses from PDF tables using pdfplumber.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Tuple of (parsed_courses, warnings)
    """
    if not PDFPLUMBER_AVAILABLE:
        return [], ["pdfplumber not available for table extraction"]
    
    parsed_courses = []
    warnings = []
    courses_dict = {}  # For deduplication
    
    # Regex patterns
    course_code_pattern = r"\b[A-Z]{2}\d{4}\b"
    grade_pattern = r"\b(A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D|F)\b"
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                if not tables:
                    continue
                
                logger.debug(f"Found {len(tables)} table(s) on page {page_num + 1}")
                
                for table_idx, table in enumerate(tables):
                    if not table:
                        continue
                    
                    for row_idx, row in enumerate(table):
                        if not row:
                            continue
                        
                        # Join all cells in the row into a single string
                        row_text = ' '.join([str(cell) if cell else '' for cell in row])
                        row_text = ' '.join(row_text.split())  # Normalize whitespace
                        
                        if not row_text:
                            continue
                        
                        # Look for course code
                        course_match = re.search(course_code_pattern, row_text, re.IGNORECASE)
                        if not course_match:
                            continue
                        
                        course_code = course_match.group(0).upper()
                        
                        # Look for grade in the same row
                        grade_match = re.search(grade_pattern, row_text)
                        if not grade_match:
                            continue
                        
                        grade = grade_match.group(1).upper()
                        
                        # Extract course title (best effort)
                        title = row_text
                        title = re.sub(course_code_pattern, '', title, count=1)
                        title = re.sub(grade_pattern, '', title, count=1)
                        title = re.sub(r'\b\d+\.\d+\b', '', title)  # Remove credit numbers
                        title = re.sub(r'\b20\d{2}\b', '', title)   # Remove years
                        title = ' '.join(title.split()).strip()
                        
                        course_name = title if title and len(title) > 3 else None
                        
                        # Store (dedup by keeping last occurrence)
                        courses_dict[course_code] = {
                            "course_code": course_code,
                            "grade": grade,
                            "course_name": course_name,
                            "year_taken": None
                        }
                        
                        logger.debug(
                            f"Table extraction: {course_code} -> {grade} "
                            f"({course_name or 'no title'})"
                        )
        
        parsed_courses = list(courses_dict.values())
        
        if parsed_courses:
            logger.info(f"Extracted {len(parsed_courses)} courses from tables")
        else:
            warnings.append("No courses found in tables")
        
        return parsed_courses, warnings
    
    except Exception as e:
        logger.error(f"Table extraction failed: {e}")
        return [], [f"Table extraction error: {str(e)}"]


def parse_courses_from_text(text: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse course codes and grades from transcript text using block parsing.
    
    Handles SLIIT-style transcripts where each field is on its own line:
    - Course code (e.g., IT1010)
    - Course title (may span multiple lines)
    - Semester number
    - Credits
    - Grade
    
    Args:
        text: Extracted text from transcript
        
    Returns:
        Tuple of (parsed_courses, warnings)
    """
    parsed_courses = []
    warnings = []
    courses_dict = {}  # For deduplication, key = course_code
    
    # Regex patterns
    course_code_pattern = r"\bIT\d{4}\b"  # SLIIT course codes start with IT
    grade_pattern = r"^(A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D|F)$"
    date_pattern = r"\b[A-Za-z]{3}-(\d{4})\b"  # Apr-2021 format
    
    # Split into lines, strip each, drop empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line is a course code
        if re.match(course_code_pattern, line, re.IGNORECASE):
            course_code = line.upper()
            i += 1
            
            # Collect title lines
            title_parts = []
            while i < len(lines):
                current_line = lines[i]
                # Stop at numeric-only line (semester/credits) or date-like token or grade
                if re.match(r"^\d+$", current_line):
                    break
                if re.match(r"^[A-Za-z]{3}-\d{4}$", current_line):  # Apr-2021 format
                    break
                if re.match(grade_pattern, current_line):
                    break
                # Also stop at another course code
                if re.match(course_code_pattern, current_line, re.IGNORECASE):
                    break
                
                title_parts.append(current_line)
                i += 1
            
            course_name = " ".join(title_parts).strip() if title_parts else None
            
            # Scan forward for credits, year_taken, and grade (up to 10 lines)
            credits_val = None
            grade_val = None
            year_taken_val = None
            numeric_values = []  # Collect all numeric tokens
            lookahead_limit = min(len(lines), i + 10)
            j = i
            
            while j < lookahead_limit:
                current_line = lines[j]
                
                # Check for date token (e.g., Apr-2021)
                date_match = re.search(date_pattern, current_line)
                if date_match:
                    year_taken_val = int(date_match.group(1))
                
                # Check for numeric value (could be semester or credits)
                if re.match(r"^\d+(\.\d+)?$", current_line):
                    numeric_values.append(float(current_line))
                
                # Check for grade
                if re.match(grade_pattern, current_line):
                    grade_val = current_line.upper()
                    # Keep the last numeric value before grade as credits
                    # (First numeric is usually semester like 1 or 2, last is credits like 3 or 4)
                    if numeric_values:
                        credits_val = numeric_values[-1]
                    break
                
                # Stop if we hit another course code
                if re.match(course_code_pattern, current_line, re.IGNORECASE):
                    break
                
                j += 1
            
            # Only add if we found a grade
            if grade_val:
                # Derive academic year from course code (e.g., IT1010 -> year 1, IT2050 -> year 2)
                academic_year = None
                year_match = re.match(r"IT([1-4])\d{3}", course_code)
                if year_match:
                    academic_year = int(year_match.group(1))
                    # Validate academic_year is 1-4
                    if not (1 <= academic_year <= 4):
                        academic_year = None
                
                courses_dict[course_code] = {
                    "course_code": course_code,
                    "course_name": course_name,
                    "grade": grade_val,
                    "credits": credits_val,
                    "year_taken": year_taken_val,
                    "academic_year": academic_year
                }
                logger.debug(
                    f"Parsed: {course_code} -> {grade_val}, credits: {credits_val}, "
                    f"academic_year: {academic_year}, year_taken: {year_taken_val}, title: {course_name or 'none'}"
                )
            else:
                logger.debug(f"Course code {course_code} found but no grade detected")
        else:
            i += 1
    
    # Convert dict to list (deduped, keeping last occurrence)
    parsed_courses = list(courses_dict.values())
    
    if not parsed_courses:
        warnings.append("No courses could be parsed from the transcript")
    elif len(courses_dict) < sum(1 for line in lines if re.match(course_code_pattern, line, re.IGNORECASE)):
        warnings.append("Duplicate course codes were found and deduplicated (kept last occurrence)")
    
    return parsed_courses, warnings
    
    if not parsed_courses:
        warnings.append("No courses could be parsed from the transcript")
    
    return parsed_courses, warnings


def save_upload_file(upload_file: UploadFile, student_id: str) -> Path:
    """
    Save uploaded file to disk.
    
    Args:
        upload_file: FastAPI UploadFile object
        student_id: Student identifier for filename
        
    Returns:
        Path to saved file
    """
    # Sanitize filename
    original_filename = upload_file.filename or "transcript.pdf"
    file_extension = Path(original_filename).suffix
    safe_filename = f"{student_id}_transcript{file_extension}"
    
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file
    with open(file_path, "wb") as f:
        content = upload_file.file.read()
        f.write(content)
    
    logger.info(f"Saved upload to: {file_path}")
    return file_path


def save_debug_text(text: str, student_id: str) -> None:
    """
    Save extracted text to debug file.
    
    Args:
        text: Extracted text content
        student_id: Student identifier
    """
    try:
        debug_filename = f"debug_extracted_text_{student_id}.txt"
        debug_path = OUTPUT_DIR / debug_filename
        
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        logger.info(f"Saved debug text to: {debug_path}")
    except Exception as e:
        logger.error(f"Failed to save debug text: {e}")


def process_transcript_upload(
    db: Session,
    upload_file: UploadFile,
    student_id: str
) -> Dict:
    """
    Process transcript upload: save file, extract text, parse courses, save to DB.
    
    Args:
        db: Database session
        upload_file: Uploaded file
        student_id: Student identifier
        
    Returns:
        Dictionary with student_id, parsed_courses, and warnings
    """
    warnings = []
    
    # Ensure student exists
    student = db.get(Student, student_id)
    if not student:
        # Create student record
        student = Student(student_id=student_id)
        db.add(student)
        db.flush()
        logger.info(f"Created new student: {student_id}")
    
    # Save file
    try:
        file_path = save_upload_file(upload_file, student_id)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        warnings.append(f"File save error: {str(e)}")
        return {
            "student_id": student_id,
            "parsed_courses": [],
            "warnings": warnings
        }
    
    # Extract courses from PDF
    parsed_courses = []
    text = ""
    student_info = {}
    
    if file_path.suffix.lower() == ".pdf":
        # Extract text first for student info parsing
        text = extract_text_from_pdf(file_path)
        
        # Parse student information from header
        student_info = parse_student_info(text)
        
        # Update student record with parsed info
        if student_info.get("name"):
            student.name = student_info["name"]
        if student_info.get("program"):
            student.program = student_info["program"]
        if student_info.get("intake"):
            student.intake = student_info["intake"]
        if student_info.get("specialization"):
            student.specialization = student_info["specialization"]
        
        # STEP 1: Try table extraction first
        logger.info("Attempting table extraction...")
        parsed_courses, table_warnings = extract_courses_from_tables(file_path)
        warnings.extend(table_warnings)
        
        if parsed_courses:
            logger.info(f"Table extraction successful: {len(parsed_courses)} courses found")
            # Save debug info even for table extraction
            save_debug_text(text, student_id)
            debug_preview = f"Courses extracted from tables: {len(parsed_courses)}"
        else:
            # STEP 2: Fallback to plain text extraction
            logger.info("Table extraction yielded no results, using previously extracted text...")
            
            # Log text length
            logger.info(f"Extracted text length (direct): {len(text)} characters")
            
            # STEP 3: Fallback to OCR if insufficient text
            if len(text.strip()) < 50:
                warnings.append("Direct text extraction yielded minimal content, attempting OCR")
                ocr_text = extract_text_with_ocr(file_path)
                if ocr_text:
                    text = ocr_text
                    logger.info(f"Extracted text length (OCR): {len(text)} characters")
                    # Re-parse student info from OCR text
                    student_info = parse_student_info(text)
                    if student_info.get("name"):
                        student.name = student_info["name"]
                    if student_info.get("program"):
                        student.program = student_info["program"]
                    if student_info.get("intake"):
                        student.intake = student_info["intake"]
                    if student_info.get("specialization"):
                        student.specialization = student_info["specialization"]
                else:
                    warnings.append("OCR extraction also failed or unavailable")
            
            # Save debug text file
            if text:
                save_debug_text(text, student_id)
            
            # Create debug preview (first 600 chars)
            debug_preview = text[:600] if text else ""
            
            if not text.strip():
                warnings.append("No text could be extracted from the document")
                return {
                    "student_id": student_id,
                    "parsed_courses": [],
                    "warnings": warnings,
                    "debug_preview": debug_preview
                }
            
            # Parse courses from text
            parsed_courses, parse_warnings = parse_courses_from_text(text)
            warnings.extend(parse_warnings)
    else:
        warnings.append(f"Unsupported file format: {file_path.suffix}")
        return {
            "student_id": student_id,
            "parsed_courses": [],
            "warnings": warnings,
            "debug_preview": ""
        }
    
    # Ensure we have parsed courses
    if not parsed_courses:
        warnings.append("No courses could be parsed from the document")
        debug_preview = text[:600] if text else ""
        return {
            "student_id": student_id,
            "parsed_courses": [],
            "warnings": warnings,
            "debug_preview": debug_preview
        }
    
    # Delete existing courses for this student to avoid duplicates
    deleted_count = db.query(CourseTaken).filter(
        CourseTaken.student_id == student_id
    ).delete()
    
    if deleted_count > 0:
        logger.info(f"Deleted {deleted_count} existing courses for student {student_id}")
    
    # Insert courses into database
    inserted_count = 0
    debug_preview = text[:600] if text else "Courses extracted from tables"
    
    for course_data in parsed_courses:
        try:
            course_taken = CourseTaken(
                student_id=student_id,
                course_code=course_data["course_code"],
                course_name=course_data.get("course_name"),
                grade=course_data["grade"],
                year_taken=course_data.get("year_taken"),
                credits=course_data.get("credits"),
                academic_year=course_data.get("academic_year")
            )
            db.add(course_taken)
            inserted_count += 1
        except Exception as e:
            warnings.append(f"Failed to insert {course_data['course_code']}: {str(e)}")
            logger.error(f"Course insertion error: {e}")
    
    db.commit()
    logger.info(f"Inserted {inserted_count} courses for student {student_id}")
    
    return {
        "student_id": student_id,
        "parsed_courses": parsed_courses,
        "warnings": warnings,
        "debug_preview": debug_preview
    }
