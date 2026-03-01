# 🤖 CareerHunt AI — Multi-Agent AI Job Seeker System

> **Find jobs · Optimize your resume · Ace your interviews — all powered by AI**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-orange)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 What is CareerHunt AI?

**CareerHunt AI** is a full-stack multi-agent AI application that automates the three hardest parts of job hunting:

1. 🔍 **Job Discovery** — Searches and ranks jobs by role, location, and experience with direct LinkedIn / Naukri / Indeed apply links
2. 📝 **Resume Optimization** — Rewrites your resume to pass ATS filters, shows before/after score, downloads as professional DOCX
3. 🎤 **Interview Preparation** — Generates role-specific technical, behavioral, and system design Q&A pulled from the actual JD — downloads as PDF

Built as a portfolio project to demonstrate **multi-agent AI architecture**, **LLM integration**, **full-stack development**, and **production-ready engineering practices**.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 Job Search | Fuzzy role matching across 18+ Indian tech companies |
| 🔗 Apply Links | Every job has LinkedIn, Naukri, and Indeed buttons |
| 🎯 ATS Keywords | Extracts must-have, tools, and soft skill keywords per search |
| 📊 ATS Score | Before/after resume score with matched/missing keyword pills |
| ⬇️ DOCX Download | Professional ATS resume — navy/blue theme, Calibri font, proper sections |
| 🎤 Interview Q&A | 7 technical + 5 behavioral + 3 system design questions from your JD |
| 📄 PDF Download | Formatted interview prep PDF — ready instantly, no page refresh |
| 💾 Dashboard | All searches, resumes, and interview sessions saved to your account |
| 🔐 Auth System | Register/login with bcrypt-hashed passwords |
| 🛡️ Admin Panel | User management, activity log, platform insights |

---

## 🏗️ System Architecture

```
                        ┌─────────────────────────┐
                        │     Orchestrator Agent   │
                        │   (crew_orchestrator.py) │
                        └──────┬──────┬──────┬─────┘
                               │      │      │
               ┌───────────────┘      │      └───────────────┐
               ▼                      ▼                       ▼
    ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐
    │  Job Discovery   │  │ Resume Optimizer  │  │ Interview Prep    │
    │     Agent        │  │     Agent         │  │     Agent         │
    └────────┬─────────┘  └────────┬──────────┘  └────────┬──────────┘
             │                     │                       │
             └─────────────────────┼───────────────────────┘
                                   ▼
                        ┌──────────────────┐
                        │  Job Profiling   │
                        │     Agent        │
                        └──────────────────┘
                                   │
                                   ▼
                          Streamlit UI → User
```

### What each agent does

| Agent | Input | Output |
|-------|-------|--------|
| **Job Discovery** | Role, location, experience | Ranked job list with relevance scores |
| **Job Profiling** | Job description text | Domain, seniority, skills, keywords |
| **Resume Optimizer** | Resume + Job Profile | ATS score, optimized text, DOCX file |
| **Interview Prep** | Job Profile + Resume | Deep Q&A based on actual JD content |
| **Orchestrator** | All user inputs | Runs agents in order, passes outputs between them |

---

## 🛠️ Tech Stack

| Technology | Purpose | Why |
|-----------|---------|-----|
| **Python 3.10+** | Core language | Best AI/ML ecosystem |
| **Groq LLaMA 3.1** | LLM backbone | Free tier, fastest inference (LPU hardware) |
| **CrewAI** | Multi-agent framework | Purpose-built for role-based agent workflows |
| **Streamlit** | Web UI | Python-native, rapid development |
| **SQLite + bcrypt** | Auth & persistence | Zero-setup DB, industry-standard password hashing |
| **python-docx** | DOCX resume generation | ATS-friendly, fully editable output |
| **reportlab** | PDF interview prep | Professional formatted reports |

---

## 📁 Project Structure

```
CareerHunt-AI/
│
├── agents/
│   ├── job_discovery_agent.py   # Searches & ranks jobs with fuzzy matching
│   ├── job_profiling_agent.py   # Extracts skills/keywords from JD
│   ├── resume_agent.py          # ATS scoring + resume rewriting
│   └── interview_agent.py       # Deep JD-aware Q&A generation
│
├── orchestrator/
│   └── crew_orchestrator.py     # Runs full pipeline via CrewAI
│
├── tools/
│   ├── nlp_utils.py             # Keyword extraction, ATS scoring
│   ├── job_data_loader.py       # Job search with role aliases
│   ├── resume_parser.py         # Parse .txt and .docx uploads
│   └── resume_formatter.py      # Generate professional ATS DOCX
│
├── auth/
│   └── auth_manager.py          # bcrypt hashing, login, session state
│
├── database/
│   └── db_manager.py            # SQLite schema + CRUD operations
│
├── data/
│   ├── sample_jobs.json         # 18 realistic Indian tech job listings
│   └── ats_keywords.json        # ATS keyword bank by domain
│
├── config/
│   └── settings.py              # API keys, model name, app config
│
├── ui/
│   └── app.py                   # Complete Streamlit app (all in one file)
│
├── tests/
│   ├── test_job_discovery.py
│   └── test_nlp_utils.py
│
├── outputs/                     # Generated DOCX/PDF (gitignored)
├── make_admin.py                # Promote user to admin role
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Local Setup (Step by Step)

### Step 1 — Clone the repo
```bash
git clone https://github.com/Saksham1136/CareerHunt-AI.git
cd CareerHunt-AI
```

### Step 2 — Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Add Groq API key
```bash
cp .env.example .env
```
Open `.env` and paste your key:
```
GROQ_API_KEY=your_actual_key_here
```
👉 Get a **free** key at [console.groq.com](https://console.groq.com) — no credit card needed.

### Step 5 — Run the app
```bash
streamlit run ui/app.py
```
Open **http://localhost:8501** in your browser.

---

## 🔑 Default Login

```
Username : admin
Password : admin123
```
> Change this immediately in the Admin Panel after first login.

---

## 🌐 Deploy Free on Streamlit Cloud

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit - CareerHunt AI"
git branch -M main
git remote add origin https://github.com/Saksham1136/CareerHunt-AI.git
git push -u origin main
```

```
2. Go to → share.streamlit.io
3. Sign in with GitHub
4. Click "New app"
5. Repository  : Saksham1136/CareerHunt-AI
   Branch      : main
   Main file   : ui/app.py
6. Advanced Settings → Secrets → paste:
   GROQ_API_KEY = "your_actual_key_here"
7. Click Deploy — live in ~2 minutes 🎉
```

> ⚠️ SQLite resets on Streamlit Cloud restarts (idle timeout). Fine for demos. For production use [Supabase](https://supabase.com) free PostgreSQL.

---

## 📄 Resume Upload Formats

| Format | Supported |
|--------|-----------|
| `.txt` plain text | ✅ Best |
| `.docx` Word doc | ✅ Works |
| `.pdf` | ❌ Not supported |

---

## 🔐 Security Practices

- Passwords hashed with **bcrypt** — never stored in plain text
- Session state fully cleared on logout
- Admin pages protected with role check on every page load
- All DB queries enforce `user_id` ownership — users can only see/delete their own data

---

## 🔮 Planned Features

- [ ] Live job API integration (LinkedIn, Naukri, Indeed)
- [ ] Cover letter generator agent
- [ ] Job application tracker with status board
- [ ] PostgreSQL / Supabase for persistent cloud storage
- [ ] Side-by-side resume version comparison
- [ ] Mock interview with voice input (Whisper API)

---

## 🧠 Engineering Decisions

**Why a single-file Streamlit app?**
Streamlit auto-discovers `.py` files in any folder named `pages/` and creates separate routes — which breaks when those pages depend on session state. Putting all pages as functions inside `app.py` eliminates this entire class of bugs.

**Why results in `session_state`?**
Every Streamlit button click triggers a full page re-run, which destroys any variables created during the previous run. Storing results in `session_state` immediately after the pipeline runs means DOCX and PDF downloads are always available as pre-generated bytes — no refresh, no data loss.

**Why Groq over OpenAI?**
Free tier with the fastest available LLM inference (LPU hardware). Perfect for portfolio demos with no rate limit anxiety or cost.

**Why mock job data instead of live APIs?**
LinkedIn/Indeed/Naukri require paid or restricted API access. A well-structured mock dataset demonstrates identical engineering skills without live dependencies that could break during a demo.

**Why stateless agents?**
Single Responsibility Principle. Each agent can be tested, replaced, or improved independently. One agent failing does not crash the full pipeline.

---

# 📸 Screenshots

> Coming soon — add screenshots of Job Search, ATS Score, Interview PDF here
<img width="1096" height="778" alt="Screenshot 2026-03-02 034615" src="https://github.com/user-attachments/assets/a2e82cb2-4da4-4c51-99d1-9362e0ead256" />
<img width="1908" height="810" alt="Screenshot 2026-03-02 034926" src="https://github.com/user-attachments/assets/3cf95dcb-6d1b-4274-a476-e00dbb2b0da7" />
<img width="1839" height="763" alt="Screenshot 2026-03-02 035010" src="https://github.com/user-attachments/assets/599e3cd3-208f-4c44-9066-1c1c2e200157" />
<img width="1877" height="759" alt="Screenshot 2026-03-02 035040" src="https://github.com/user-attachments/assets/eb9890a4-5c78-4143-98c2-28737e8c3c3a" />

---

## 📄 License

MIT — free to use, modify, and distribute with attribution.

---

## 👨‍💻 Author

**Saksham Kumar**

📧 sakshamkumar1136@gmail.com
🔗 [LinkedIn](https://www.linkedin.com/in/saksham-kumar-66b410264/)
💻 [GitHub](https://github.com/Saksham1136)

---

<div align="center">
  <strong>⭐ Star this repo if it helped you!</strong><br><br>
  Built with ❤️ using Groq · CrewAI · Streamlit
</div>
