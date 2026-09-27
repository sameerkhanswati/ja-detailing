"""Admin dashboard - business overview. Shows only real data from the database."""

import altair as alt
import pandas as pd
import streamlit as st

import services as svc
from utils import page_file
from models import MONTHS
from ui import MONEY_COL, admin_page, empty_state, money, stat_cards, style_status
from utils import today_london

admin_page("Dashboard", "A live overview of clients, jobs and revenue.")

ov = svc.overview()
today = today_london()

stat_cards([
    {"label": "Total Clients", "value": f"{ov['total_clients']:,}", "icon": "fa-solid fa-users"},
    {"label": "Total Jobs", "value": f"{ov['total_jobs']:,}", "icon": "fa-solid fa-car", "sub": "Excludes cancelled"},
    {"label": "Total Revenue", "value": money(ov["total_revenue"]), "icon": "fa-solid fa-sterling-sign",
     "sub": "Booked, in progress & completed"},
    {"label": "This Month", "value": money(ov["month_revenue"]), "icon": "fa-regular fa-calendar",
     "sub": today.strftime("%B %Y")},
    {"label": "Outstanding", "value": money(ov["outstanding"]), "icon": "fa-solid fa-hourglass-half",
     "tone": "warn" if ov["outstanding"] > 0 else ""},
    {"label": "Completed Jobs", "value": f"{ov['completed_jobs']:,}", "icon": "fa-solid fa-circle-check", "tone": "good"},
    {"label": "Pending Jobs", "value": f"{ov['pending_jobs']:,}", "icon": "fa-solid fa-clock",
     "sub": "Enquiry, booked or in progress"},
    {"label": "New Enquiries", "value": f"{ov['new_enquiries']:,}", "icon": "fa-solid fa-inbox",
     "sub": "From the website"},
])

c1, c2, c3, c4 = st.columns(4)
c1.page_link(page_file("pages/jobs.py"), label="New job", icon=":material/add_circle:")
c2.page_link(page_file("pages/clients.py"), label="New client", icon=":material/person_add:")
c3.page_link(page_file("pages/payments.py"), label="Record payment", icon=":material/payments:")
c4.page_link(page_file("pages/enquiries.py"), label=f"Enquiries ({ov['new_enquiries']} new)", icon=":material/inbox:")

st.divider()

# --- Revenue this year -------------------------------------------------------
st.subheader(f"Revenue {today.year}")
df = svc.jobs_dataframe()
monthly = svc.monthly_revenue(df, today.year)
if monthly["Revenue"].sum() == 0:
    empty_state("No revenue data available for this period.", "fa-solid fa-chart-column")
else:
    chart = (
        alt.Chart(monthly)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#E5E7EB")
        .encode(
            x=alt.X("Month:N", sort=MONTHS, axis=alt.Axis(labelAngle=0, labelExpr="slice(datum.label, 0, 3)")),
            y=alt.Y("Revenue:Q", title="Revenue (£)"),
            tooltip=["Month", alt.Tooltip("Revenue:Q", format="£,.2f"),
                     alt.Tooltip("Received:Q", format="£,.2f"), "Jobs"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, width="stretch")

left, right = st.columns(2, gap="large")

with left:
    st.subheader("Upcoming bookings")
    upcoming = [j for j in svc.list_jobs(start=today, job_statuses=["Booked", "In Progress"])]
    upcoming.sort(key=lambda j: (j["job_date"], j["id"]))
    if not upcoming:
        empty_state("No upcoming bookings.", "fa-regular fa-calendar")
    else:
        t = pd.DataFrame(upcoming[:10])
        t = t.assign(Date=pd.to_datetime(t["job_date"]).dt.strftime("%a %d %b"))
        st.dataframe(
            style_status(t[["Date", "client_name", "service", "vehicle", "job_status"]]
                         .rename(columns={"client_name": "Client", "service": "Service",
                                          "vehicle": "Vehicle", "job_status": "Status"}), ["Status"]),
            hide_index=True, width="stretch",
        )

with right:
    st.subheader("Outstanding balances")
    owing = [j for j in svc.list_jobs(job_statuses=["Booked", "In Progress", "Completed"]) if j["outstanding"] > 0]
    if not owing:
        empty_state("Nothing outstanding - all recorded jobs are paid.", "fa-solid fa-circle-check")
    else:
        t = pd.DataFrame(owing[:10])
        t["Outstanding"] = t["outstanding"] / 100
        t["Job"] = t["id"].map(svc.job_code)
        st.dataframe(
            style_status(t[["Job", "client_name", "service", "Outstanding", "payment_status"]]
                         .rename(columns={"client_name": "Client", "service": "Service",
                                          "payment_status": "Payment"}), ["Payment"]),
            hide_index=True, width="stretch", column_config={"Outstanding": MONEY_COL},
        )

st.subheader("Recent jobs")
recent = svc.list_jobs()[:8]
if not recent:
    empty_state("No jobs recorded yet.", "fa-solid fa-car")
else:
    t = pd.DataFrame(recent)
    t["Job"] = t["id"].map(svc.job_code)
    t["Date"] = pd.to_datetime(t["job_date"]).dt.strftime("%d %b %Y")
    t["Total"] = t["total_amount"] / 100
    st.dataframe(
        style_status(t[["Job", "Date", "client_name", "service", "Total", "job_status", "payment_status"]]
                     .rename(columns={"client_name": "Client", "service": "Service",
                                      "job_status": "Status", "payment_status": "Payment"}),
                     ["Status", "Payment"]),
        hide_index=True, width="stretch", column_config={"Total": MONEY_COL},
    )
