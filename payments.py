"""Payments - record payments against jobs and review payment history."""

import pandas as pd
import streamlit as st

import services as svc
from models import PAYMENT_METHODS, PaymentInput, ValidationError
from ui import MONEY_COL, admin_page, empty_state, money, receipt_download, show_validation, stat_cards
from utils import fmt_date, today_london

admin_page("Payments", "Record payments and keep balances up to date.")

tab_record, tab_history = st.tabs(["Record payment", "Payment history"])

with tab_record:
    options = svc.job_options(only_outstanding=True)
    if not options:
        empty_state("No jobs with an outstanding balance.", "fa-solid fa-circle-check")
    else:
        job_id = st.selectbox("Job *", list(options.keys()), index=None, format_func=options.get,
                              placeholder="Select a job with a balance due", key="adm_pay_job")
        job = svc.get_job(job_id) if job_id else None
        if job:
            stat_cards([
                {"label": "Total", "value": money(job["total_amount"] / 100)},
                {"label": "Received", "value": money(job["amount_received"] / 100), "tone": "good"},
                {"label": "Outstanding", "value": money(job["outstanding"] / 100), "tone": "warn"},
                {"label": "Payment status", "value": job["payment_status"]},
            ])
            with st.form(f"adm_payform_{job_id}", border=True):
                c1, c2, c3 = st.columns(3)
                amount = c1.number_input("Amount (£) *", 0.0, job["outstanding"] / 100, job["outstanding"] / 100,
                                         step=5.0, format="%.2f")
                paid_at = c2.date_input("Payment date *", today_london(), format="DD/MM/YYYY")
                method = c3.selectbox("Method", PAYMENT_METHODS)
                ref = st.text_input("Reference (optional)", max_chars=80)
                notes = st.text_input("Notes (optional)", max_chars=500)
                also_receipt = st.checkbox("Generate a receipt after recording", value=True)
                submitted = st.form_submit_button("Record payment", type="primary")
            if submitted:
                try:
                    svc.add_payment(PaymentInput(job_id=job_id, amount=amount, paid_at=paid_at,
                                                 method=method, reference=ref, notes=notes))
                    st.session_state["adm_pay_done"] = job_id
                    if also_receipt:
                        st.session_state["adm_pay_receipt"] = svc.generate_receipt(job_id)["id"]
                    st.session_state.pop("adm_pay_job", None)
                    st.rerun()
                except ValidationError as e:
                    show_validation(e)

    done = st.session_state.get("adm_pay_done")
    if done and (j := svc.get_job(done)):
        st.success(f"Payment recorded for {svc.job_code(done)} ({j['client_name']}). "
                   f"Outstanding now {money(j['outstanding'] / 100)} - {j['payment_status']}.")
        rid = st.session_state.get("adm_pay_receipt")
        if rid and (r := svc.get_receipt(rid)):
            receipt_download(r, key=f"adm_pay_dl_{rid}")

with tab_history:
    c1, c2 = st.columns(2)
    start = c1.date_input("From", value=None, format="DD/MM/YYYY", key="adm_payh_from")
    end = c2.date_input("To", value=None, format="DD/MM/YYYY", key="adm_payh_to")
    payments = svc.list_payments(start, end)
    if not payments:
        empty_state("No payments recorded for this period.", "fa-solid fa-sterling-sign")
        st.stop()
    df = pd.DataFrame(payments)
    st.metric("Total received in period", money(df["amount"].sum() / 100))
    table = pd.DataFrame({
        "Date": df["paid_at"].map(fmt_date),
        "Job": df["job_id"].map(svc.job_code),
        "Client": df["client_name"],
        "Service": df["service"],
        "Amount": df["amount"] / 100,
        "Method": df["method"],
        "Reference": df["reference"],
        "Notes": df["notes"],
    })
    event = st.dataframe(table, hide_index=True, width="stretch", column_config={"Amount": MONEY_COL},
                         on_select="rerun", selection_mode="single-row", key="adm_pay_table")
    rows = event.selection.rows if event and event.selection else []
    if rows:
        p = payments[rows[0]]
        st.warning(f"Delete the {money(p['amount'] / 100)} payment from {fmt_date(p['paid_at'])} "
                   f"({p['client_name']})? The job balance will be recalculated. Receipts already issued are not changed.")
        ok = st.checkbox("Yes, delete this payment", key=f"adm_delpay_{p['id']}")
        if st.button("Delete payment", type="primary", disabled=not ok, icon=":material/delete:"):
            svc.delete_payment(p["id"])
            st.toast("Payment deleted", icon="🗑️")
            st.rerun()
