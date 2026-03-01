"""
agents/job_profiling_agent.py
------------------------------
Job Profiling Agent

Responsibility:
    - Takes a raw job description
    - Extracts structured information: skills, responsibilities, keywords, seniority
    - This profile is shared with Resume Agent and Interview Agent (avoid redundant parsing)

Input:
    { job_description: str }

Output:
    {
        skills: List[str],
        responsibilities: List[str],
        keywords: List[str],
        seniority: str,
        domain: str,
        profile_summary: str
    }
"""

import json
from groq import Groq
from typing import Dict, List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import GROQ_API_KEY, GROQ_MODEL_NAME, GROQ_TEMPERATURE
from tools.nlp_utils import extract_keywords_from_text, clean_text


class JobProfilingAgent:
    """
    Agent that deeply reads a job description and extracts structured
    information to feed into the Resume and Interview agents.
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL_NAME

    def run(self, job_description: str) -> Dict:
        """
        Main entry point for the Job Profiling Agent.

        Args:
            job_description: Raw text of the job description

        Returns:
            Structured job profile dict
        """
        print("\n🔬 Job Profiling Agent: Analyzing job description...")

        if not job_description or len(job_description.strip()) < 50:
            return self._empty_profile("Job description is too short to analyze.")

        # Step 1: Quick NLP-based keyword extraction (fast, no API cost)
        nlp_keywords = extract_keywords_from_text(job_description)

        # Step 2: LLM-based deep structured extraction
        llm_profile = self._extract_with_llm(job_description)

        # Step 3: Merge NLP keywords with LLM output
        all_keywords = list(set(nlp_keywords + llm_profile.get("keywords", [])))

        result = {
            "skills": llm_profile.get("skills", nlp_keywords[:10]),
            "responsibilities": llm_profile.get("responsibilities", []),
            "keywords": all_keywords,
            "seniority": llm_profile.get("seniority", "mid-level"),
            "domain": llm_profile.get("domain", "Technology"),
            "profile_summary": llm_profile.get("profile_summary", ""),
            "raw_jd": job_description
        }

        print(f"   ✅ Profiling complete. Found {len(result['skills'])} skills, {len(result['keywords'])} keywords.")
        return result

    def _extract_with_llm(self, job_description: str) -> Dict:
        """
        Use Groq LLM to extract structured data from job description.
        Returns a dict with skills, responsibilities, keywords, seniority, domain.
        """
        prompt = f"""Analyze the following job description and extract structured information.
Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Job Description:
{job_description[:3000]}

Return this exact JSON structure:
{{
  "skills": ["skill1", "skill2", ...],
  "responsibilities": ["responsibility1", "responsibility2", ...],
  "keywords": ["keyword1", "keyword2", ...],
  "seniority": "entry-level | mid-level | senior | lead",
  "domain": "Data Science | Software Engineering | DevOps | NLP | Full Stack | etc.",
  "profile_summary": "2-sentence summary of what this role requires"
}}

Rules:
- skills: list of 5-15 specific technical and soft skills required
- responsibilities: list of 4-8 key job duties (short phrases)
- keywords: list of 10-20 ATS keywords from the JD (mix of tech + domain terms)
- seniority: one of the four options listed
- domain: the closest domain category
- profile_summary: brief summary for resume tailoring"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1  # Very low — we want consistent JSON
            )

            raw_content = response.choices[0].message.content.strip()

            # Clean up potential markdown code fences
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]

            return json.loads(raw_content)

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error from LLM: {e}. Using NLP fallback.")
            return self._nlp_fallback_profile(job_description)

        except Exception as e:
            print(f"   ⚠️ LLM profiling failed: {e}. Using NLP fallback.")
            return self._nlp_fallback_profile(job_description)

    def _nlp_fallback_profile(self, job_description: str) -> Dict:
        """
        Fallback profiler using pure NLP when LLM fails.
        Less structured but still useful.
        """
        keywords = extract_keywords_from_text(job_description)
        jd_lower = job_description.lower()

        # Detect seniority from keywords
        if any(w in jd_lower for w in ["senior", "lead", "principal", "staff"]):
            seniority = "senior"
        elif any(w in jd_lower for w in ["junior", "entry", "fresher", "graduate"]):
            seniority = "entry-level"
        else:
            seniority = "mid-level"

        return {
            "skills": keywords[:12],
            "responsibilities": ["Build and maintain systems", "Collaborate with teams", "Deliver features"],
            "keywords": keywords,
            "seniority": seniority,
            "domain": "Technology",
            "profile_summary": "This role requires strong technical skills and collaborative abilities."
        }

    def _empty_profile(self, reason: str) -> Dict:
        """Return an empty profile with a reason."""
        return {
            "skills": [],
            "responsibilities": [],
            "keywords": [],
            "seniority": "mid-level",
            "domain": "Unknown",
            "profile_summary": reason,
            "raw_jd": ""
        }
