import fitz  # PyMuPDF
from pathlib import Path

def extract_jd_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()
