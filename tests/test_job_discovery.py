"""
tests/test_job_discovery.py
----------------------------
Unit tests for the Job Discovery Agent and job data tools.
Run with: pytest tests/test_job_discovery.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from tools.job_data_loader import load_all_jobs, filter_jobs, rank_jobs


class TestJobDataLoader:

    def test_load_all_jobs_returns_list(self):
        jobs = load_all_jobs()
        assert isinstance(jobs, list), "Jobs should be a list"

    def test_load_all_jobs_not_empty(self):
        jobs = load_all_jobs()
        assert len(jobs) > 0, "Jobs dataset should not be empty"

    def test_job_has_required_fields(self):
        jobs = load_all_jobs()
        required_fields = ["id", "title", "company", "location", "description"]
        for job in jobs:
            for field in required_fields:
                assert field in job, f"Job missing field: {field}"

    def test_filter_by_role(self):
        jobs = load_all_jobs()
        filtered = filter_jobs(jobs, role="Data Scientist")
        assert len(filtered) > 0, "Should find Data Scientist jobs"
        for job in filtered:
            assert "data" in job["title"].lower() or "data" in job["domain"].lower()

    def test_filter_by_location(self):
        jobs = load_all_jobs()
        filtered = filter_jobs(jobs, role="engineer", location="Bangalore")
        for job in filtered:
            assert "bangalore" in job["location"].lower() or job["location"].lower() == "remote"

    def test_filter_by_experience(self):
        jobs = load_all_jobs()
        filtered = filter_jobs(jobs, role="Data Scientist", experience=2, tolerance=1)
        for job in filtered:
            assert abs(job["experience_required"] - 2) <= 1

    def test_filter_returns_empty_for_unknown_role(self):
        jobs = load_all_jobs()
        filtered = filter_jobs(jobs, role="xyzunknownrole12345")
        assert len(filtered) == 0

    def test_rank_jobs_returns_sorted(self):
        jobs = load_all_jobs()[:5]
        ranked = rank_jobs(jobs, role="Data Scientist")
        scores = [j.get("relevance_score", 0) for j in ranked]
        assert scores == sorted(scores, reverse=True), "Jobs should be sorted by score"
