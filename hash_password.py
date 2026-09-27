"""
Generate a secure password hash for the admin login.

Usage (from the project folder):
    python tools/hash_password.py

Paste the printed line into .streamlit/secrets.toml as ADMIN_PASSWORD_HASH.
Uses PBKDF2-SHA256 from the Python standard library (same as auth.py).
"""

import base64
import getpass
import hashlib
import secrets

ITERATIONS = 390_000


def main() -> None:
    pw = getpass.getpass("New admin password (min 10 characters): ")
    if len(pw) < 10:
        raise SystemExit("Password too short - use at least 10 characters.")
    if pw != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITERATIONS)
    value = f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
    print("\nAdd this line to .streamlit/secrets.toml:\n")
    print(f'ADMIN_PASSWORD_HASH = "{value}"')


if __name__ == "__main__":
    main()
