"""Website enquiries - review quote requests and convert them to clients/jobs."""

import pandas as pd
import streamlit as st

import services as svc
from config import BUSINESS
from models import ENQUIRY_STATUSES, ValidationError
from ui import admin_page, badge, empty_state, kv_panel, show_validation, style_status
from utils import fmt_date, phone_to_whatsapp, whatsapp_link

admin_page("Enquiries", "Quote requests submitted through the website.")

status_filter = st.segmented_control("Status", ["All"] + ENQUIRY_STATUSES, default="New",
                                     key="adm_enq_status")
enquiries = svc.list_enquiries(None if status_filter in (None, "All") else [status_filter])
if not enquiries:
    empty_state("No enquiries here yet. New quote requests from the website will appear here.",
                "fa-solid fa-inbox")
    st.stop()

df = pd.DataFrame(enquiries)
table = pd.DataFrame({
    "Ref": df["id"].map(svc.enquiry_code),
    "Received": df["created_at"].map(fmt_date),
    "Name": df["name"],
    "Phone": df["phone"],
    "Vehicle": (df["vehicle_make"] + " " + df["vehicle_model"]).str.strip(),
    "Service": df["service"],
    "Preferred": df["preferred_date"].map(fmt_date) + " · " + df["preferred_time"],
    "Status": df["status"],
})
event = st.dataframe(style_status(table, ["Status"]), hide_index=True, width="stretch", on_select="rerun",
                     selection_mode="single-row", key="adm_enq_table")
rows = event.selection.rows if event and event.selection else []
if not rows:
    st.caption("Select an enquiry to view, reply or convert it.")
    st.stop()

e = enquiries[rows[0]]
st.divider()
st.subheader(f"{svc.enquiry_code(e['id'])} · {e['name']}")
left, right = st.columns([3, 1], gap="large")
with left:
    kv_panel([
        ("Name", e["name"]), ("Phone", e["phone"]), ("Email", e["email"]),
        ("Vehicle", f"{e['vehicle_make']} {e['vehicle_model']}".strip()),
        ("Registration", e["registration"]), ("Service", e["service"]),
        ("Preferred date", fmt_date(e["preferred_date"])), ("Preferred time", e["preferred_time"]),
        ("Notes", e["notes"]), ("Received", fmt_date(e["created_at"])), ("Status", badge(e["status"])),
    ])
with right:
    wa = phone_to_whatsapp(e["phone"])
    if wa:
        msg = (f"Hi {e['name']}, thanks for your enquiry with {BUSINESS['name']} about "
               f"{e['service']} for your {e['vehicle_make']} {e['vehicle_model']}. ")
        st.link_button("Reply on WhatsApp", whatsapp_link(msg, wa), icon=":material/chat:", width="stretch")
    new_status = st.selectbox("Update status", ENQUIRY_STATUSES, index=ENQUIRY_STATUSES.index(e["status"]),
                              key=f"adm_enq_st_{e['id']}")
    if new_status != e["status"]:
        svc.update_enquiry_status(e["id"], new_status)
        st.toast("Status updated", icon="✅")
        st.rerun()
    if e["status"] != "Converted":
        if st.button("Convert to client + job", type="primary", width="stretch", icon=":material/person_add:",
                     help="Creates a client record and a job with status 'Enquiry' (price to be added)."):
            try:
                cid, jid = svc.convert_enquiry(e["id"])
                st.success(f"Created {svc.client_code(cid)} and {svc.job_code(jid)}. "
                           "Open Jobs to add the price and confirm the booking.")
            except ValidationError as err:
                show_validation(err)
    with st.popover("Delete", icon=":material/delete:", width="stretch"):
        st.write("Permanently delete this enquiry?")
        if st.button("Yes, delete", type="primary", key=f"adm_enq_del_{e['id']}"):
            svc.delete_enquiry(e["id"])
            st.rerun()
