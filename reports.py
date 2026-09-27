"""Revenue reports - monthly dashboard, filters and revenue by service.

Revenue = total value of jobs with status Booked, In Progress or Completed
(Enquiry and Cancelled jobs are excluded). Jobs are counted in the month of
their job date. Only real data from the database is shown.
"""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

import services as svc
from models import MONTHS, PAYMENT_STATUSES, ReportFilters
from ui import MONEY_COL, admin_page, empty_state, money, stat_cards, style_status
from utils import today_london

admin_page("Reports", "Monthly revenue, balances and service performance.")

today = today_london()
services_list = svc.list_service_names(active_only=False)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
with st.container(border=True):
    f1, f2, f3, f4 = st.columns(4)
    year = f1.selectbox("Year", svc.available_years(), key="adm_rep_year")
    month_label = f2.selectbox("Month", ["All months"] + MONTHS, key="adm_rep_month")
    sel_services = f3.multiselect("Service", services_list, placeholder="All services", key="adm_rep_svc")
    sel_pay = f4.multiselect("Payment status", PAYMENT_STATUSES, placeholder="All", key="adm_rep_pay")
    use_range = st.toggle("Use a custom date range instead", key="adm_rep_range_on")
    if use_range:
        r1, r2 = st.columns(2)
        start = r1.date_input("From", date(year, 1, 1), format="DD/MM/YYYY", key="adm_rep_from")
        end = r2.date_input("To", today, format="DD/MM/YYYY", key="adm_rep_to")
        if start > end:
            st.warning("'From' date is after 'To' date.")
            st.stop()
        period_label = f"{start:%d %b %Y} – {end:%d %b %Y}"
    elif month_label != "All months":
        m = MONTHS.index(month_label) + 1
        start = date(year, m, 1)
        end = (date(year + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
        period_label = f"{month_label} {year}"
    else:
        start, end = date(year, 1, 1), date(year, 12, 31)
        period_label = str(year)

base_filters = ReportFilters(services=sel_services, payment_statuses=sel_pay)
all_df = svc.jobs_dataframe(base_filters)          # filters except date (for month comparisons + chart)
period_df = svc.jobs_dataframe(ReportFilters(start=start, end=end, services=sel_services,
                                             payment_statuses=sel_pay))

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
def month_revenue(df: pd.DataFrame, y: int, m: int) -> float:
    rev = svc.revenue_jobs(df)
    if rev.empty:
        return 0.0
    return float(rev[(rev["job_date"].dt.year == y) & (rev["job_date"].dt.month == m)]["total_amount"].sum())


prev_y, prev_m = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
cur_rev = month_revenue(all_df, today.year, today.month)
prev_rev = month_revenue(all_df, prev_y, prev_m)
total_all = svc.period_summary(all_df)
period = svc.period_summary(period_df)

change = ""
if prev_rev > 0:
    pct = (cur_rev - prev_rev) / prev_rev * 100
    change = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.0f}% vs last month"

st.markdown("##### All time")
stat_cards([
    {"label": "Current month", "value": money(cur_rev), "icon": "fa-regular fa-calendar", "sub": change or today.strftime("%B %Y")},
    {"label": "Previous month", "value": money(prev_rev), "icon": "fa-regular fa-calendar-minus",
     "sub": date(prev_y, prev_m, 1).strftime("%B %Y")},
    {"label": "Total revenue", "value": money(total_all["revenue"]), "icon": "fa-solid fa-sterling-sign"},
    {"label": "Outstanding", "value": money(total_all["outstanding"]), "icon": "fa-solid fa-hourglass-half",
     "tone": "warn" if total_all["outstanding"] else ""},
])
st.markdown(f"##### Selected period · {period_label}")
stat_cards([
    {"label": "Revenue", "value": money(period["revenue"]), "icon": "fa-solid fa-chart-line"},
    {"label": "Amount received", "value": money(period["received"]), "icon": "fa-solid fa-wallet", "tone": "good"},
    {"label": "Outstanding", "value": money(period["outstanding"]), "icon": "fa-solid fa-hourglass-half",
     "tone": "warn" if period["outstanding"] else ""},
    {"label": "Jobs · average value", "value": f"{period['jobs']} · {money(period['average'])}",
     "icon": "fa-solid fa-car"},
])

# ---------------------------------------------------------------------------
# Monthly chart (Jan - Dec)
# ---------------------------------------------------------------------------
st.subheader(f"Monthly revenue · {year}")
monthly = svc.monthly_revenue(all_df, year)
if monthly["Revenue"].sum() == 0:
    empty_state("No revenue data available for this period.", "fa-solid fa-chart-column")
else:
    long = monthly.melt(id_vars=["Month", "month_num", "Jobs"], value_vars=["Revenue", "Received"],
                        var_name="Measure", value_name="Amount")
    chart = (
        alt.Chart(long)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Month:N", sort=MONTHS, title=None,
                    axis=alt.Axis(labelAngle=0, labelExpr="slice(datum.label, 0, 3)")),
            xOffset=alt.XOffset("Measure:N", sort=["Revenue", "Received"]),
            y=alt.Y("Amount:Q", title="£"),
            color=alt.Color("Measure:N", sort=["Revenue", "Received"],
                            scale=alt.Scale(range=["#E5E7EB", "#4ADE80"]),
                            legend=alt.Legend(orient="top", title=None)),
            tooltip=["Month", "Measure", alt.Tooltip("Amount:Q", format="£,.2f"), "Jobs"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, width="stretch")
    with st.expander("Monthly table"):
        st.dataframe(monthly.drop(columns=["month_num"]), hide_index=True, width="stretch",
                     column_config={c: MONEY_COL for c in ("Revenue", "Received", "Outstanding")})

# ---------------------------------------------------------------------------
# Revenue by service
# ---------------------------------------------------------------------------
st.subheader(f"Revenue by service · {period_label}")
breakdown = svc.service_breakdown(period_df)
if breakdown.empty:
    empty_state("No revenue data available for this period.", "fa-solid fa-list")
else:
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.dataframe(breakdown, hide_index=True, width="stretch",
                     column_config={c: MONEY_COL for c in ("Revenue", "Average Price", "Received", "Outstanding")})
    with c2:
        bars = (
            alt.Chart(breakdown)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#E5E7EB")
            .encode(
                y=alt.Y("Service:N", sort="-x", title=None),
                x=alt.X("Revenue:Q", title="£"),
                tooltip=["Service", "Jobs", alt.Tooltip("Revenue:Q", format="£,.2f"),
                         alt.Tooltip("Average Price:Q", format="£,.2f")],
            )
            .properties(height=max(160, 38 * len(breakdown)))
        )
        st.altair_chart(bars, width="stretch")

# ---------------------------------------------------------------------------
# Jobs in period + export
# ---------------------------------------------------------------------------
st.subheader("Jobs in period")
if period_df.empty:
    empty_state("No jobs recorded yet.", "fa-solid fa-car")
else:
    out = pd.DataFrame({
        "Job": period_df["id"].map(svc.job_code),
        "Date": period_df["job_date"].dt.strftime("%d %b %Y"),
        "Client": period_df["client_name"],
        "Service": period_df["service"],
        "Total": period_df["total_amount"],
        "Received": period_df["amount_received"],
        "Outstanding": period_df["outstanding"],
        "Status": period_df["job_status"],
        "Payment": period_df["payment_status"],
    })
    st.dataframe(style_status(out, ["Status", "Payment"]), hide_index=True, width="stretch")
    st.download_button("Export to CSV", out.to_csv(index=False).encode(), f"ja-jobs-{period_label}.csv",
                       "text/csv", icon=":material/download:")
