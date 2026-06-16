"""Create or reset the seeded admin account with a real password hash.

Run after importing schema.sql:
    python seed_admin.py
"""
import sys
from werkzeug.security import generate_password_hash
from db import query

EMAIL = "admin@example.com"
NAME = "Admin"
PASSWORD = sys.argv[1] if len(sys.argv) > 1 else "admin123"

pw_hash = generate_password_hash(PASSWORD, method="pbkdf2:sha256")

query(
    """
    INSERT INTO employees (name, email, password_hash, role)
    VALUES (%s, %s, %s, 'admin')
    ON CONFLICT(email) DO UPDATE SET
      password_hash=excluded.password_hash, role='admin', name=excluded.name
    """,
    (NAME, EMAIL, pw_hash),
    fetch=False, commit=True,
)
print(f"Admin ready: {EMAIL} / {PASSWORD}")
