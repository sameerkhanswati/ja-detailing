"""
Shared helpers: money, dates, validation, sanitising, WhatsApp links, images.
Nothing in here imports Streamlit, so it is easy to unit test.
"""

from __future__ import annotations

import base64
import html
import io
import logging
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

from config import BUSINESS

log = logging.getLogger("ja_detailing.utils")

LONDON = ZoneInfo("Europe/London")
PROJECT_DIR = Path(__file__).resolve().parent


def page_file(rel_path: str) -> str:
    """Return 'pages/x.py' if it exists, else 'x.py' in the main folder.

    Lets the app run whether files are kept in their folders or were uploaded
    flat (e.g. via GitHub's web uploader).
    """
    if (PROJECT_DIR / rel_path).is_file():
        return rel_path
    flat = Path(rel_path).name
    return flat if (PROJECT_DIR / flat).is_file() else rel_path
MAX_MONEY = 1_000_000  # £1m sanity ceiling for any single amount


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------
def today_london() -> date:
    return datetime.now(LONDON).date()


def now_london_str() -> str:
    return datetime.now(LONDON).strftime("%Y-%m-%d %H:%M:%S")


def parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def fmt_date(value) -> str:
    d = parse_date(value)
    return d.strftime("%d %b %Y") if d else "—"


# --------------------------------------------------------------------------
# Money (stored as integer pence)
# --------------------------------------------------------------------------
def to_pence(amount) -> int:
    try:
        dec = Decimal(str(amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid amount: {amount!r}")
    return int(dec * 100)


def from_pence(pence) -> float:
    return round((int(pence or 0)) / 100, 2)


def gbp(pence_or_pounds, *, pence: bool = True) -> str:
    value = from_pence(pence_or_pounds) if pence else float(pence_or_pounds or 0)
    sign = "-" if value < 0 else ""
    return f"{sign}£{abs(value):,.2f}"


# --------------------------------------------------------------------------
# Validation & sanitising
# --------------------------------------------------------------------------
_PHONE_ALLOWED = re.compile(r"^\+?[0-9 ()\-]{7,20}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_REG = re.compile(r"^[A-Z0-9 ]{2,10}$")


def clean_text(value, max_len: int = 500) -> str:
    """Trim whitespace, drop control characters and cap the length."""
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return text.strip()[:max_len]


def esc(value) -> str:
    """HTML-escape any user-generated value before placing it in HTML."""
    return html.escape(str(value if value is not None else ""), quote=True)


def is_valid_phone(value: str) -> bool:
    value = (value or "").strip()
    if not _PHONE_ALLOWED.match(value):
        return False
    digits = re.sub(r"\D", "", value)
    return 10 <= len(digits) <= 15


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL.match((value or "").strip()))


def normalise_registration(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").upper()).strip()


def is_valid_registration(value: str) -> bool:
    value = normalise_registration(value)
    return value == "" or bool(_REG.match(value))


def validate_money(value, label: str, *, allow_zero: bool = True) -> list[str]:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return [f"{label} must be a number."]
    if amount < 0:
        return [f"{label} cannot be negative."]
    if not allow_zero and amount == 0:
        return [f"{label} must be greater than zero."]
    if amount > MAX_MONEY:
        return [f"{label} looks too large - please check it."]
    return []


def phone_to_whatsapp(value: str) -> str | None:
    """Convert a UK/international phone number to wa.me format (digits only).

    07xxx xxxxxx  -> 447xxxxxxxxx
    +44 7xxx      -> 447xxxxxxxxx
    """
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if value.strip().startswith("+"):
        pass
    elif digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = "44" + digits[1:]
    return digits if 10 <= len(digits) <= 15 else None


# --------------------------------------------------------------------------
# WhatsApp
# --------------------------------------------------------------------------
def whatsapp_link(message: str = "", number: str | None = None) -> str:
    number = number or BUSINESS["whatsapp_number"]
    url = f"https://wa.me/{number}"
    if message:
        url += "?text=" + quote(message, safe="")
    return url


def quote_whatsapp_message(e: dict) -> str:
    """Build the pre-filled WhatsApp message for a quote request."""
    vehicle = " ".join(x for x in [e.get("vehicle_make"), e.get("vehicle_model")] if x).strip()
    if e.get("registration"):
        vehicle = f"{vehicle} ({e['registration']})".strip()
    lines = [
        f"Hello {BUSINESS['name']}, I would like to request a quote.",
        "",
        f"Name: {e.get('name', '')}",
        f"Vehicle: {vehicle or '-'}",
        f"Service: {e.get('service', '')}",
        f"Preferred Date: {fmt_date(e.get('preferred_date')) if e.get('preferred_date') else '-'}",
        f"Preferred Time: {e.get('preferred_time') or '-'}",
        f"Additional Notes: {e.get('notes') or '-'}",
    ]
    if e.get("reference"):
        lines += ["", f"Enquiry ref: {e['reference']}"]
    return "\n".join(lines)


def service_whatsapp_message(service: str) -> str:
    return f"Hello {BUSINESS['name']}, I'd like a quote for {service}."


# --------------------------------------------------------------------------
# Images - local file if present, otherwise the configured demo URL.
# Missing images never crash the app.
# --------------------------------------------------------------------------
def image_to_data_uri(path: Path, max_width: int = 1400, keep_png: bool = False) -> str | None:
    """Load a local image, downscale it for the web, return a data URI.

    Returns None if the file is missing or unreadable.
    """
    try:
        path = Path(path)
        if not path.is_file():
            return None
        from PIL import Image  # Pillow is installed with Streamlit

        with Image.open(path) as img:
            img.load()
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
            buf = io.BytesIO()
            if keep_png or img.mode in ("RGBA", "LA", "P"):
                img.save(buf, format="PNG", optimize=True)
                mime = "image/png"
            else:
                img.convert("RGB").save(buf, format="JPEG", quality=80, optimize=True, progressive=True)
                mime = "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("Could not load image %s: %s", path, exc)
        return None


STATIC_IMG_DIR = Path(__file__).resolve().parent / "static"


def static_image_url(path: Path, max_width: int = 1400, keep_png: bool = False) -> str | None:
    """Resize a local image once into ./static and return its web URL.

    Served by Streamlit's static file server (enableStaticServing = true), so
    the browser downloads and caches it like a normal website image - much
    faster than embedding base64 data in the page.
    """
    try:
        src = Path(path)
        if not src.is_file():
            return None
        from PIL import Image

        ext = "png" if keep_png else "jpg"
        name = f"opt-{src.stem}-{max_width}-{int(src.stat().st_mtime)}.{ext}"
        out = STATIC_IMG_DIR / name
        if not out.is_file():
            STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)
            with Image.open(src) as img:
                img.load()
                if img.width > max_width:
                    ratio = max_width / img.width
                    img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
                if keep_png:
                    img.save(out, format="PNG", optimize=True)
                else:
                    img.convert("RGB").save(out, format="JPEG", quality=78, optimize=True, progressive=True)
        return f"app/static/{name}"
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("Could not prepare static image %s: %s", path, exc)
        return None


def _with_width(url: str, width: int) -> str:
    """Change the w= parameter of an image CDN URL (Unsplash)."""
    return re.sub(r"([?&])w=\d+", rf"\g<1>w={width}", url) if "w=" in url else url


def resolve_image(entry: dict | None, max_width: int = 1400, use_static: bool = True) -> str:
    """Return the best available src for an image config entry.

    Order: local file (static URL, or base64 if static serving is off) -> demo URL.
    """
    if not entry:
        return ""
    local = entry.get("local")
    if local and Path(local).is_file():
        uri = static_image_url(local, max_width) if use_static else None
        uri = uri or image_to_data_uri(local, max_width=max_width)
        if uri:
            return uri
    return _with_width(entry.get("url", ""), max_width)


def responsive_image(entry: dict | None, widths=(640, 1024, 1600), use_static: bool = True) -> tuple[str, str]:
    """(src, srcset) so phones download a small image and desktops a large one."""
    if not entry:
        return "", ""
    parts = []
    for w in widths:
        url = resolve_image(entry, w, use_static)
        if url.startswith("data:"):  # base64 fallback - no srcset
            return url, ""
        parts.append(f"{url} {w}w")
    return resolve_image(entry, widths[-1], use_static), ", ".join(parts)


def is_local_image(entry: dict | None) -> bool:
    return bool(entry and entry.get("local") and Path(entry["local"]).is_file())


def logo_data_uri(max_width: int = 600) -> str | None:
    from config import LOGO_PATH

    return image_to_data_uri(LOGO_PATH, max_width=max_width, keep_png=True)


def logo_url(max_width: int = 400, use_static: bool = True) -> str | None:
    """Logo as a cacheable static URL (falls back to base64)."""
    from config import LOGO_PATH

    if use_static:
        url = static_image_url(LOGO_PATH, max_width=max_width, keep_png=True)
        if url:
            return url
    return image_to_data_uri(LOGO_PATH, max_width=max_width, keep_png=True)
