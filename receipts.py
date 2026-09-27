"""Receipts - generate, find and download/print receipts (JA-YYYY-NNNN)."""

import pandas as pd
import streamlit as st

import services as svc
from models import ValidationError
from ui import admin_page, empty_state, kv_panel, money, receipt_download, show_validation
from utils import fmt_date

admin_page("Receipts", "Unique, sequential receipts - download as PDF to send or print.")

with st.container(border=True):
    st.markdown("**Generate a new receipt**")
    options = svc.job_options()
    if not options:
        st.caption("No jobs recorded yet.")
    else:
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        job_id = c1.selectbox("Job", list(options.keys()), index=None, format_func=options.get,
                              placeholder="Select a job", key="adm_rc_job")
        if c2.button("Generate Receipt", type="primary", disabled=not job_id, width="stretch",
                     icon=":material/receipt_long:"):
            try:
                st.session_state["adm_rc_new"] = svc.generate_receipt(job_id)["id"]
            except ValidationError as e:
                show_validation(e)
        new_id = st.session_state.get("adm_rc_new")
        if new_id and (r := svc.get_receipt(new_id)):
            st.success(f"Receipt {r['receipt_no']} generated for {r['client_name']}.")
            receipt_download(r, key=f"adm_rc_dl_new_{new_id}")

search = st.text_input("Search receipts", placeholder="Receipt number, client or registration",
                       key="adm_rc_search")
receipts = svc.list_receipts(search)
if not receipts:
    empty_state("No receipts found." if search else "No receipts issued yet.", "fa-solid fa-receipt")
    st.stop()

df = pd.DataFrame(receipts)
table = pd.DataFrame({
    "Receipt No.": df["receipt_no"],
    "Issued": df["issued_at"].map(fmt_date),
    "Client": df["client_name"],
    "Service": df["service"],
    "Total": df["total_amount"].map(lambda p: money(p / 100)),
    "Received": df["amount_received"].map(lambda p: money(p / 100)),
    "Outstanding": df["outstanding"].map(lambda p: money(p / 100)),
    "Status": df["payment_status"],
})
st.caption(f"{len(df)} receipt(s) · select one to download or print")
event = st.dataframe(table, hide_index=True, width="stretch", on_select="rerun",
                     selection_mode="single-row", key="adm_rc_table")
rows = event.selection.rows if event and event.selection else []
if rows:
    r = receipts[rows[0]]
    st.subheader(r["receipt_no"])
    kv_panel([
        ("Client", r["client_name"]), ("Vehicle", r["vehicle"]), ("Registration", r["registration"]),
        ("Service", r["service"]), ("Service date", fmt_date(r["job_date"])),
        ("Total amount", money(r["total_amount"] / 100)),
        ("Amount received", money(r["amount_received"] / 100)),
        ("Outstanding balance", money(r["outstanding"] / 100)),
        ("Payment status", r["payment_status"]), ("Issued", fmt_date(r["issued_at"])),
    ])
    receipt_download(r, key=f"adm_rc_dl_{r['id']}")
    st.caption("Open the PDF and use your viewer's Print option to print it.")
