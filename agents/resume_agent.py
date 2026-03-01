"""
agents/resume_agent.py
-----------------------
Resume Optimization & ATS Formatting Agent

Responsibility:
    - Takes user's raw resume + job profile (from Job Profiling Agent)
    - Computes keyword match score
    - Uses Groq LLM to rewrite and optimize the resume for ATS
    - Generates a downloadable ATS-friendly DOCX file

Input:
    { resume_text: str, job_profile: dict, user_info: dict }

Output:
    {
        optimized_resume_text: str,
        match_score: int,
        matched_keywords: List[str],
        missing_keywords: List[str],
        docx_path: str,
        suggestions: List[str]
    }
"""

from groq import Groq
from typing import Dict, List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import GROQ_API_KEY, GROQ_MODEL_NAME, GROQ_TEMPERATURE, GROQ_MAX_TOKENS
from tools.nlp_utils import compute_keyword_match_score, extract_keywords_from_text, clean_text
from tools.resume_formatter import generate_ats_resume, build_resume_data_from_llm_output


class ResumeAgent:
    """
    Agent that tailors and optimizes a user's resume for a specific job,
    maximizing ATS compatibility and keyword alignment.
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL_NAME

    def run(self, resume_text: str, job_profile: Dict, user_info: Dict = None) -> Dict:
        """
        Main entry point for the Resume Optimization Agent.

        Args:
            resume_text: User's current resume as plain text
            job_profile: Output from JobProfilingAgent.run()
            user_info: Optional dict with name, email, phone, linkedin, github

        Returns:
            Dict with optimized resume text, match scores, DOCX file path
        """
        print("\n📝 Resume Agent: Optimizing resume for ATS compatibility...")

        if not user_info:
            user_info = {}

        # Step 1: Compute baseline keyword match score
        job_keywords = job_profile.get("keywords", [])
        match_result = compute_keyword_match_score(resume_text, job_keywords)

        print(f"   → Baseline ATS score: {match_result['score']}% | "
              f"Missing: {len(match_result['missing_keywords'])} keywords")

        # Step 2: Use LLM to optimize the resume
        optimized_text = self._optimize_resume_with_llm(
            resume_text=resume_text,
            job_profile=job_profile,
            missing_keywords=match_result["missing_keywords"]
        )

        # Step 3: Re-score after optimization
        new_match = compute_keyword_match_score(optimized_text, job_keywords)

        # Step 4: Generate DOCX file
        docx_path = self._generate_docx(
            optimized_text=optimized_text,
            user_info=user_info,
            job_profile=job_profile
        )

        # Step 5: Generate improvement suggestions
        suggestions = self._generate_suggestions(match_result, new_match, job_profile)

        print(f"   ✅ Resume optimized. New ATS score: {new_match['score']}% | File: {docx_path}")

        return {
            "optimized_resume_text": optimized_text,
            "original_score": match_result["score"],
            "optimized_score": new_match["score"],
            "matched_keywords": new_match["matched_keywords"],
            "missing_keywords": new_match["missing_keywords"],
            "docx_path": docx_path,
            "suggestions": suggestions
        }

    def _optimize_resume_with_llm(
        self, resume_text: str, job_profile: Dict, missing_keywords: List[str]
    ) -> str:
        """
        Use Groq LLM to rewrite the resume, incorporating missing keywords
        and aligning it with the job requirements.
        """
        skills_str = ", ".join(job_profile.get("skills", []))
        responsibilities_str = "\n".join(f"- {r}" for r in job_profile.get("responsibilities", []))
        missing_kw_str = ", ".join(missing_keywords[:15])  # Top 15 missing
        seniority = job_profile.get("seniority", "mid-level")
        domain = job_profile.get("domain", "Technology")

        prompt = f"""You are an expert ATS resume optimizer and career coach.

TASK: Rewrite the user's resume to be highly optimized for the following job.

JOB REQUIREMENTS:
- Domain: {domain}
- Seniority: {seniority}
- Required Skills: {skills_str}
- Key Responsibilities:
{responsibilities_str}

MISSING KEYWORDS TO INCORPORATE: {missing_kw_str}

USER'S CURRENT RESUME:
{resume_text[:4000]}

INSTRUCTIONS:
1. Keep all factual information (companies, dates, degrees, names) exactly as provided
2. Rewrite bullet points to start with strong action verbs (Developed, Designed, Built, Led, etc.)
3. Naturally incorporate the missing keywords where they are truthfully applicable
4. Quantify achievements where possible (use estimates if exact numbers aren't given, but note they should be verified)
5. Align the professional summary to the target job's domain and seniority
6. Use ATS-safe formatting: plain text, standard headings, no special characters
7. Keep the output professional and concise

OUTPUT FORMAT — Use these exact section headers:
PROFESSIONAL SUMMARY
[2-3 sentences aligned to the job]

TECHNICAL SKILLS
[Comma-separated list of skills]

PROFESSIONAL EXPERIENCE
[Company Name | Role Title | Dates]
• [Action verb + achievement + impact]
• [Action verb + achievement + impact]

EDUCATION
[Degree | Institution | Year]

PROJECTS
[Project Name]: [Brief description with tech stack]

Keep the tone professional. Do NOT fabricate experience or credentials."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=GROQ_MAX_TOKENS,
                temperature=GROQ_TEMPERATURE
            )
            return clean_text(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"   ⚠️ LLM optimization failed: {e}. Returning enhanced original.")
            return self._basic_enhancement(resume_text, missing_keywords)

    def _basic_enhancement(self, resume_text: str, missing_keywords: List[str]) -> str:
        """
        Lightweight fallback enhancement when LLM is unavailable.
        Appends a skills addendum to help ATS scoring.
        """
        addendum = f"\n\nADDITIONAL SKILLS\n{', '.join(missing_keywords[:10])}"
        return resume_text + addendum

    def _generate_docx(self, optimized_text: str, user_info: Dict, job_profile: Dict) -> str:
        """
        Build structured resume data and generate the DOCX file.
        """
        # Build the resume data dict for the formatter
        resume_data = build_resume_data_from_llm_output(
            llm_output=optimized_text,
            user_name=user_info.get("name", ""),
            contact={
                "email": user_info.get("email", ""),
                "phone": user_info.get("phone", ""),
                "location": user_info.get("location", ""),
                "linkedin": user_info.get("linkedin", ""),
                "github": user_info.get("github", "")
            }
        )

        # Add job-matched skills if not already extracted
        if not resume_data["skills"] and job_profile.get("skills"):
            resume_data["skills"] = job_profile["skills"][:15]

        # Generate the DOCX
        docx_path = generate_ats_resume(
            resume_data=resume_data,
            output_filename=f"ATS_Resume_{user_info.get('name', 'Optimized').replace(' ', '_')}"
        )

        return docx_path

    def _generate_suggestions(
        self, original_match: Dict, new_match: Dict, job_profile: Dict
    ) -> List[str]:
        """
        Generate actionable improvement suggestions for the user.
        """
        suggestions = []
        improvement = new_match["score"] - original_match["score"]

        if improvement > 0:
            suggestions.append(
                f"✅ ATS score improved by {improvement}% after optimization "
                f"({original_match['score']}% → {new_match['score']}%)"
            )

        if new_match["missing_keywords"]:
            top_missing = new_match["missing_keywords"][:5]
            suggestions.append(
                f"💡 Still missing these keywords — add them if applicable: "
                f"{', '.join(top_missing)}"
            )

        if new_match["score"] >= 80:
            suggestions.append("🎯 Strong ATS match! Your resume is well-aligned with this role.")
        elif new_match["score"] >= 60:
            suggestions.append("📈 Good match. Consider adding more project examples with the missing skills.")
        else:
            suggestions.append(
                "⚠️ Below 60% match. Focus on building projects that demonstrate the missing skills."
            )

        seniority = job_profile.get("seniority", "mid-level")
        if seniority == "senior":
            suggestions.append("👔 Senior role: Emphasize leadership, mentoring, and system-level decisions.")
        elif seniority == "entry-level":
            suggestions.append("🎓 Entry-level role: Highlight projects, internships, and learning velocity.")

        return suggestions
