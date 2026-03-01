"""
auth/auth_manager.py
---------------------
Authentication Manager

Handles:
- Password hashing (bcrypt)
- User registration with validation
- Login verification
- Streamlit session state management
- Admin access control

Security practices used:
- bcrypt password hashing (industry standard)
- No plain-text passwords stored anywhere
- Session state cleared on logout
- Email + username uniqueness enforced at DB level
"""

import re
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    import hashlib  # Fallback (less secure, but works without bcrypt)

from database.db_manager import (
    create_user, get_user_by_username, update_last_login,
    log_activity, init_db
)


# ─────────────────────────────────────────────
# Password Utilities
# ─────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt (preferred) or SHA-256 fallback.
    Returns the hash as a string for storage.
    """
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        # SHA-256 fallback — less secure but functional without bcrypt
        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a stored hash.
    """
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False
    else:
        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == hashed_password


# ─────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────

def validate_registration(username: str, email: str, password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Validate registration form inputs.
    Returns (is_valid: bool, error_message: str)
    """
    if not username or len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."

    if not email or not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
        return False, "Please enter a valid email address."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    if password != confirm_password:
        return False, "Passwords do not match."

    return True, ""


# ─────────────────────────────────────────────
# Registration & Login
# ─────────────────────────────────────────────

def register_user(username: str, email: str, password: str, full_name: str = "") -> tuple[bool, str]:
    """
    Register a new user.
    Returns (success: bool, message: str)
    """
    password_hash = hash_password(password)
    user_id = create_user(
        username=username.strip().lower(),
        email=email.strip().lower(),
        password_hash=password_hash,
        full_name=full_name.strip()
    )

    if user_id is None:
        return False, "Username or email already exists. Please try a different one."

    log_activity(user_id, username, "register", f"New user registered: {email}")
    return True, f"Account created successfully! Welcome, {username}."


def login_user(username: str, password: str) -> tuple[bool, str]:
    """
    Authenticate a user and set session state.
    Returns (success: bool, message: str)
    """
    user = get_user_by_username(username.strip().lower())

    if not user:
        return False, "Invalid username or password."

    if not user["is_active"]:
        return False, "Your account has been deactivated. Contact admin."

    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password."

    # Set Streamlit session state
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["full_name"] = user["full_name"] or user["username"]
    st.session_state["email"] = user["email"]
    st.session_state["role"] = user["role"]
    st.session_state["user_data"] = user

    update_last_login(user["id"])
    log_activity(user["id"], user["username"], "login", "User logged in")

    return True, f"Welcome back, {user['full_name'] or user['username']}!"


def logout_user():
    """Clear session state and log the logout."""
    user_id = st.session_state.get("user_id")
    username = st.session_state.get("username", "unknown")

    if user_id:
        log_activity(user_id, username, "logout", "User logged out")

    # Clear all session state keys
    for key in ["authenticated", "user_id", "username", "full_name", "email", "role", "user_data"]:
        if key in st.session_state:
            del st.session_state[key]


# ─────────────────────────────────────────────
# Session Helpers
# ─────────────────────────────────────────────

def is_authenticated() -> bool:
    """Check if the current session has a logged-in user."""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Check if the current user has admin role."""
    return st.session_state.get("role") == "admin"


def get_current_user_id() -> int:
    """Get the current logged-in user's ID."""
    return st.session_state.get("user_id", 0)


def get_current_username() -> str:
    """Get the current logged-in user's username."""
    return st.session_state.get("username", "")


def require_auth():
    """
    Decorator-style guard. Call at the top of any page that requires login.
    Redirects to login page if not authenticated.
    """
    if not is_authenticated():
        st.warning("⚠️ Please log in to access this page.")
        st.stop()


def require_admin():
    """Guard for admin-only pages."""
    require_auth()
    if not is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        st.stop()


# ─────────────────────────────────────────────
# Seed Admin Account
# ─────────────────────────────────────────────

def seed_admin_if_needed():
    """
    Create a default admin account if no admin exists.
    Admin credentials: username=admin / password=admin123
    Change this immediately after first login!
    """
    from database.db_manager import get_all_users, get_connection
    import sqlite3

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    conn.close()

    if admin_count == 0:
        password_hash = hash_password("admin123")
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES ('admin', 'admin@jobseeker.ai', ?, 'System Admin', 'admin')
            """, (password_hash,))
            conn.commit()
            print("✅ Default admin created: username=admin / password=admin123")
            print("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY after first login!")
        except sqlite3.IntegrityError:
            pass  # Admin already exists
        finally:
            conn.close()
