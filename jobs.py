"""Job management - create jobs, auto-calculated totals, filters, edit, receipts."""

import pandas as pd
import streamlit as st

import services as svc
from utils import page_file
from models import JOB_STATUSES, PAYMENT_METHODS, PAYMENT_STATUSES, JobInput, PaymentInput, ValidationError
from ui import (
    admin_page,
    badge,
    empty_state,
    kv_panel,
    money,
    receipt_download,
    show_validation,
    style_status,
)
from utils import fmt_date, parse_date, today_london

admin_page("Jobs", "Create detailing jobs, track status and payments.")

clients = svc.client_options()
services_list = svc.list_service_names(active_only=False)


def job_editor(prefix: str, d: dict | None = None) -> tuple[JobInput | None, float, str, bool]:
    """Live job form (not st.form, so the total updates as you type).

    Returns (job_input, initial_payment, method, clicked).
    """
    d = d or {}
    ids = list(clients.keys())
    default_client = ids.index(d["client_id"]) if d.get("client_id") in ids else None
    c1, c2 = st.columns([2, 1])
    client_id = c1.selectbox("Client *", ids, index=default_client, format_func=lambda i: clients.get(i, "?"),
                             placeholder="Select a client", key=f"{prefix}_client")
    job_date = c2.date_input("Date *", parse_date(d.get("job_date")) or today_london(),
                             format="DD/MM/YYYY", key=f"{prefix}_date")

    client = svc.get_client(client_id) if client_id else None
    default_vehicle = d.get("vehicle") or (
        f"{client['vehicle_make']} {client['vehicle_model']}".strip() if client else "")
    default_reg = d.get("registration") or (client["registration"] if client else "")

    c3, c4, c5 = st.columns([2, 1, 2])
    # Keys include the client id so vehicle details refresh when the client changes.
    vehicle = c3.text_input("Vehicle", default_vehicle, max_chars=120, key=f"{prefix}_veh_{client_id}")
    reg = c4.text_input("Registration", default_reg, max_chars=12, key=f"{prefix}_reg_{client_id}")
    svc_index = services_list.index(d["service"]) if d.get("service") in services_list else None
    service = c5.selectbox("Service *", services_list, index=svc_index, placeholder="Choose a service",
                           key=f"{prefix}_service")

    c6, c7, c8, c9 = st.columns(4)
    price = c6.number_input("Service price (£) *", 0.0, 1_000_000.0, d.get("service_price", 0) / 100,
                            step=5.0, format="%.2f", key=f"{prefix}_price")
    extra = c7.number_input("Additional charges (£)", 0.0, 1_000_000.0, d.get("additional_charges", 0) / 100,
                            step=5.0, format="%.2f", key=f"{prefix}_extra")
    discount = c8.number_input("Discount (£)", 0.0, 1_000_000.0, d.get("discount", 0) / 100,
                               step=5.0, format="%.2f", key=f"{prefix}_disc")
    total = round(price + extra - discount, 2)
    c9.metric("Total amount", money(total))

    initial, method = 0.0, "Cash"
    c10, c11, c12 = st.columns(3)
    status_index = JOB_STATUSES.index(d["job_status"]) if d.get("job_status") in JOB_STATUSES else 1
    job_status = c10.selectbox("Job status", JOB_STATUSES, index=status_index, key=f"{prefix}_status")
    if not d:  # new job - allow recording a payment straight away
        initial = c11.number_input("Amount received now (£)", 0.0, 1_000_000.0, 0.0, step=5.0,
                                   format="%.2f", key=f"{prefix}_paid")
        method = c12.selectbox("Payment method", PAYMENT_METHODS, key=f"{prefix}_method")
        outstanding = total - initial
        st.caption(
            f"Outstanding after this payment: **{money(max(outstanding, 0))}**"
            + ("  ·  ⚠️ amount received is more than the total" if outstanding < 0 else "")
        )
    notes = st.text_area("Notes", d.get("notes", ""), max_chars=2000, height=80, key=f"{prefix}_notes")
    clicked = st.button("Create job" if not d else "Save changes", type="primary", key=f"{prefix}_save",
                        icon=":material/save:")
    if not clicked:
        return None, 0.0, method, False
    job = JobInput(client_id=client_id or 0, job_date=job_date, service=service or "", service_price=price,
                   vehicle=vehicle, registration=reg, additional_charges=extra, discount=discount,
                   job_status=job_status, notes=notes)
    return job, initial, method, True


tab_list, tab_new = st.tabs(["All jobs", "New job"])

# ---------------------------------------------------------------------------
# New job
# ---------------------------------------------------------------------------
with tab_new:
    if not clients:
        empty_state("Add a client first - jobs are linked to a client.", "fa-solid fa-user-plus")
        st.page_link(page_file("pages/clients.py"), label="Go to Clients", icon=":material/group:")
    else:
        job, initial, method, clicked = job_editor("adm_newjob")
        if clicked:
            try:
                jid = svc.create_job(job, initial, method)
                st.session_state["adm_last_job"] = jid
                for k in [k for k in st.session_state if k.startswith("adm_newjob")]:
                    del st.session_state[k]
                st.rerun()
            except ValidationError as e:
                show_validation(e)

        last = st.session_state.get("adm_last_job")
        if last and (j := svc.get_job(last)):
            st.success(f"Job **{svc.job_code(last)}** created for {j['client_name']} - "
                       f"total {money(j['total_amount'] / 100)}, outstanding {money(j['outstanding'] / 100)}.")
            if st.button("Generate Receipt", icon=":material/receipt_long:", key="adm_newjob_receipt"):
                try:
                    st.session_state["adm_last_receipt"] = svc.generate_receipt(last)["id"]
                except ValidationError as e:
                    show_validation(e)
            rid = st.session_state.get("adm_last_receipt")
            if rid and (r := svc.get_receipt(rid)) and r["job_id"] == last:
                receipt_download(r, key=f"adm_dl_new_{rid}")

# ---------------------------------------------------------------------------
# Job list + filters
# ---------------------------------------------------------------------------
with tab_list:
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        start = f1.date_input("From", value=None, format="DD/MM/YYYY", key="adm_jobs_from")
        end = f2.date_input("To", value=None, format="DD/MM/YYYY", key="adm_jobs_to")
        client_filter = f3.selectbox("Client", list(clients.keys()), index=None,
                                     format_func=lambda i: clients.get(i, "?"), placeholder="All clients",
                                     key="adm_jobs_client")
        search = f4.text_input("Search", placeholder="Vehicle or registration", key="adm_jobs_search")
        f5, f6, f7 = st.columns(3)
        svc_filter = f5.multiselect("Service", services_list, placeholder="All services", key="adm_jobs_svc")
        status_filter = f6.multiselect("Job status", JOB_STATUSES, placeholder="All statuses", key="adm_jobs_st")
        pay_filter = f7.multiselect("Payment status", PAYMENT_STATUSES, placeholder="All", key="adm_jobs_pay")

    if start and end and start > end:
        st.warning("'From' date is after 'To' date.")
    jobs = svc.list_jobs(start=start, end=end, client_id=client_filter, services=svc_filter,
                         job_statuses=status_filter, payment_statuses=pay_filter, search=search)
    if not jobs:
        empty_state("No jobs recorded yet." if not any([start, end, client_filter, search, svc_filter,
                                                        status_filter, pay_filter])
                    else "No jobs match these filters.", "fa-solid fa-car")
        st.stop()

    df = pd.DataFrame(jobs)
    table = pd.DataFrame({
        "Job ID": df["id"].map(svc.job_code),
        "Date": df["job_date"].map(fmt_date),
        "Client": df["client_name"],
        "Vehicle": df["vehicle"],
        "Reg": df["registration"],
        "Service": df["service"],
        "Total": df["total_amount"] / 100,
        "Received": df["amount_received"] / 100,
        "Outstanding": df["outstanding"] / 100,
        "Status": df["job_status"],
        "Payment": df["payment_status"],
    })
    active = df[df["job_status"] != "Cancelled"]
    st.caption(
        f"{len(df)} job(s) · total {money(active['total_amount'].sum() / 100)} · "
        f"outstanding {money(active['outstanding'].sum() / 100)} (cancelled jobs excluded) · select a row to manage"
    )
    event = st.dataframe(style_status(table, ["Status", "Payment"]), hide_index=True, width="stretch",
                         on_select="rerun", selection_mode="single-row", key="adm_jobs_table")
    rows = event.selection.rows if event and event.selection else []
    if not rows:
        st.stop()

    job = svc.get_job(int(df.iloc[rows[0]]["id"]))
    if not job:
        st.warning("That job no longer exists.")
        st.stop()

    st.divider()
    st.subheader(f"{svc.job_code(job['id'])} · {job['client_name']}")
    kv_panel([
        ("Client", f"{job['client_name']} ({svc.client_code(job['client_id'])})"),
        ("Date", fmt_date(job["job_date"])),
        ("Vehicle", job["vehicle"] or "—"),
        ("Registration", job["registration"] or "—"),
        ("Service", job["service"]),
        ("Service price", money(job["service_price"] / 100)),
        ("Additional charges", money(job["additional_charges"] / 100)),
        ("Discount", money(job["discount"] / 100)),
        ("Total amount", money(job["total_amount"] / 100)),
        ("Amount received", money(job["amount_received"] / 100)),
        ("Amount outstanding", money(job["outstanding"] / 100)),
        ("Job status", badge(job["job_status"])),
        ("Payment status", badge(job["payment_status"])),
        ("Notes", job["notes"] or "—"),
    ])

    t_pay, t_receipt, t_edit, t_del = st.tabs(["Record payment", "Receipts", "Edit job", "Delete"])

    with t_pay:
        if job["outstanding"] <= 0:
            st.info("This job is fully paid.")
        else:
            with st.form(f"adm_pay_{job['id']}", border=False):
                p1, p2, p3 = st.columns(3)
                amount = p1.number_input("Amount (£)", 0.0, job["outstanding"] / 100, job["outstanding"] / 100,
                                         step=5.0, format="%.2f")
                paid_at = p2.date_input("Payment date", today_london(), format="DD/MM/YYYY")
                method = p3.selectbox("Method", PAYMENT_METHODS)
                ref = st.text_input("Reference (optional)", max_chars=80)
                if st.form_submit_button("Record payment", type="primary"):
                    try:
                        svc.add_payment(PaymentInput(job_id=job["id"], amount=amount, paid_at=paid_at,
                                                     method=method, reference=ref))
                        st.toast("Payment recorded", icon="✅")
                        st.rerun()
                    except ValidationError as e:
                        show_validation(e)

    with t_receipt:
        if st.button("Generate Receipt", icon=":material/receipt_long:", key=f"adm_gen_{job['id']}",
                     disabled=job["job_status"] == "Cancelled"):
            try:
                svc.generate_receipt(job["id"])
                st.toast("Receipt generated", icon="🧾")
            except ValidationError as e:
                show_validation(e)
        existing = svc.receipts_for_job(job["id"])
        if not existing:
            st.caption("No receipts issued for this job yet.")
        for r in existing:
            st.markdown(f"**{r['receipt_no']}** · issued {fmt_date(r['issued_at'])} · "
                        f"received {money(r['amount_received'] / 100)} · {r['payment_status']}")
            receipt_download(r, key=f"adm_dl_{r['id']}")

    with t_edit:
        upd, _, _, clicked = job_editor(f"adm_edit_{job['id']}", job)
        if clicked:
            try:
                svc.update_job(job["id"], upd)
                st.toast("Job updated", icon="✅")
                st.rerun()
            except ValidationError as e:
                show_validation(e)

    with t_del:
        st.warning("Deleting a job also deletes its payments. Issued receipts are kept for your records.")
        ok = st.checkbox("I understand - delete this job", key=f"adm_deljob_{job['id']}")
        if st.button("Delete job", type="primary", disabled=not ok, icon=":material/delete:",
                     key=f"adm_deljob_btn_{job['id']}"):
            svc.delete_job(job["id"])
            st.toast("Job deleted", icon="🗑️")
            st.rerun()
