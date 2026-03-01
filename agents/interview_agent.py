"""
agents/interview_agent.py
--------------------------
Interview Preparation Agent — Deep JD + Resume Aware Version

Generates:
- 7 technical questions (specific to JD skills, not generic)
- 5 behavioral questions (STAR format, role-relevant)
- 3 system design questions (with step-by-step approach)
- Key talking points extracted from JD+resume overlap
- Preparation tips based on seniority and domain
"""

import json
from groq import Groq
from typing import Dict, List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import GROQ_API_KEY, GROQ_MODEL_NAME


class InterviewAgent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model  = GROQ_MODEL_NAME

    def run(self, job_profile: Dict, experience_years: int = 2,
            resume_text: str = "", job_description: str = "") -> Dict:
        """
        Generate comprehensive interview prep using JD + resume context.
        """
        print("\n🎤 Interview Agent: Generating deep role-specific Q&A...")

        domain          = job_profile.get("domain", "Software Engineering")
        skills          = job_profile.get("skills", [])
        seniority       = job_profile.get("seniority", "mid-level")
        responsibilities= job_profile.get("responsibilities", [])
        keywords        = job_profile.get("keywords", [])
        raw_jd          = job_profile.get("raw_jd", "") or job_description

        qa_data = self._generate_deep_questions(
            domain=domain, skills=skills, seniority=seniority,
            responsibilities=responsibilities, keywords=keywords,
            experience_years=experience_years,
            raw_jd=raw_jd[:2000],
            resume_snippet=resume_text[:1000]
        )

        talking_points = self._generate_talking_points(domain, skills, responsibilities, resume_text)

        result = {
            "technical_questions":      qa_data.get("technical_questions", []),
            "behavioral_questions":     qa_data.get("behavioral_questions", []),
            "system_design_questions":  qa_data.get("system_design_questions", []),
            "key_talking_points":       talking_points,
            "preparation_tips":         self._get_prep_tips(seniority, domain),
            "domain":    domain,
            "seniority": seniority
        }

        total = (len(result["technical_questions"]) +
                 len(result["behavioral_questions"]) +
                 len(result["system_design_questions"]))
        print(f"   ✅ Generated {total} questions.")
        return result

    def _generate_deep_questions(self, domain, skills, seniority, responsibilities,
                                  keywords, experience_years, raw_jd, resume_snippet) -> Dict:
        skills_str  = ", ".join(skills[:12])
        resp_str    = "\n".join(f"- {r}" for r in responsibilities[:6])
        kw_str      = ", ".join(keywords[:15])

        prompt = f"""You are a senior technical interviewer at a top tech company.
Your job is to create a HIGHLY SPECIFIC interview prep guide for a candidate.

=== ROLE CONTEXT ===
Domain:          {domain}
Seniority:       {seniority}
Experience:      {experience_years} years
Required Skills: {skills_str}
Key Responsibilities:
{resp_str}
ATS Keywords: {kw_str}

=== JOB DESCRIPTION (excerpt) ===
{raw_jd}

=== CANDIDATE RESUME (excerpt) ===
{resume_snippet}

=== YOUR TASK ===
Generate interview questions that are DEEPLY SPECIFIC to this exact role and JD.
Do NOT generate generic questions. Every question must reference specific skills,
tools, or responsibilities mentioned in the JD above.

Return ONLY valid JSON. No markdown, no explanation, no extra text.

{{
  "technical_questions": [
    {{
      "question": "Very specific technical question about a skill/tool in the JD",
      "answer": "Detailed 4-6 sentence model answer with technical depth, specific examples, metrics where possible. Explain the WHY not just the WHAT.",
      "follow_up": "A likely follow-up question the interviewer would ask",
      "tip": "One specific tip for answering this question impressively"
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "Situation-specific behavioral question tied to a responsibility in the JD",
      "answer": "Full STAR answer: Situation (2 sentences) → Task (1 sentence) → Action (3 sentences with specifics) → Result (1-2 sentences with metrics). Make it sound authentic and senior-level.",
      "tip": "One tip to make this STAR answer stand out from other candidates"
    }}
  ],
  "system_design_questions": [
    {{
      "question": "System design question directly relevant to the domain and scale in this JD",
      "approach": [
        "Step 1: Clarify requirements — ask about scale, latency, consistency needs",
        "Step 2: High-level architecture — describe main components",
        "Step 3: Deep dive into the most critical component",
        "Step 4: Address data storage — SQL vs NoSQL choice with justification",
        "Step 5: Scaling strategy — horizontal scaling, caching, CDN",
        "Step 6: Failure handling — what breaks first and how to fix it"
      ],
      "key_concepts": "2-3 key concepts the interviewer is testing with this question"
    }}
  ]
}}

RULES:
- Generate exactly 7 technical questions, 5 behavioral questions, 3 system design questions
- Technical answers must be 4-6 sentences minimum — not one-liners
- STAR answers must be complete with a measurable Result
- System design must have exactly 6 steps
- Make every question feel like it came from a real senior engineer at this company
- Reference specific tools/technologies from the JD (not generic "a database" — say "PostgreSQL" or "Redis")"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.4
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown fences
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    p = part.strip()
                    if p.startswith("json"): p = p[4:].strip()
                    if p.startswith("{"): raw = p; break
            return json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error: {e}. Using fallback.")
            return self._fallback_questions(domain, skills)
        except Exception as e:
            print(f"   ⚠️ LLM error: {e}. Using fallback.")
            return self._fallback_questions(domain, skills)

    def _generate_talking_points(self, domain, skills, responsibilities, resume_text) -> List[str]:
        top_skills = ", ".join(skills[:6])
        resp_sample = responsibilities[0] if responsibilities else "delivering high-quality work"
        prompt = f"""For a {domain} interview, give 5 powerful talking points a candidate should weave into answers.
Skills to highlight: {top_skills}
Key responsibility: {resp_sample}

Return ONLY a JSON array of 5 strings. Each string = 1 complete sentence, action-oriented, specific.
["point 1", "point 2", "point 3", "point 4", "point 5"]"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500, temperature=0.3
            )
            raw = resp.choices[0].message.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1].strip()
                if raw.startswith("json"): raw = raw[4:]
            return json.loads(raw)
        except Exception:
            return [
                f"Demonstrate hands-on experience with {skills[0] if skills else 'core tech'} through specific project examples",
                "Quantify every achievement — use numbers, percentages, and scale",
                "Show cross-functional collaboration experience with engineers, PMs, and designers",
                "Highlight continuous learning: recent projects, certifications, or open-source work",
                "Directly connect your past accomplishments to the responsibilities of this role"
            ]

    def _get_prep_tips(self, seniority: str, domain: str) -> List[str]:
        base = [
            "Research the company's tech stack, recent blog posts, and product announcements before the interview",
            "Prepare 3-4 concrete STAR stories covering: leadership, technical challenge, failure+learning, impact",
            "Practice explaining your projects out loud — timing yourself helps (aim for 2 min per project)",
            "Have 3 thoughtful questions ready for the interviewer that show you've done your research",
            "Review everything listed on your resume — expect deep follow-up on anything you mention",
            "For live coding: think aloud, start with brute-force, then optimize — silence is worse than wrong",
        ]
        senior_extras = [
            "Prepare system design answers at scale (10M+ users) — show you think beyond the happy path",
            "Be ready to discuss architecture decisions you've owned and the tradeoffs you made",
            "Have examples of mentoring others, conducting code reviews, or influencing technical roadmaps",
        ]
        entry_extras = [
            "Your projects are your strongest asset — know every technical decision you made and why",
            "Show learning velocity — mention how quickly you picked up new technologies in past projects",
            "It's fine to say 'I haven't used X, but here's how I'd approach learning it' — shows maturity",
        ]
        if seniority in ("senior","lead"):   return base + senior_extras
        elif seniority == "entry-level":     return base + entry_extras
        return base

    def _fallback_questions(self, domain: str, skills: List[str]) -> Dict:
        s0 = skills[0] if skills else "Python"
        s1 = skills[1] if len(skills) > 1 else "SQL"
        return {
            "technical_questions": [
                {
                    "question": f"Walk me through a project where you used {s0} to solve a real business problem. What was the problem, your approach, and the outcome?",
                    "answer": f"Describe a specific project in detail — the business context, why {s0} was the right tool, the technical challenges you faced, how you overcame them, and the measurable impact. Include scale (users, data size, performance).",
                    "follow_up": "How would you do it differently if you started today?",
                    "tip": "Lead with the business impact first, then go into technical depth. Interviewers care about outcomes, not just code."
                },
                {
                    "question": f"Explain how you would optimize a slow {s1} query that's causing performance issues in production.",
                    "answer": f"Start by using EXPLAIN/EXPLAIN ANALYZE to understand the query plan. Check for missing indexes on columns used in WHERE/JOIN clauses. Look for N+1 query problems, unnecessary full table scans, and consider query restructuring. Add covering indexes, consider query caching, and evaluate whether the data model itself needs optimization.",
                    "follow_up": "What if adding an index made it worse?",
                    "tip": "Show systematic debugging — don't jump to solutions. The process matters as much as the answer."
                }
            ],
            "behavioral_questions": [
                {
                    "question": "Tell me about a time you had to deliver a project under significant time pressure. What trade-offs did you make?",
                    "answer": "Situation: We had a product launch in 2 weeks but the feature was only 40% complete. Task: I was responsible for delivering the core functionality on time. Action: I broke the scope into must-have vs nice-to-have, communicated clearly with stakeholders about what we could realistically ship, and focused the team on the critical path. Result: We shipped on time with 80% of planned features, and the remaining 20% were delivered in the following sprint with no user impact.",
                    "tip": "Show that you can make smart trade-off decisions under pressure, not just grind harder."
                }
            ],
            "system_design_questions": [
                {
                    "question": f"Design a scalable {domain} system that can handle 1 million daily active users.",
                    "approach": [
                        "Step 1: Clarify requirements — read/write ratio, latency SLA, consistency needs, geography",
                        "Step 2: Estimate scale — 1M DAU means ~12 req/sec average, ~120 req/sec peak",
                        "Step 3: High-level architecture — Load Balancer → API servers → Cache → DB",
                        "Step 4: Database choice — PostgreSQL for relational data, Redis for sessions/cache",
                        "Step 5: Scaling — horizontal scaling of API layer, read replicas for DB, CDN for static assets",
                        "Step 6: Failure modes — what if DB goes down? Cache stampede? Handle with circuit breakers and graceful degradation"
                    ],
                    "key_concepts": "Horizontal scaling, caching strategies, database replication"
                }
            ]
        }
