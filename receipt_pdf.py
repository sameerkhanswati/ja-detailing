"""
PDF receipt generation (ReportLab).

Receipts show only facts held in the database. No VAT/tax details are
printed because none have been supplied by the business.
"""

from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from config import BUSINESS, LOGO_PATH
from utils import fmt_date, gbp

INK = colors.HexColor("#111214")
MUTED = colors.HexColor("#6B7280")
LINE = colors.HexColor("#E5E7EB")
PANEL = colors.HexColor("#F5F6F7")
STATUS_COLOURS = {
    "Paid": colors.HexColor("#15803D"),
    "Partially Paid": colors.HexColor("#B45309"),
    "Unpaid": colors.HexColor("#B91C1C"),
}


def _draw_logo(c: canvas.Canvas, x: float, y_top: float, max_w: float, max_h: float) -> float:
    """Draw the logo keeping its aspect ratio. Returns height used (0 if missing)."""
    path = Path(LOGO_PATH)
    if not path.is_file():
        return 0
    try:
        img = ImageReader(str(path))
        iw, ih = img.getSize()
        scale = min(max_w / iw, max_h / ih)
        w, h = iw * scale, ih * scale
        c.drawImage(img, x, y_top - h, width=w, height=h, mask="auto")
        return h
    except Exception:
        return 0


def build_receipt_pdf(r: dict, footer: str = "") -> bytes:
    buf = io.BytesIO()
    W, H = A5
    c = canvas.Canvas(buf, pagesize=A5)
    c.setTitle(f"Receipt {r['receipt_no']} - {BUSINESS['name']}")
    c.setAuthor(BUSINESS["name"])
    margin = 14 * mm
    y = H - margin

    # --- Header -----------------------------------------------------------
    logo_h = _draw_logo(c, margin, y, 38 * mm, 22 * mm)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawRightString(W - margin, y - 6 * mm, "RECEIPT")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawRightString(W - margin, y - 11 * mm, f"No. {r['receipt_no']}")
    c.drawRightString(W - margin, y - 15 * mm, f"Issued {fmt_date(r['issued_at'])}")

    y -= max(logo_h, 17 * mm) + 5 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(margin, y, BUSINESS["name"])
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawString(margin, y - 4.6 * mm, BUSINESS["area"])
    c.drawString(margin, y - 8.8 * mm, f"WhatsApp {BUSINESS['whatsapp_display']}  ·  {BUSINESS['instagram_handle']}")

    y -= 14 * mm
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(margin, y, W - margin, y)

    # --- Details ------------------------------------------------------------
    y -= 8 * mm
    rows = [
        ("Client", r["client_name"]),
        ("Vehicle", r.get("vehicle") or "—"),
        ("Registration", r.get("registration") or "—"),
        ("Service", r["service"]),
        ("Service date", fmt_date(r["job_date"])),
    ]
    for label, value in rows:
        c.setFont("Helvetica", 8.5)
        c.setFillColor(MUTED)
        c.drawString(margin, y, label.upper())
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(INK)
        c.drawString(margin + 34 * mm, y, str(value)[:48])
        y -= 7 * mm

    # --- Amounts panel -------------------------------------------------------
    y -= 3 * mm
    panel_h = 32 * mm
    c.setFillColor(PANEL)
    c.roundRect(margin, y - panel_h, W - 2 * margin, panel_h, 3 * mm, stroke=0, fill=1)
    py = y - 8 * mm
    amounts = [
        ("Total amount", gbp(r["total_amount"]), False),
        ("Amount received", gbp(r["amount_received"]), False),
        ("Outstanding balance", gbp(r["outstanding"]), True),
    ]
    for label, value, bold in amounts:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10 if bold else 9.5)
        c.setFillColor(INK)
        c.drawString(margin + 5 * mm, py, label)
        c.drawRightString(W - margin - 5 * mm, py, value)
        py -= 8 * mm

    y -= panel_h + 9 * mm

    # --- Status badge -----------------------------------------------------------
    status = r["payment_status"]
    col = STATUS_COLOURS.get(status, INK)
    c.setFont("Helvetica-Bold", 9)
    label = f"PAYMENT STATUS: {status.upper()}"
    tw = c.stringWidth(label, "Helvetica-Bold", 9) + 10 * mm
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(1.2)
    c.roundRect(margin, y - 3 * mm, tw, 8.5 * mm, 2 * mm, stroke=1, fill=0)
    c.drawString(margin + 5 * mm, y, label)

    # --- Footer --------------------------------------------------------------
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    if footer:
        c.drawCentredString(W / 2, margin + 8 * mm, footer[:110])
    c.setFont("Helvetica", 7)
    c.drawCentredString(
        W / 2, margin + 3 * mm,
        f"{BUSINESS['name']}  ·  {BUSINESS['hours_open']}, {BUSINESS['hours_closed'].lower()}",
    )

    c.showPage()
    c.save()
    return buf.getvalue()
