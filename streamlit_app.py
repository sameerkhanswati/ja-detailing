"""
JA Detailing London - website + admin management system.

Run locally:   streamlit run streamlit_app.py
Public site:   http://localhost:8501/
Admin login:   http://localhost:8501/admin   (not linked anywhere on the public site)

Routing
-------
* Logged-out visitors get ONLY the public home page (and the hidden /admin login
  route). Admin pages are not registered at all, so they cannot be reached.
* After login, the admin pages are registered and shown in the sidebar.
* Every admin page also calls ``require_admin()`` itself (defence in depth).
"""

from __future__ import annotations

import logging

import streamlit as st

from auth import is_authenticated, logout
from config import LOGO_PATH, SEO

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ja_detailing")


def _page_icon():
    try:
        if LOGO_PATH.is_file():
            from PIL import Image

            return Image.open(LOGO_PATH)
    except Exception:
        pass
    return "🚘"


st.set_page_config(
    page_title=SEO["title"],
    page_icon=_page_icon(),
    layout="wide",
    initial_sidebar_state="auto",
)


@st.cache_resource(show_spinner=False)
def _init_database() -> bool:
    """Create tables once per server process. Never crash the public site."""
    try:
        import database

        database.init_db()
        return True
    except Exception:
        log.exception("Database initialisation failed")
        return False


db_ready = _init_database()

home = st.Page("public/home.py", title="Website", icon=":material/language:", default=not is_authenticated())

if is_authenticated():
    if not db_ready:
        st.error("The database could not be opened. Check the server logs and the data/ folder permissions.")

    def _logout():
        logout()
        st.switch_page(home)

    pages = {
        "Business": [
            st.Page("pages/dashboard.py", title="Dashboard", icon=":material/space_dashboard:",
                    url_path="admin", default=True),
            st.Page("pages/enquiries.py", title="Enquiries", icon=":material/inbox:", url_path="enquiries"),
            st.Page("pages/clients.py", title="Clients", icon=":material/group:", url_path="clients"),
            st.Page("pages/jobs.py", title="Jobs", icon=":material/directions_car:", url_path="jobs"),
            st.Page("pages/payments.py", title="Payments", icon=":material/payments:", url_path="payments"),
            st.Page("pages/receipts.py", title="Receipts", icon=":material/receipt_long:", url_path="receipts"),
            st.Page("pages/reports.py", title="Reports", icon=":material/monitoring:", url_path="reports"),
        ],
        "Account": [
            st.Page("pages/settings.py", title="Settings", icon=":material/settings:", url_path="settings"),
            home,
            st.Page(_logout, title="Logout", icon=":material/logout:", url_path="logout"),
        ],
    }
    nav = st.navigation(pages, position="sidebar")
else:
    login = st.Page("pages/admin_login.py", title="Admin Login", icon=":material/lock:", url_path="admin")
    nav = st.navigation([home, login], position="hidden")

nav.run()
