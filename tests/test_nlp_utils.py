"""
tests/test_nlp_utils.py
------------------------
Unit tests for NLP utility functions.
Run with: pytest tests/test_nlp_utils.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from tools.nlp_utils import (
    extract_keywords_from_text,
    compute_keyword_match_score,
    clean_text,
    extract_sections_from_resume
)


class TestExtractKeywords:

    def test_extracts_python(self):
        text = "We need a Python developer with Django experience"
        keywords = extract_keywords_from_text(text)
        assert any("python" in k.lower() for k in keywords)

    def test_extracts_multiple_skills(self):
        text = "Required: Python, SQL, Docker, AWS, machine learning"
        keywords = extract_keywords_from_text(text)
        assert len(keywords) >= 3

    def test_returns_list(self):
        result = extract_keywords_from_text("Hello world")
        assert isinstance(result, list)

    def test_empty_text_returns_empty_list(self):
        result = extract_keywords_from_text("")
        assert result == []


class TestKeywordMatchScore:

    def test_perfect_match(self):
        resume = "Python, SQL, Docker, AWS"
        keywords = ["Python", "SQL", "Docker", "AWS"]
        result = compute_keyword_match_score(resume, keywords)
        assert result["score"] == 100

    def test_zero_match(self):
        resume = "Java Spring Boot"
        keywords = ["Python", "React", "AWS"]
        result = compute_keyword_match_score(resume, keywords)
        assert result["score"] == 0

    def test_partial_match(self):
        resume = "Python and SQL developer"
        keywords = ["Python", "SQL", "Docker"]
        result = compute_keyword_match_score(resume, keywords)
        assert 60 <= result["score"] <= 70

    def test_result_has_required_keys(self):
        result = compute_keyword_match_score("Python developer", ["Python"])
        assert "score" in result
        assert "matched_keywords" in result
        assert "missing_keywords" in result

    def test_matched_keywords_correct(self):
        resume = "I know Python and Docker"
        keywords = ["Python", "Docker", "Kubernetes"]
        result = compute_keyword_match_score(resume, keywords)
        assert "Python" in result["matched_keywords"]
        assert "Docker" in result["matched_keywords"]
        assert "Kubernetes" in result["missing_keywords"]


class TestCleanText:

    def test_removes_extra_newlines(self):
        text = "Hello\n\n\n\nWorld"
        result = clean_text(text)
        assert "\n\n\n" not in result

    def test_strips_whitespace(self):
        text = "  hello world  "
        result = clean_text(text)
        assert result == "hello world"

    def test_removes_extra_spaces(self):
        text = "hello   world"
        result = clean_text(text)
        assert "   " not in result


class TestExtractSections:

    def test_returns_dict(self):
        result = extract_sections_from_resume("Sample resume text")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = extract_sections_from_resume("Sample resume")
        for key in ["summary", "experience", "education", "skills"]:
            assert key in result

    def test_extracts_skills_section(self):
        resume = """
John Doe

EXPERIENCE
Software Engineer at TechCorp 2020-2023

SKILLS
Python, SQL, Docker, AWS

EDUCATION
B.Tech Computer Science 2020
"""
        result = extract_sections_from_resume(resume)
        assert "Python" in result["skills"] or "python" in result["skills"].lower()
