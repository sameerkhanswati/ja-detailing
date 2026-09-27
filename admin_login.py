"""Admin login page - reachable only at /admin and never linked from the public site."""

import streamlit as st

from auth import admin_configured, is_authenticated, lockout_remaining, login
from styles import ADMIN_CSS, LOGIN_CSS
from utils import esc, logo_data_uri

st.html(f"<style>{ADMIN_CSS}{LOGIN_CSS}</style>")

if is_authenticated():
    st.rerun()

logo = logo_data_uri(500)
st.html(f"""
<div class="login-brand">
  {f'<img src="{logo}" alt="JA Detailing London logo">' if logo else ''}
  <h1>Admin Login</h1>
  <p>{esc("JA Detailing London · Business management")}</p>
</div>
""")

if not admin_configured():
    st.warning(
        "Admin access isn't configured yet. Add ADMIN_USERNAME and ADMIN_PASSWORD_HASH "
        "(or ADMIN_PASSWORD) to `.streamlit/secrets.toml` - see the README."
    )
    st.stop()

with st.form("admin_login", border=True):
    username = st.text_input("Username", autocomplete="username")
    password = st.text_input("Password", type="password", autocomplete="current-password")
    submitted = st.form_submit_button("Log in", type="primary", width="stretch",
                                      disabled=bool(lockout_remaining()))

if submitted:
    ok, message = login(username, password)
    if ok:
        st.rerun()
    else:
        st.error(message)

st.caption("Authorised staff only. All login attempts are logged.")
