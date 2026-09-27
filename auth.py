"""
Admin authentication.

Credentials are read from Streamlit secrets (``.streamlit/secrets.toml`` or the
Streamlit Community Cloud "Secrets" panel) or environment variables - never
from code, and never shown in the UI.

Supported settings (secrets.toml top level, or env vars):

    ADMIN_USERNAME       = "your-username"
    ADMIN_PASSWORD_HASH  = "pbkdf2_sha256$...."   # recommended - see tools/hash_password.py
    ADMIN_PASSWORD       = "..."                  # plain alternative (less secure)

If ADMIN_PASSWORD_HASH is set, it takes priority over ADMIN_PASSWORD.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time

import streamlit as st

log = logging.getLogger("ja_detailing.auth")

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 5 * 60
SESSION_TIMEOUT_SECONDS = 8 * 60 * 60  # 8 hours
PBKDF2_ITERATIONS = 390_000


# ---------------------------------------------------------------------------
# Password hashing (standard library only - no extra dependency)
# ---------------------------------------------------------------------------
def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iterations, salt_b64, hash_b64 = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Config lookup
# ---------------------------------------------------------------------------
def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
        admin = st.secrets.get("admin")  # also allow an [admin] table
        if admin and admin.get(name.replace("ADMIN_", "").lower()):
            return str(admin.get(name.replace("ADMIN_", "").lower()))
    except Exception:
        pass  # no secrets.toml - fall back to environment
    return os.environ.get(name, "")


def admin_configured() -> bool:
    return bool(_secret("ADMIN_USERNAME") and (_secret("ADMIN_PASSWORD_HASH") or _secret("ADMIN_PASSWORD")))


def _credentials_match(username: str, password: str) -> bool:
    expected_user = _secret("ADMIN_USERNAME")
    pw_hash = _secret("ADMIN_PASSWORD_HASH")
    pw_plain = _secret("ADMIN_PASSWORD")
    if not expected_user or not (pw_hash or pw_plain):
        return False
    user_ok = hmac.compare_digest(username.strip().encode(), expected_user.encode())
    if pw_hash:
        pw_ok = verify_password(password, pw_hash)
    else:
        pw_ok = hmac.compare_digest(password.encode(), pw_plain.encode())
    return user_ok and pw_ok


# ---------------------------------------------------------------------------
# Session handling
# ---------------------------------------------------------------------------
@st.cache_resource
def _global_attempts() -> dict:
    """Server-wide failed-attempt tracker (survives page refreshes)."""
    return {"count": 0, "locked_until": 0.0}


def is_authenticated() -> bool:
    if not st.session_state.get("admin_authenticated"):
        return False
    started = st.session_state.get("admin_login_time", 0)
    if time.time() - started > SESSION_TIMEOUT_SECONDS:
        logout()
        return False
    return True


def lockout_remaining() -> int:
    tracker = _global_attempts()
    return max(0, int(tracker["locked_until"] - time.time()))


def login(username: str, password: str) -> tuple[bool, str]:
    """Attempt to log in. Returns (success, user-facing message)."""
    if not admin_configured():
        return False, "Admin access has not been configured yet. See README → Admin setup."
    remaining = lockout_remaining()
    if remaining:
        return False, f"Too many failed attempts. Try again in {remaining // 60 + 1} minute(s)."

    tracker = _global_attempts()
    if _credentials_match(username or "", password or ""):
        tracker["count"] = 0
        st.session_state["admin_authenticated"] = True
        st.session_state["admin_login_time"] = time.time()
        log.info("Admin login successful")
        return True, "Welcome back."

    tracker["count"] += 1
    time.sleep(0.8)  # slow down brute-force attempts
    log.warning("Failed admin login attempt (%s)", tracker["count"])
    if tracker["count"] >= MAX_ATTEMPTS:
        tracker["locked_until"] = time.time() + LOCKOUT_SECONDS
        tracker["count"] = 0
        return False, "Too many failed attempts. Admin login is locked for 5 minutes."
    return False, "Incorrect username or password."


def logout() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("admin_") or key.startswith("adm_"):
            del st.session_state[key]


def require_admin() -> None:
    """Call at the top of EVERY admin page. Stops rendering if not logged in."""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
