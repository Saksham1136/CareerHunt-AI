"""
config/settings.py
------------------
Central configuration file for the Multi-Agent Job Seeker AI System.
All environment variables, model settings, and constants live here.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────────
# GROQ API SETTINGS
# ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME = "llama-3.1-8b-instant"    # Current free tier Groq model (replaces llama3-8b-8192)
GROQ_MAX_TOKENS = 2048                       # Max tokens per LLM response
GROQ_TEMPERATURE = 0.3                       # Lower = more focused, less random

# ─────────────────────────────────────────────
# FILE PATHS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SAMPLE_JOBS_PATH = os.path.join(DATA_DIR, "sample_jobs.json")
ATS_KEYWORDS_PATH = os.path.join(DATA_DIR, "ats_keywords.json")

# ─────────────────────────────────────────────
# JOB MATCHING SETTINGS
# ─────────────────────────────────────────────
MAX_JOB_RESULTS = 5                          # Number of top jobs to return
EXPERIENCE_TOLERANCE = 1                     # ±1 year flexibility in experience matching

# ─────────────────────────────────────────────
# RESUME SETTINGS
# ─────────────────────────────────────────────
RESUME_OUTPUT_FORMAT = "docx"               # "docx" or "pdf"
ATS_FONT_NAME = "Calibri"
ATS_FONT_SIZE_HEADING = 14
ATS_FONT_SIZE_SUBHEADING = 11
ATS_FONT_SIZE_BODY = 10.5

# ─────────────────────────────────────────────
# APP SETTINGS
# ─────────────────────────────────────────────
APP_TITLE = "🤖 Multi-Agent AI Job Seeker"
APP_ICON = "🤖"
APP_VERSION = "1.0.0"

# Validate critical settings on import
if not GROQ_API_KEY:
    import warnings
    warnings.warn(
        "⚠️  GROQ_API_KEY not found in environment. "
        "Please create a .env file with your Groq API key. "
        "Get a free key at: https://console.groq.com",
        UserWarning
    )
