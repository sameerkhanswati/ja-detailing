"""
Reusable UI building blocks for the admin system (cards, badges, headers,
empty states). Every admin page starts with ``admin_page(...)`` which also
enforces authentication.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import require_admin
from models import ValidationError
from styles import ADMIN_CSS
from utils import esc, gbp


# Admin menu shown at the top of every admin page (works on desktop and phones,
# so the admin never depends on the collapsible sidebar).
ADMIN_MENU = [
    ("Dashboard", "pages/dashboard.py"),
    ("Enquiries", "pages/enquiries.py"),
    ("Clients", "pages/clients.py"),
    ("Jobs", "pages/jobs.py"),
    ("Payments", "pages/payments.py"),
    ("Receipts", "pages/receipts.py"),
    ("Reports", "pages/reports.py"),
    ("Settings", "pages/settings.py"),
    ("Website", "public/home.py"),
    ("Logout", None),
]


def admin_menu(current: str) -> None:
    from auth import logout
    from utils import page_file

    labels = [label for label, _ in ADMIN_MENU]
    choice = st.segmented_control(
        "Admin menu", labels, default=current if current in labels else None,
        key=f"adm_menu_{current}", label_visibility="collapsed",
    )
    if choice and choice != current:
        target = dict(ADMIN_MENU)[choice]
        if target is None:  # Logout
            logout()
            st.switch_page(page_file("public/home.py"))
        st.switch_page(page_file(target))


def admin_page(title: str, subtitle: str = "", kicker: str = "JA Detailing · Admin") -> None:
    """Auth guard + styles + menu + page header. Call first on every admin page."""
    require_admin()
    st.html(f"<style>{ADMIN_CSS}</style>")
    admin_menu(title)
    st.html(f"""
    <div class="adm-head">
      <div><div class="adm-kicker">{esc(kicker)}</div><h1>{esc(title)}</h1>
      {f'<p>{esc(subtitle)}</p>' if subtitle else ''}</div>
    </div>""")


def stat_cards(items: list[dict]) -> None:
    """items: {label, value, icon?, sub?, tone? ('good'|'warn')}"""
    cards = []
    for it in items:
        icon = f'<i class="{it["icon"]}" aria-hidden="true"></i>' if it.get("icon") else ""
        sub = f'<div class="sub">{esc(it["sub"])}</div>' if it.get("sub") else ""
        cards.append(
            f'<div class="stat {it.get("tone", "")}"><div class="lbl">{icon}{esc(it["label"])}</div>'
            f'<div class="val">{esc(it["value"])}</div>{sub}</div>'
        )
    st.html(f'<div class="stat-grid">{"".join(cards)}</div>')


def money(pounds: float) -> str:
    return gbp(pounds, pence=False)


class HTML(str):
    """Marks a string as trusted, already-escaped HTML for kv_panel."""


def badge(status: str) -> HTML:
    cls = "b-" + (status or "").lower().replace(" ", "-")
    return HTML(f'<span class="badge {cls}">{esc(status)}</span>')


def empty_state(message: str, icon: str = "fa-regular fa-folder-open") -> None:
    st.html(f'<div class="empty"><i class="{icon}" aria-hidden="true"></i>{esc(message)}</div>')


def show_validation(err: ValidationError) -> None:
    st.error("\n".join(f"- {m}" for m in err.errors))


def kv_panel(rows: list[tuple[str, str]]) -> None:
    """Label/value panel. Values are HTML-escaped unless wrapped in ``HTML``."""
    cells = "".join(
        f"<span>{esc(k)}</span><b>{v if isinstance(v, HTML) else esc(v or '—')}</b>" for k, v in rows
    )
    st.html(f'<div class="panel"><div class="kv">{cells}</div></div>')


STATUS_COLOURS = {
    "Paid": "#4ADE80", "Completed": "#4ADE80", "Converted": "#4ADE80",
    "Partially Paid": "#FBBF24", "In Progress": "#FBBF24", "Contacted": "#FBBF24",
    "Unpaid": "#F87171", "Cancelled": "#F87171",
    "Booked": "#60A5FA", "New": "#60A5FA",
    "Enquiry": "#CBD5E1", "Closed": "#94A3B8",
}


def style_status(df: pd.DataFrame, columns: list[str]):
    """Colour-code status columns in a dataframe (acts as status badges)."""
    def colour(v):
        c = STATUS_COLOURS.get(v)
        return f"color: {c}; font-weight: 600;" if c else ""

    cols = [c for c in columns if c in df.columns]
    styler = df.style.map(colour, subset=cols) if cols else df.style
    # Styler display values override column_config formats, so format money here.
    # (In admin tables every float column is a £ amount.)
    money_cols = [c for c in df.columns if pd.api.types.is_float_dtype(df[c])]
    if money_cols:
        styler = styler.format({c: "£{:,.2f}" for c in money_cols})
    return styler


MONEY_COL = st.column_config.NumberColumn(format="£%.2f")


def receipt_download(receipt: dict, key: str) -> None:
    """Download button for a receipt PDF (print from any PDF viewer)."""
    from receipt_pdf import build_receipt_pdf
    import services as svc

    try:
        pdf = build_receipt_pdf(receipt, svc.get_setting("receipt_footer", ""))
    except Exception:
        st.error("The receipt PDF couldn't be created. Please try again.")
        return
    st.download_button(
        f"Download receipt {receipt['receipt_no']} (PDF)",
        data=pdf,
        file_name=f"{receipt['receipt_no']}.pdf",
        mime="application/pdf",
        icon=":material/download:",
        key=key,
        type="primary",
    )
