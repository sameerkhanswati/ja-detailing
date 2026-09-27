"""
Create the admin login (writes .streamlit/secrets.toml for you).

Run by double-clicking SETUP_ADMIN.bat, or:  python tools/setup_admin.py
"""

import base64
import getpass
import hashlib
import secrets
from pathlib import Path

ITERATIONS = 390_000
SECRETS = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"


def main() -> None:
    print("=== JA Detailing London - admin login setup ===\n")
    user = input("Choose an admin username: ").strip()
    if not user or '"' in user:
        raise SystemExit("Invalid username.")
    pw = getpass.getpass("Choose a password (min 10 characters, typing is hidden): ")
    if len(pw) < 10:
        raise SystemExit("Password too short - use at least 10 characters.")
    if pw != getpass.getpass("Type the password again: "):
        raise SystemExit("Passwords do not match.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITERATIONS)
    hashed = f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
    SECRETS.parent.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text(
        "# Admin login - keep this file private. Re-run SETUP_ADMIN.bat to change it.\n"
        f'ADMIN_USERNAME = "{user}"\nADMIN_PASSWORD_HASH = "{hashed}"\n',
        encoding="utf-8",
    )
    print(f"\nDone! Admin login saved. Log in at http://localhost:8501/admin as '{user}'.")
    print("If the website is already running, stop it (Ctrl + C) and start it again.")


if __name__ == "__main__":
    main()
