"""Client management - add, search, view, edit, delete, history."""

import pandas as pd
import streamlit as st

import services as svc
from models import ClientInput, ValidationError
from ui import MONEY_COL, admin_page, empty_state, kv_panel, money, show_validation, style_status
from utils import fmt_date, phone_to_whatsapp, whatsapp_link

admin_page("Clients", "Customer records, vehicles and service history.")


def client_form(key: str, d: dict | None = None) -> ClientInput | None:
    """Render the client form; returns ClientInput when submitted."""
    d = d or {}
    with st.form(key, border=True, clear_on_submit=(d == {})):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Client name *", d.get("name", ""), max_chars=120)
        phone = c2.text_input("Phone", d.get("phone", ""), max_chars=30, placeholder="07123 456789")
        whatsapp = c3.text_input("WhatsApp", d.get("whatsapp", ""), max_chars=30,
                                 help="Leave blank if same as phone")
        c4, c5, c6 = st.columns(3)
        email = c4.text_input("Email", d.get("email", ""), max_chars=160)
        make = c5.text_input("Vehicle make", d.get("vehicle_make", ""), max_chars=60)
        model = c6.text_input("Vehicle model", d.get("vehicle_model", ""), max_chars=60)
        c7, c8 = st.columns([1, 2])
        reg = c7.text_input("Registration number", d.get("registration", ""), max_chars=12)
        area = c8.text_input("Address / area", d.get("area", ""), max_chars=120)
        notes = st.text_area("Notes", d.get("notes", ""), max_chars=2000, height=90)
        submitted = st.form_submit_button("Save client", type="primary")
    if submitted:
        return ClientInput(name=name, phone=phone, whatsapp=whatsapp or phone, email=email,
                           vehicle_make=make, vehicle_model=model, registration=reg, area=area, notes=notes)
    return None


tab_list, tab_add = st.tabs(["All clients", "Add client"])

with tab_add:
    new = client_form("add_client")
    if new:
        try:
            cid = svc.create_client(new)
            st.toast(f"Client {svc.client_code(cid)} added", icon="✅")
            st.success(f"Client **{new.name}** saved as {svc.client_code(cid)}.")
        except ValidationError as e:
            show_validation(e)

with tab_list:
    search = st.text_input("Search clients", placeholder="Name, phone, vehicle or registration…",
                           label_visibility="collapsed", key="adm_client_search")
    clients = svc.list_clients(search)
    if not clients:
        empty_state("No clients match your search." if search else "No clients yet - add your first client.",
                    "fa-solid fa-users")
        st.stop()

    df = pd.DataFrame(clients)
    table = pd.DataFrame({
        "Client ID": df["id"].map(svc.client_code),
        "Name": df["name"],
        "Phone": df["phone"],
        "Vehicle": (df["vehicle_make"] + " " + df["vehicle_model"]).str.strip(),
        "Registration": df["registration"],
        "Area": df["area"],
        "Jobs": df["job_count"],
        "Last job": df["last_job"].map(lambda v: fmt_date(v) if v else "—"),
        "Added": df["created_at"].map(fmt_date),
    })
    st.caption(f"{len(table)} client(s) · select a row to view, edit or delete")
    event = st.dataframe(table, hide_index=True, width="stretch", on_select="rerun",
                         selection_mode="single-row", key="adm_clients_table")
    rows = event.selection.rows if event and event.selection else []
    if not rows:
        st.stop()

    client = svc.get_client(int(df.iloc[rows[0]]["id"]))
    if not client:
        st.warning("That client no longer exists.")
        st.stop()

    st.divider()
    st.subheader(f"{client['name']}  ·  {svc.client_code(client['id'])}")
    history = svc.client_history(client["id"])
    spent = sum(j["total_amount"] for j in history if j["job_status"] != "Cancelled") / 100
    owing = sum(j["outstanding"] for j in history if j["job_status"] != "Cancelled") / 100

    info, actions = st.columns([3, 1], gap="large")
    with info:
        kv_panel([
            ("Phone", client["phone"]), ("WhatsApp", client["whatsapp"]), ("Email", client["email"]),
            ("Vehicle", f"{client['vehicle_make']} {client['vehicle_model']}".strip()),
            ("Registration", client["registration"]), ("Address / area", client["area"]),
            ("Date added", fmt_date(client["created_at"])), ("Notes", client["notes"]),
        ])
    with actions:
        st.metric("Jobs", len(history))
        st.metric("Total value", money(spent))
        st.metric("Outstanding", money(owing))
        wa = phone_to_whatsapp(client["whatsapp"] or client["phone"])
        if wa:
            st.link_button("WhatsApp client", whatsapp_link(f"Hi {client['name']}, ", wa),
                           icon=":material/chat:", width="stretch")

    tab_hist, tab_edit, tab_del = st.tabs(["Service history", "Edit", "Delete"])
    with tab_hist:
        if not history:
            empty_state("No jobs recorded for this client yet.", "fa-solid fa-car")
        else:
            h = pd.DataFrame(history)
            st.dataframe(
                style_status(pd.DataFrame({
                    "Job": h["id"].map(svc.job_code),
                    "Date": h["job_date"].map(fmt_date),
                    "Service": h["service"],
                    "Vehicle": h["vehicle"],
                    "Total": h["total_amount"] / 100,
                    "Received": h["amount_received"] / 100,
                    "Outstanding": h["outstanding"] / 100,
                    "Status": h["job_status"],
                    "Payment": h["payment_status"],
                }), ["Status", "Payment"]),
                hide_index=True, width="stretch",
                column_config={"Total": MONEY_COL, "Received": MONEY_COL, "Outstanding": MONEY_COL},
            )
    with tab_edit:
        upd = client_form(f"edit_client_{client['id']}", client)
        if upd:
            try:
                svc.update_client(client["id"], upd)
                st.toast("Client updated", icon="✅")
                st.rerun()
            except ValidationError as e:
                show_validation(e)
    with tab_del:
        st.warning(
            f"Deleting **{client['name']}** also permanently deletes their {len(history)} job(s) and payments. "
            "Issued receipts are kept for your records."
        )
        confirm = st.checkbox("I understand - delete this client", key=f"adm_del_client_{client['id']}")
        if st.button("Delete client", type="primary", disabled=not confirm, icon=":material/delete:"):
            svc.delete_client(client["id"])
            st.toast("Client deleted", icon="🗑️")
            st.rerun()
