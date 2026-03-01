"""
tools/resume_parser.py
-----------------------
Parses uploaded resume files (TXT or DOCX) into plain text
for further processing by the Resume and Profiling agents.
"""

import os
import re
from typing import Optional

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def parse_resume_from_text(raw_text: str) -> str:
    """
    Clean and normalize plain text resume input.

    Args:
        raw_text: Raw text pasted by user or read from file

    Returns:
        Cleaned plain text
    """
    if not raw_text or not raw_text.strip():
        return ""

    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', raw_text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def parse_resume_from_docx(file_path: str) -> str:
    """
    Extract plain text from a .docx resume file.

    Args:
        file_path: Absolute path to the .docx file

    Returns:
        Extracted plain text content
    """
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx required. Run: pip install python-docx")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    doc = DocxDocument(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def parse_resume_from_upload(uploaded_file) -> str:
    """
    Parse resume from a Streamlit UploadedFile object.
    Supports .txt and .docx formats.

    Args:
        uploaded_file: Streamlit file uploader object

    Returns:
        Extracted plain text of resume
    """
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    if filename.endswith(".txt"):
        return parse_resume_from_text(uploaded_file.read().decode("utf-8", errors="ignore"))

    elif filename.endswith(".docx"):
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx required to parse DOCX files.")

        # Save temp file then parse
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            text = parse_resume_from_docx(tmp_path)
        finally:
            os.unlink(tmp_path)  # Clean up temp file
        return text

    else:
        raise ValueError(f"Unsupported file type: {filename}. Please upload .txt or .docx")


def validate_resume_text(resume_text: str) -> tuple[bool, str]:
    """
    Basic validation to check if resume text seems valid.

    Args:
        resume_text: Parsed resume text

    Returns:
        (is_valid: bool, message: str)
    """
    if not resume_text or len(resume_text.strip()) < 100:
        return False, "Resume appears too short. Please provide your full resume text."

    if len(resume_text) > 15000:
        return False, "Resume text is very long. Please trim it to under 15,000 characters."

    # Check for at least some recognizable resume content
    resume_lower = resume_text.lower()
    has_experience = any(kw in resume_lower for kw in ["experience", "work", "project", "skill", "education"])

    if not has_experience:
        return False, "Could not detect resume sections. Please include Experience, Skills, or Education."

    return True, "Resume looks good!"
