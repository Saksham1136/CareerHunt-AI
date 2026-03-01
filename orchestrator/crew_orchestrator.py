"""
orchestrator/crew_orchestrator.py
-----------------------------------
Orchestration & Workflow Engine

Responsibility:
    - Coordinates the execution order of all agents
    - Passes outputs from one agent as inputs to the next
    - Handles errors gracefully so one agent failure doesn't crash the whole pipeline
    - Returns a unified result object to the UI

Workflow:
    1. Job Discovery Agent  → finds relevant jobs
    2. Job Profiling Agent  → parses job description
    3. Resume Agent         → optimizes resume using job profile
    4. Interview Agent      → generates Q&A using job profile

Note: Uses CrewAI for agent coordination when available,
      with a clean Python fallback for simpler environments.
"""

import time
from typing import Dict, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.job_discovery_agent import JobDiscoveryAgent
from agents.job_profiling_agent import JobProfilingAgent
from agents.resume_agent import ResumeAgent
from agents.interview_agent import InterviewAgent


class JobSeekerOrchestrator:
    """
    Orchestrates the multi-agent workflow for the Job Seeker AI system.
    Coordinates all agents and returns unified results.
    """

    def __init__(self):
        print("🚀 Initializing Multi-Agent Job Seeker System...")
        self.job_discovery = JobDiscoveryAgent()
        self.job_profiling = JobProfilingAgent()
        self.resume_agent = ResumeAgent()
        self.interview_agent = InterviewAgent()
        print("✅ All agents initialized.\n")

    def run_full_pipeline(
        self,
        role: str,
        location: str,
        experience: int,
        resume_text: str,
        job_description: str,
        user_info: Optional[Dict] = None
    ) -> Dict:
        """
        Run the complete multi-agent pipeline.

        Args:
            role: Target job role (e.g., "Data Scientist")
            location: Preferred location
            experience: Years of experience
            resume_text: User's current resume as plain text
            job_description: Target job description text
            user_info: Optional dict with name, email, phone, linkedin, github

        Returns:
            Comprehensive result dict with all agent outputs
        """
        start_time = time.time()
        results = {
            "status": "running",
            "job_discovery": None,
            "job_profile": None,
            "resume": None,
            "interview": None,
            "errors": [],
            "elapsed_seconds": 0
        }

        print("=" * 60)
        print("  MULTI-AGENT PIPELINE STARTING")
        print("=" * 60)

        # ──────────────────────────────────────────
        # AGENT 1: Job Discovery
        # ──────────────────────────────────────────
        try:
            job_result = self.job_discovery.run(
                role=role,
                location=location,
                experience=experience
            )
            results["job_discovery"] = job_result
        except Exception as e:
            error_msg = f"Job Discovery Agent failed: {str(e)}"
            results["errors"].append(error_msg)
            results["job_discovery"] = {"jobs": [], "summary": error_msg, "count": 0}
            print(f"   ❌ {error_msg}")

        # ──────────────────────────────────────────
        # AGENT 2: Job Profiling
        # Use provided JD, or fall back to top discovered job's description
        # ──────────────────────────────────────────
        try:
            # Determine which job description to profile
            jd_to_profile = job_description.strip()

            if not jd_to_profile and results["job_discovery"] and results["job_discovery"]["jobs"]:
                # Use top job's description as fallback
                top_job = results["job_discovery"]["jobs"][0]
                jd_to_profile = top_job.get("description", "")
                print(f"   ℹ️  Using top job's JD for profiling: {top_job.get('title')} at {top_job.get('company')}")

            if jd_to_profile:
                job_profile = self.job_profiling.run(job_description=jd_to_profile)
                results["job_profile"] = job_profile
            else:
                results["job_profile"] = {
                    "skills": [], "keywords": [], "responsibilities": [],
                    "seniority": "mid-level", "domain": role,
                    "profile_summary": "No job description provided."
                }
        except Exception as e:
            error_msg = f"Job Profiling Agent failed: {str(e)}"
            results["errors"].append(error_msg)
            results["job_profile"] = {
                "skills": [], "keywords": [], "responsibilities": [],
                "seniority": "mid-level", "domain": role,
                "profile_summary": error_msg
            }
            print(f"   ❌ {error_msg}")

        # ──────────────────────────────────────────
        # AGENT 3: Resume Optimization
        # Only runs if we have resume text and a job profile
        # ──────────────────────────────────────────
        if resume_text and resume_text.strip():
            try:
                resume_result = self.resume_agent.run(
                    resume_text=resume_text,
                    job_profile=results["job_profile"],
                    user_info=user_info or {}
                )
                results["resume"] = resume_result
            except Exception as e:
                error_msg = f"Resume Agent failed: {str(e)}"
                results["errors"].append(error_msg)
                results["resume"] = {
                    "optimized_resume_text": resume_text,
                    "optimized_score": 0,
                    "original_score": 0,
                    "matched_keywords": [],
                    "missing_keywords": [],
                    "docx_path": None,
                    "suggestions": [f"⚠️ Resume optimization unavailable: {str(e)}"]
                }
                print(f"   ❌ {error_msg}")
        else:
            results["resume"] = None
            print("   ℹ️  No resume provided — skipping Resume Agent.")

        # ──────────────────────────────────────────
        # AGENT 4: Interview Preparation
        # ──────────────────────────────────────────
        try:
            interview_result = self.interview_agent.run(
                job_profile=results["job_profile"],
                experience_years=experience,
                resume_text=resume_text,
                job_description=jd_to_profile
            )
            results["interview"] = interview_result
        except Exception as e:
            error_msg = f"Interview Agent failed: {str(e)}"
            results["errors"].append(error_msg)
            results["interview"] = {
                "technical_questions": [],
                "behavioral_questions": [],
                "system_design_questions": [],
                "key_talking_points": [],
                "preparation_tips": [f"⚠️ Interview prep unavailable: {str(e)}"]
            }
            print(f"   ❌ {error_msg}")

        # ──────────────────────────────────────────
        # Finalize
        # ──────────────────────────────────────────
        elapsed = round(time.time() - start_time, 2)
        results["elapsed_seconds"] = elapsed
        results["status"] = "completed" if not results["errors"] else "completed_with_errors"

        print("\n" + "=" * 60)
        print(f"  PIPELINE COMPLETE in {elapsed}s | Errors: {len(results['errors'])}")
        print("=" * 60 + "\n")

        return results

    def run_job_search_only(self, role: str, location: str, experience: int) -> Dict:
        """
        Run only the job discovery pipeline (lighter, faster).
        Used when user only wants job listings without resume/interview.
        """
        try:
            return self.job_discovery.run(role=role, location=location, experience=experience)
        except Exception as e:
            return {"jobs": [], "summary": f"Search failed: {str(e)}", "count": 0}

    def run_resume_only(
        self, resume_text: str, job_description: str, user_info: Dict = None
    ) -> Dict:
        """
        Run only profiling + resume optimization.
        Used when user already has a job and just wants resume tailoring.
        """
        try:
            job_profile = self.job_profiling.run(job_description=job_description)
            return self.resume_agent.run(
                resume_text=resume_text,
                job_profile=job_profile,
                user_info=user_info or {}
            )
        except Exception as e:
            return {
                "optimized_resume_text": resume_text,
                "optimized_score": 0,
                "suggestions": [f"Error: {str(e)}"],
                "docx_path": None
            }

    def run_interview_only(self, job_description: str, experience: int = 2) -> Dict:
        """
        Run only profiling + interview prep.
        """
        try:
            job_profile = self.job_profiling.run(job_description=job_description)
            return self.interview_agent.run(job_profile=job_profile, experience_years=experience)
        except Exception as e:
            return {
                "technical_questions": [],
                "behavioral_questions": [],
                "preparation_tips": [f"Error: {str(e)}"]
            }
