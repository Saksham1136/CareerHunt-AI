"""
agents/job_discovery_agent.py
------------------------------
Job Discovery & Matching Agent

Responsibility:
    - Takes user's job role, location, and experience level
    - Searches and filters the job dataset
    - Uses Groq LLM to generate a natural-language summary of top matches
    - Returns ranked job listings with match explanations

Input:
    { role, location, experience }

Output:
    { jobs: [...], summary: str, count: int }
"""

from groq import Groq
from typing import Dict, List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import GROQ_API_KEY, GROQ_MODEL_NAME, GROQ_MAX_TOKENS, GROQ_TEMPERATURE, MAX_JOB_RESULTS
from tools.job_data_loader import load_all_jobs, filter_jobs, rank_jobs
from tools.nlp_utils import extract_keywords_from_text


class JobDiscoveryAgent:
    """
    Agent responsible for finding and ranking job opportunities
    based on user's role, location, and experience.
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL_NAME
        self.all_jobs = load_all_jobs()

    def run(self, role: str, location: str = "", experience: int = 0) -> Dict:
        """
        Main entry point for the Job Discovery Agent.

        Args:
            role: Target job role (e.g., "Data Scientist")
            location: Preferred city or "Remote"
            experience: Years of experience

        Returns:
            Dict with 'jobs', 'summary', 'count'
        """
        print(f"\n🔍 Job Discovery Agent: Searching for '{role}' in '{location}' with {experience} YOE...")

        # Step 1: Filter jobs from dataset
        filtered = filter_jobs(
            jobs=self.all_jobs,
            role=role,
            location=location if location else None,
            experience=experience
        )

        if not filtered:
            # Relax location filter if no results
            print("   → No exact matches. Relaxing location filter...")
            filtered = filter_jobs(
                jobs=self.all_jobs,
                role=role,
                location=None,
                experience=experience
            )

        if not filtered:
            # Relax experience filter too
            print("   → Still no matches. Relaxing experience filter...")
            filtered = filter_jobs(
                jobs=self.all_jobs,
                role=role,
                location=None,
                experience=None
            )

        # Step 2: Rank by relevance
        ranked = rank_jobs(filtered, role)

        # Step 3: Take top N results
        top_jobs = ranked[:MAX_JOB_RESULTS]

        if not top_jobs:
            return {
                "jobs": [],
                "summary": f"No job listings found for '{role}'. Try a broader search term.",
                "count": 0
            }

        # Step 4: Use LLM to generate a helpful summary
        summary = self._generate_job_summary(role, location, experience, top_jobs)

        print(f"   ✅ Found {len(top_jobs)} matching jobs.")

        return {
            "jobs": top_jobs,
            "summary": summary,
            "count": len(top_jobs)
        }

    def _generate_job_summary(
        self, role: str, location: str, experience: int, jobs: List[Dict]
    ) -> str:
        """
        Use Groq LLM to generate a natural-language summary of the job results.
        """
        # Build a short jobs overview for the prompt
        jobs_overview = ""
        for i, job in enumerate(jobs, 1):
            jobs_overview += (
                f"{i}. {job['title']} at {job['company']} ({job['location']}) — "
                f"Exp: {job['experience_required']} yrs — Salary: {job.get('salary', 'N/A')}\n"
            )

        prompt = f"""You are a career advisor. A job seeker is looking for:
Role: {role}
Location: {location or 'Any'}
Experience: {experience} years

Here are the top matching job listings found:
{jobs_overview}

Write a brief, encouraging 2-3 sentence summary of these results for the job seeker.
Mention the number of jobs found, highlight any standout opportunities, and give one quick tip.
Be concise and friendly."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=GROQ_TEMPERATURE
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️ LLM summary generation failed: {e}")
            return (
                f"Found {len(jobs)} job listings matching your search for '{role}'. "
                f"Top results include positions at {jobs[0]['company']} and {jobs[1]['company'] if len(jobs) > 1 else 'others'}."
            )
