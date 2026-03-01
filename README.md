# 🤖 Multi-Agent AI Job Seeker

> An AI-powered application that helps job seekers find relevant jobs, optimize their resumes for ATS, and prepare for interviews — built with a modular multi-agent architecture.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203-green)
![CrewAI](https://img.shields.io/badge/Agents-CrewAI-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Agent Responsibilities](#-agent-responsibilities)
- [Tech Stack](#-tech-stack)
- [Folder Structure](#-folder-structure)
- [Quick Start (Local)](#-quick-start-local)
- [Deployment Guide](#-deployment-guide)
- [How to Use](#-how-to-use)
- [Design Decisions](#-design-decisions)
- [Limitations & Future Improvements](#-limitations--future-improvements)

---

## 🎯 Project Overview

The Multi-Agent AI Job Seeker is a production-quality Python application that supports users across the entire job application lifecycle:

1. **Job Discovery** — Search and rank relevant job openings by role, location, and experience
2. **Resume Optimization** — Tailor and ATS-optimize your resume for a specific job description
3. **Interview Preparation** — Get role-specific technical + behavioral Q&A with model answers
4. **Resume Download** — Download your optimized resume as a formatted ATS-friendly DOCX file

---

## 🏗️ System Architecture

```
User Input (Streamlit UI)
        │
        ▼
┌─────────────────────────┐
│   Orchestrator (CrewAI)  │  ← Manages agent sequence & error handling
└─────────────────────────┘
        │
   ┌────┴──────────────────────────────────┐
   │              │              │          │
   ▼              ▼              ▼          ▼
Job Discovery  Job Profiling  Resume    Interview
   Agent          Agent        Agent      Agent
   │               │             │          │
   └───────────────┴─────────────┴──────────┘
                        │
                        ▼
            Results displayed in Streamlit
         (Jobs + ATS Score + Resume Download + Q&A)
```

### Data Flow

```
1. User submits: role, location, experience, resume, JD
2. Orchestrator → Job Discovery Agent → ranked job listings
3. Orchestrator → Job Profiling Agent → structured job profile (skills, keywords, responsibilities)
4. Job Profile → Resume Agent → ATS-optimized resume + DOCX file
5. Job Profile → Interview Agent → Q&A + preparation tips
6. All results → Streamlit UI
```

---

## 🤖 Agent Responsibilities

| Agent | Input | Output | Why Separate? |
|-------|-------|--------|---------------|
| **Job Discovery** | role, location, experience | Ranked job list | Swappable data source (mock → live API) |
| **Job Profiling** | Job description text | Structured profile (skills, keywords) | Both Resume & Interview agents need this; parse once, share everywhere |
| **Resume Optimizer** | Resume text + Job profile | ATS resume text + DOCX file | Involves NLP, document generation — distinct concern |
| **Interview Prep** | Job profile | Technical + behavioral Q&A | Pure generative task, stateless |
| **Orchestrator** | All inputs | Unified result dict | Decouples agents; one failure doesn't break everything |

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.10+ | Industry standard for AI/ML |
| LLM | Groq (LLaMA 3 8B) | Free tier, fast inference |
| Agent Framework | CrewAI | Role-based multi-agent design |
| UI | Streamlit | Fast, Python-native, deployable |
| Document Generation | python-docx | ATS-safe DOCX generation |
| NLP | Custom keyword extractor | Lightweight, no heavy model downloads |
| Config | python-dotenv | Secure API key handling |

---

## 📁 Folder Structure

```
job_seeker_ai/
│
├── agents/                        # One file per agent
│   ├── job_discovery_agent.py     # Searches and ranks job listings
│   ├── job_profiling_agent.py     # Parses job descriptions
│   ├── resume_agent.py            # Optimizes and formats resumes
│   └── interview_agent.py         # Generates interview Q&A
│
├── orchestrator/
│   └── crew_orchestrator.py       # Coordinates all agents
│
├── tools/                         # Reusable utilities
│   ├── nlp_utils.py               # Keyword extraction, scoring
│   ├── resume_parser.py           # Parse .txt and .docx uploads
│   ├── resume_formatter.py        # Generate ATS DOCX output
│   └── job_data_loader.py         # Load & filter job dataset
│
├── data/
│   ├── sample_jobs.json           # 12 realistic mock job listings
│   └── ats_keywords.json          # ATS keyword reference data
│
├── ui/
│   └── app.py                     # Streamlit UI (all pages + components)
│
├── config/
│   └── settings.py                # Centralized config & env vars
│
├── tests/
│   ├── test_job_discovery.py      # Tests for job search logic
│   └── test_nlp_utils.py          # Tests for NLP utilities
│
├── outputs/                       # Generated resume files (gitignored)
├── .streamlit/config.toml         # Streamlit theme & server config
├── .env.example                   # Template for API keys
├── .gitignore
├── requirements.txt
├── run.sh                         # One-command local startup
└── README.md
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.10 or higher
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Step 1: Clone the repository
```bash
git clone https://github.com/yourusername/job-seeker-ai.git
cd job-seeker-ai
```

### Step 2: Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set up your API key
```bash
cp .env.example .env
# Open .env and replace 'your_groq_api_key_here' with your actual key
```

### Step 5: Run the app
```bash
streamlit run ui/app.py
```
The app will open at **http://localhost:8501**

Or use the one-command script:
```bash
bash run.sh
```

### Run tests
```bash
pytest tests/ -v
```

---

## 🌐 Deployment Guide

### Deploy to Streamlit Cloud (Free)

1. Push your code to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New App"**
4. Connect your GitHub repo
5. Set **Main file path** to: `ui/app.py`
6. Click **"Advanced settings"** → add your environment variable:
   ```
   GROQ_API_KEY = your_actual_groq_key
   ```
7. Click **"Deploy"** — your app goes live in ~2 minutes!

### Deploy to Hugging Face Spaces (Alternative)

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Choose **Streamlit** as the SDK
3. Upload all project files
4. Add `GROQ_API_KEY` in **Settings → Repository secrets**
5. The Space builds and deploys automatically

---

## 📖 How to Use

1. **Fill in the sidebar:**
   - Enter your target job role (e.g., "Data Scientist")
   - Set your preferred location and years of experience
   - Paste or upload your current resume
   - Paste a job description you want to apply for (optional)

2. **Choose a run mode:**
   - **Full Pipeline** — runs all 4 agents (recommended)
   - **Job Search Only** — just find matching jobs
   - **Resume Optimization Only** — tailor resume to a specific JD
   - **Interview Prep Only** — generate Q&A for a role

3. **Click "Run AI Pipeline"** and wait ~30-60 seconds

4. **Review results across tabs:**
   - 🔍 Jobs Found — ranked listings with skills breakdown
   - 📝 Optimized Resume — ATS score, keyword analysis, download button
   - 🎤 Interview Prep — technical, behavioral, and system design Q&A
   - 🔬 Job Profile — structured analysis of the job description

---

## 🧠 Design Decisions

**Why separate agents instead of one big prompt?**
Each agent has a single responsibility, making them independently testable, replaceable, and debuggable. If the Resume Agent fails, the Interview Agent still runs.

**Why Groq instead of OpenAI?**
Groq's free tier offers extremely fast inference (LPU hardware). For a portfolio/demo project, speed matters and cost = $0.

**Why a mock job dataset instead of a live API?**
LinkedIn and Indeed require paid developer access. A well-structured mock dataset demonstrates identical engineering skill without demo failures or API costs.

**Why python-docx instead of PDF for resume download?**
DOCX is editable (users want to make final tweaks) and widely accepted by ATS systems. PDFs from code can have formatting issues that break ATS parsing.

**Why stateless agents?**
Each agent takes inputs and returns outputs with no internal state. This makes them thread-safe, independently testable, and easy to replace with better implementations.

---

## ⚠️ Limitations & Future Improvements

### Current Limitations
- Job listings are from a mock dataset (12 listings) — not live job boards
- Resume DOCX generation creates a structured format, but may not preserve exact original formatting
- No user authentication or session persistence
- Single-language support (English only)

### Planned Improvements
- [ ] Integrate live job APIs (Adzuna, JSearch via RapidAPI)
- [ ] Add PDF resume download option
- [ ] Add resume version history and comparison
- [ ] Support LinkedIn profile import
- [ ] Add cover letter generation agent
- [ ] Multi-language support (Hindi, etc.)
- [ ] User accounts with saved searches
- [ ] Email notification for new matching jobs

---

## 👨‍💻 Author

**Saksham Singh**
- Built as a technical assessment submission
- Demonstrates: multi-agent AI system design, NLP, LLM integration, full-stack Python development

---

## 📄 License

MIT License — free to use, modify, and distribute.
