"""Create or reset the shashekhar employee account.

Login identifier is stored in the `email` column literally as 'shashekhar'
(the login form accepts any string after the type="email" loosening).

Run:
    python seed_shashekhar.py
"""
from werkzeug.security import generate_password_hash
from db import query

LOGIN = "shashekhar"
NAME = "Shashekhar"
PASSWORD = "shashekhar123"

pw_hash = generate_password_hash(PASSWORD, method="pbkdf2:sha256")

query(
    """
    INSERT INTO employees (name, email, password_hash, role)
    VALUES (%s, %s, %s, 'employee')
    ON DUPLICATE KEY UPDATE
      password_hash = VALUES(password_hash),
      name = VALUES(name)
    """,
    (NAME, LOGIN, pw_hash),
    fetch=False, commit=True,
)
print(f"Ready: login='{LOGIN}'  password='{PASSWORD}'")
