"""Settings - receipt options, services list, data export & backup."""

import re
import sqlite3
import tempfile
from pathlib import Path

import streamlit as st

import database as db
import services as svc
from auth import SESSION_TIMEOUT_SECONDS
from ui import admin_page
from utils import today_london

admin_page("Settings", "Receipts, services and data backups.")

tab_receipts, tab_services, tab_data, tab_account = st.tabs(["Receipts", "Services", "Data & backup", "Account"])

with tab_receipts:
    with st.form("adm_receipt_settings"):
        prefix = st.text_input("Receipt number prefix", svc.get_setting("receipt_prefix", "JA"), max_chars=6,
                               help="Receipts are numbered PREFIX-YEAR-0001, e.g. JA-2026-0001.")
        footer = st.text_input("Receipt footer message", svc.get_setting("receipt_footer", ""), max_chars=110)
        if st.form_submit_button("Save", type="primary"):
            if not re.fullmatch(r"[A-Za-z0-9]{1,6}", prefix.strip()):
                st.error("Prefix must be 1–6 letters or numbers.")
            else:
                svc.set_setting("receipt_prefix", prefix.strip().upper())
                svc.set_setting("receipt_footer", footer)
                st.toast("Settings saved", icon="✅")
    st.caption("No VAT or tax details are printed on receipts. Add them here only if the business is VAT registered "
               "(this would need a small code change in receipt_pdf.py).")

with tab_services:
    st.caption("Inactive services are hidden from the website quote form and new jobs. "
               "Descriptions and images for the website are edited in config.py.")
    for s in svc.list_services():
        active = st.toggle(s["name"], value=bool(s["active"]), key=f"adm_svc_{s['id']}")
        if active != bool(s["active"]):
            svc.set_service_active(s["id"], active)
            st.rerun()

with tab_data:
    st.markdown("**Export tables as CSV**")
    cols = st.columns(3)
    for i, table in enumerate(["clients", "jobs", "payments", "receipts", "enquiries", "services"]):
        df = svc.export_table(table)
        cols[i % 3].download_button(
            f"{table.title()} ({len(df)})", df.to_csv(index=False).encode(),
            f"ja-{table}-{today_london()}.csv", "text/csv", key=f"adm_exp_{table}", width="stretch",
            icon=":material/table_view:",
        )
    st.caption("Money columns in raw exports are in pence (e.g. 12550 = £125.50).")
    st.divider()
    st.markdown("**Full database backup**")
    if st.button("Prepare backup file", icon=":material/backup:"):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "backup.db"
            src = db.get_connection()
            try:
                with sqlite3.connect(dest) as out:
                    src.backup(out)  # consistent online copy
            finally:
                src.close()
            st.session_state["adm_backup"] = dest.read_bytes()
    if st.session_state.get("adm_backup"):
        st.download_button("Download database backup", st.session_state["adm_backup"],
                           f"ja-detailing-backup-{today_london()}.db", "application/octet-stream",
                           type="primary", icon=":material/download:")

with tab_account:
    st.markdown(
        f"""
- You are signed in as the administrator.
- Sessions expire automatically after **{SESSION_TIMEOUT_SECONDS // 3600} hours**.
- After 5 failed login attempts, admin login is locked for 5 minutes.
- To change the admin username or password, update `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH` in
  `.streamlit/secrets.toml` (or the Secrets panel on Streamlit Community Cloud).
  Generate a new hash with `python tools/hash_password.py`.
"""
    )
