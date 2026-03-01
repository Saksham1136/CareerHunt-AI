"""
tools/job_data_loader.py
------------------------
Loads and filters job listings from the sample dataset.
FIXED: Smarter fuzzy role matching so searches like "data science" 
find Data Scientist, Senior Data Scientist, Data Scientist - NLP, etc.
"""

import json
import os
from typing import List, Dict, Optional

JOBS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_jobs.json")

# Maps common search terms to related job titles/domains
ROLE_ALIASES = {
    "data science":     ["data scientist", "data science", "ml", "machine learning", "ai"],
    "data scientist":   ["data scientist", "data science", "ml", "machine learning"],
    "machine learning": ["machine learning", "ml engineer", "ml", "ai", "deep learning", "data scientist"],
    "ml engineer":      ["ml engineer", "machine learning", "mlops", "ai"],
    "software engineer":["software engineer", "software developer", "backend", "python developer"],
    "backend":          ["backend", "software engineer", "python developer", "fastapi", "django"],
    "frontend":         ["frontend", "react", "javascript", "ui developer"],
    "full stack":       ["full stack", "fullstack", "frontend", "backend"],
    "data analyst":     ["data analyst", "business analyst", "analytics", "data analysis"],
    "devops":           ["devops", "cloud", "infrastructure", "sre", "kubernetes"],
    "nlp":              ["nlp", "natural language", "text", "data scientist"],
    "python":           ["python developer", "software engineer", "backend", "data scientist", "ml"],
    "ai":               ["ai", "machine learning", "data scientist", "deep learning", "nlp"],
}


def load_all_jobs() -> List[Dict]:
    try:
        with open(JOBS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Jobs dataset not found at {JOBS_PATH}")
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing jobs JSON: {e}")
        return []


def _get_search_terms(role: str) -> List[str]:
    """
    Expand a role query into multiple search terms using aliases.
    e.g. "data science" → ["data scientist", "data science", "ml", ...]
    """
    role_lower = role.lower().strip()
    terms = [role_lower]

    # Check aliases
    for key, aliases in ROLE_ALIASES.items():
        if key in role_lower or role_lower in key:
            terms.extend(aliases)

    # Also add individual words from multi-word queries
    words = role_lower.split()
    terms.extend(words)

    return list(set(terms))


def filter_jobs(
    jobs: List[Dict],
    role: str,
    location: Optional[str] = None,
    experience: Optional[int] = None,
    tolerance: int = 1
) -> List[Dict]:
    """
    Filter jobs with smart fuzzy role matching.
    Checks title, domain, description, AND skills_required.
    """
    search_terms = _get_search_terms(role)
    filtered = []

    for job in jobs:
        title_lower = job.get("title", "").lower()
        domain_lower = job.get("domain", "").lower()
        desc_lower = job.get("description", "").lower()
        skills_lower = " ".join(job.get("skills_required", [])).lower()

        # Check if ANY search term matches title, domain, description, or skills
        matched = False
        for term in search_terms:
            if (term in title_lower or
                term in domain_lower or
                term in desc_lower or
                term in skills_lower):
                matched = True
                break

        if not matched:
            continue

        # Location filter
        if location and location.lower() not in ("any", "all", ""):
            job_location = job.get("location", "").lower()
            if location.lower() not in job_location and job_location != "remote":
                continue

        # Experience filter
        if experience is not None:
            job_exp = job.get("experience_required", 0)
            if abs(job_exp - experience) > tolerance:
                continue

        filtered.append(job)

    return filtered


def rank_jobs(jobs: List[Dict], role: str, skills_keywords: List[str] = None) -> List[Dict]:
    """
    Score and rank jobs by relevance. Higher score = better match.
    """
    role_lower = role.lower()
    search_terms = _get_search_terms(role)

    for job in jobs:
        score = 0
        title_lower = job.get("title", "").lower()

        # Title is an exact or strong match
        if role_lower == title_lower:
            score += 5
        elif any(term in title_lower for term in search_terms[:3]):
            score += 3
        elif any(term in title_lower for term in search_terms):
            score += 1

        # Domain match
        if any(term in job.get("domain", "").lower() for term in search_terms):
            score += 2

        # Skill keyword overlap
        if skills_keywords:
            jd_lower = job.get("description", "").lower()
            for skill in skills_keywords:
                if skill.lower() in jd_lower:
                    score += 1

        job["relevance_score"] = score

    return sorted(jobs, key=lambda x: x.get("relevance_score", 0), reverse=True)
