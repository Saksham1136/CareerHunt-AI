"""
make_admin.py
--------------
Utility script to promote any registered user to admin role.

Usage:
    python make_admin.py <username>

Example:
    python make_admin.py saksham

Run this from the project root folder (where requirements.txt is).
The user must already have a registered account before running this.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import init_db, get_connection


def make_admin(username: str):
    init_db()
    username = username.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    # Check user exists
    cursor.execute("SELECT id, username, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        print(f"\n❌ User '{username}' not found.")
        print("   Make sure the user has registered an account first.\n")
        conn.close()
        return

    if user["role"] == "admin":
        print(f"\n✅ '{username}' is already an admin.\n")
        conn.close()
        return

    # Promote to admin
    conn.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    print(f"\n✅ Success! '{username}' has been promoted to admin.")
    print("   Restart the app and log in — you will now see the Admin Panel.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python make_admin.py <username>")
        print("Example: python make_admin.py saksham\n")
        sys.exit(1)

    make_admin(sys.argv[1])
