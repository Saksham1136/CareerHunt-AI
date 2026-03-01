"""
database/db_manager.py
-----------------------
SQLite Database Manager

Handles all database operations:
- Connection management
- Table creation (schema)
- CRUD operations for users, searches, resumes, interviews

Tables:
    users           — registered accounts
    job_searches    — saved job search results
    resume_versions — saved optimized resumes
    interview_sessions — saved interview Q&A sets
    activity_log    — admin audit trail
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "job_seeker.db")


# ─────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """
    Get a SQLite connection with row_factory for dict-like access.
    Creates the DB file if it doesn't exist.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # Allows row["column"] access
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────────────────────────
# Schema Initialization
# ─────────────────────────────────────────────

def init_db():
    """
    Create all tables if they don't exist.
    Safe to call on every app startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    UNIQUE NOT NULL,
            email           TEXT    UNIQUE NOT NULL,
            password_hash   TEXT    NOT NULL,
            full_name       TEXT    DEFAULT '',
            phone           TEXT    DEFAULT '',
            location        TEXT    DEFAULT '',
            linkedin_url    TEXT    DEFAULT '',
            github_url      TEXT    DEFAULT '',
            role            TEXT    DEFAULT 'user',   -- 'user' or 'admin'
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT    DEFAULT (datetime('now')),
            last_login      TEXT    DEFAULT NULL
        )
    """)

    # ── Job Searches table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_searches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            search_role     TEXT    NOT NULL,
            search_location TEXT    DEFAULT '',
            experience_yrs  INTEGER DEFAULT 0,
            results_json    TEXT    NOT NULL,   -- JSON blob of job listings
            jobs_count      INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Resume Versions table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_versions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            version_name        TEXT    DEFAULT 'Resume',
            original_resume     TEXT    NOT NULL,   -- Raw resume text
            optimized_resume    TEXT    NOT NULL,   -- ATS-optimized text
            job_description     TEXT    DEFAULT '',
            target_role         TEXT    DEFAULT '',
            ats_score_before    INTEGER DEFAULT 0,
            ats_score_after     INTEGER DEFAULT 0,
            matched_keywords    TEXT    DEFAULT '[]',  -- JSON list
            missing_keywords    TEXT    DEFAULT '[]',  -- JSON list
            docx_filename       TEXT    DEFAULT '',
            created_at          TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Interview Sessions table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_name    TEXT    DEFAULT 'Interview Prep',
            target_role     TEXT    DEFAULT '',
            domain          TEXT    DEFAULT '',
            seniority       TEXT    DEFAULT '',
            questions_json  TEXT    NOT NULL,   -- Full Q&A JSON blob
            total_questions INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Activity Log (Admin) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
            username    TEXT    DEFAULT '',
            action      TEXT    NOT NULL,   -- e.g. 'login', 'search', 'resume_saved'
            details     TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


# ─────────────────────────────────────────────
# USER Operations
# ─────────────────────────────────────────────

def create_user(username: str, email: str, password_hash: str, full_name: str = "") -> Optional[int]:
    """
    Insert a new user. Returns new user ID or None on failure (e.g. duplicate).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        """, (username.strip().lower(), email.strip().lower(), password_hash, full_name))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None  # Username or email already exists


def get_user_by_username(username: str) -> Optional[Dict]:
    """Fetch a user record by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Fetch a user record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_last_login(user_id: int):
    """Update last_login timestamp."""
    conn = get_connection()
    conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user_profile(user_id: int, full_name: str, phone: str, location: str,
                         linkedin_url: str, github_url: str):
    """Update a user's profile fields."""
    conn = get_connection()
    conn.execute("""
        UPDATE users
        SET full_name = ?, phone = ?, location = ?, linkedin_url = ?, github_url = ?
        WHERE id = ?
    """, (full_name, phone, location, linkedin_url, github_url, user_id))
    conn.commit()
    conn.close()


def get_all_users() -> List[Dict]:
    """Admin: get all registered users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email, full_name, role, is_active, created_at, last_login
        FROM users ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id: int, is_active: bool):
    """Admin: activate or deactivate a user."""
    conn = get_connection()
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# JOB SEARCH Operations
# ─────────────────────────────────────────────

def save_job_search(user_id: int, role: str, location: str, experience: int, jobs: List[Dict]) -> int:
    """Save a job search result for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO job_searches (user_id, search_role, search_location, experience_yrs, results_json, jobs_count)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, role, location, experience, json.dumps(jobs), len(jobs)))
    search_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return search_id


def get_user_job_searches(user_id: int) -> List[Dict]:
    """Get all saved job searches for a user, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM job_searches WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["results_json"] = json.loads(d["results_json"])  # Parse JSON back to list
        results.append(d)
    return results


def delete_job_search(search_id: int, user_id: int):
    """Delete a saved search (user can only delete their own)."""
    conn = get_connection()
    conn.execute("DELETE FROM job_searches WHERE id = ? AND user_id = ?", (search_id, user_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# RESUME VERSION Operations
# ─────────────────────────────────────────────

def save_resume_version(
    user_id: int, version_name: str, original_resume: str, optimized_resume: str,
    job_description: str, target_role: str, ats_before: int, ats_after: int,
    matched_kw: List[str], missing_kw: List[str], docx_filename: str = ""
) -> int:
    """Save an optimized resume version for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resume_versions
        (user_id, version_name, original_resume, optimized_resume, job_description,
         target_role, ats_score_before, ats_score_after, matched_keywords, missing_keywords, docx_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, version_name, original_resume, optimized_resume, job_description,
        target_role, ats_before, ats_after,
        json.dumps(matched_kw), json.dumps(missing_kw), docx_filename
    ))
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id


def get_user_resumes(user_id: int) -> List[Dict]:
    """Get all saved resume versions for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM resume_versions WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["matched_keywords"] = json.loads(d["matched_keywords"])
        d["missing_keywords"] = json.loads(d["missing_keywords"])
        results.append(d)
    return results


def delete_resume_version(resume_id: int, user_id: int):
    """Delete a resume version."""
    conn = get_connection()
    conn.execute("DELETE FROM resume_versions WHERE id = ? AND user_id = ?", (resume_id, user_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# INTERVIEW SESSION Operations
# ─────────────────────────────────────────────

def save_interview_session(
    user_id: int, session_name: str, target_role: str,
    domain: str, seniority: str, questions_data: Dict
) -> int:
    """Save an interview prep session."""
    total = (
        len(questions_data.get("technical_questions", [])) +
        len(questions_data.get("behavioral_questions", [])) +
        len(questions_data.get("system_design_questions", []))
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO interview_sessions
        (user_id, session_name, target_role, domain, seniority, questions_json, total_questions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, session_name, target_role, domain, seniority, json.dumps(questions_data), total))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_user_interview_sessions(user_id: int) -> List[Dict]:
    """Get all saved interview sessions for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM interview_sessions WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["questions_json"] = json.loads(d["questions_json"])
        results.append(d)
    return results


def delete_interview_session(session_id: int, user_id: int):
    """Delete an interview session."""
    conn = get_connection()
    conn.execute("DELETE FROM interview_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# ACTIVITY LOG Operations
# ─────────────────────────────────────────────

def log_activity(user_id: int, username: str, action: str, details: str = ""):
    """Log a user action for the admin audit trail."""
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO activity_log (user_id, username, action, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, action, details))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Never let logging break the main flow


def get_recent_activity(limit: int = 100) -> List[Dict]:
    """Admin: get recent activity log entries."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# ADMIN STATS
# ─────────────────────────────────────────────

def get_admin_stats() -> Dict:
    """Get summary statistics for the admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    stats["total_users"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    stats["total_admins"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM job_searches")
    stats["total_searches"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resume_versions")
    stats["total_resumes"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM interview_sessions")
    stats["total_interviews"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-7 days')")
    stats["new_users_week"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT search_role, COUNT(*) as cnt
        FROM job_searches GROUP BY search_role ORDER BY cnt DESC LIMIT 5
    """)
    stats["top_roles"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return stats
