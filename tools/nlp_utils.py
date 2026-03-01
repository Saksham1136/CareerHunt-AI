"""
tools/nlp_utils.py
------------------
NLP helper functions used across agents.
Uses simple regex + keyword matching (no heavy models needed).
Falls back gracefully if spaCy is not available.
"""

import re
import json
import os
from typing import List, Dict

# ─────────────────────────────────────────────
# Load ATS keyword reference data
# ─────────────────────────────────────────────
_KEYWORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ats_keywords.json")

def _load_ats_data() -> Dict:
    """Load ATS keywords and rules from JSON file."""
    try:
        with open(_KEYWORDS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"action_verbs": [], "domains": {}, "soft_skills": [], "ats_formatting_rules": {}}

ATS_DATA = _load_ats_data()


# ─────────────────────────────────────────────
# Keyword Extraction
# ─────────────────────────────────────────────

def extract_keywords_from_text(text: str) -> List[str]:
    """
    Extract meaningful keywords from a block of text.
    Combines tech skill detection + domain vocabulary matching.

    Args:
        text: Raw text (job description, resume section, etc.)

    Returns:
        List of unique keywords found in the text
    """
    text_lower = text.lower()

    # Common tech skills to detect (extendable list)
    tech_skills = [
        "python", "java", "javascript", "typescript", "react", "node.js", "fastapi",
        "django", "flask", "sql", "postgresql", "mysql", "mongodb", "redis", "kafka",
        "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "git", "linux",
        "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
        "pytorch", "scikit-learn", "pandas", "numpy", "spark", "hadoop", "airflow",
        "mlflow", "huggingface", "transformers", "bert", "gpt", "spacy", "nltk",
        "tableau", "power bi", "excel", "r", "scala", "golang", "c++", "c#",
        "microservices", "rest api", "graphql", "ci/cd", "jenkins", "github actions",
        "a/b testing", "statistics", "data analysis", "data visualization",
        "system design", "distributed systems", "agile", "scrum", "llm", "langchain",
        "crewai", "vector database", "pinecone", "chromadb", "embeddings"
    ]

    found_keywords = []

    # Check for each known skill
    for skill in tech_skills:
        if skill in text_lower:
            # Preserve original casing for display
            found_keywords.append(skill.title() if len(skill) <= 4 else skill)

    # Also extract domain keywords from ATS data
    for domain_keywords in ATS_DATA.get("domains", {}).values():
        for kw in domain_keywords:
            if kw.lower() in text_lower and kw not in found_keywords:
                found_keywords.append(kw)

    return list(set(found_keywords))


def compute_keyword_match_score(resume_text: str, job_keywords: List[str]) -> Dict:
    """
    Compute how well a resume matches a job's keywords.

    Args:
        resume_text: The user's resume as plain text
        job_keywords: List of required keywords from the job

    Returns:
        Dict with score (0-100), matched, and missing keywords
    """
    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for kw in job_keywords:
        if kw.lower() in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    total = len(job_keywords) if job_keywords else 1
    score = round((len(matched) / total) * 100)

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "total_keywords": total
    }


def clean_text(text: str) -> str:
    """
    Remove excessive whitespace, special characters, and normalize text.

    Args:
        text: Raw input text

    Returns:
        Cleaned text string
    """
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def extract_sections_from_resume(resume_text: str) -> Dict[str, str]:
    """
    Attempt to parse common resume sections from raw text.

    Args:
        resume_text: Raw resume text

    Returns:
        Dict with keys like 'summary', 'experience', 'education', 'skills'
    """
    sections = {
        "summary": "",
        "experience": "",
        "education": "",
        "skills": "",
        "projects": "",
        "certifications": "",
        "raw": resume_text
    }

    # Common section header patterns
    section_patterns = {
        "summary": r"(summary|objective|profile|about me)",
        "experience": r"(experience|work experience|employment|work history)",
        "education": r"(education|academic|qualification)",
        "skills": r"(skills|technical skills|core competencies|technologies)",
        "projects": r"(projects|key projects|personal projects)",
        "certifications": r"(certifications|certificates|courses|training)"
    }

    lines = resume_text.split('\n')
    current_section = "raw"

    for line in lines:
        line_lower = line.lower().strip()

        # Check if this line is a section header
        matched_section = None
        for section, pattern in section_patterns.items():
            if re.search(pattern, line_lower) and len(line_lower) < 50:
                matched_section = section
                break

        if matched_section:
            current_section = matched_section
        else:
            if current_section in sections:
                sections[current_section] += line + "\n"

    return sections


def get_action_verbs() -> List[str]:
    """Return the list of strong action verbs for resume bullet points."""
    return ATS_DATA.get("action_verbs", [
        "Developed", "Built", "Designed", "Implemented", "Optimized",
        "Led", "Delivered", "Improved", "Created", "Automated"
    ])
