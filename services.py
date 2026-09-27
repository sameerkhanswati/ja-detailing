"""
Business logic layer: clients, jobs, payments, receipts, enquiries, reports.

Pages call these functions; they never write SQL themselves. Every query is
parameterised. Monetary values are pence (int) in the DB; inputs arrive in
pounds and are converted here.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import date

import pandas as pd

import database as db
from config import SERVICE_NAMES
from models import (
    ENQUIRY_STATUSES,
    JOB_STATUSES,
    PAYMENT_METHODS,
    PENDING_JOB_STATUSES,
    REVENUE_JOB_STATUSES,
    ClientInput,
    EnquiryInput,
    JobInput,
    PaymentInput,
    ReportFilters,
    ValidationError,
)
from utils import (
    clean_text,
    is_valid_email,
    is_valid_phone,
    is_valid_registration,
    normalise_registration,
    now_london_str,
    parse_date,
    to_pence,
    today_london,
    validate_money,
)

log = logging.getLogger("ja_detailing.services")


def client_code(client_id: int | None) -> str:
    return f"CL-{int(client_id):04d}" if client_id else "—"


def job_code(job_id: int | None) -> str:
    return f"JOB-{int(job_id):05d}" if job_id else "—"


def enquiry_code(enquiry_id: int | None) -> str:
    return f"ENQ-{int(enquiry_id):05d}" if enquiry_id else "—"


# ===========================================================================
# Services list & settings
# ===========================================================================
def list_service_names(active_only: bool = True) -> list[str]:
    sql = "SELECT name FROM services"
    if active_only:
        sql += " WHERE active = 1"
    sql += " ORDER BY sort_order, name"
    names = [r["name"] for r in db.fetch_all(sql)]
    return names or list(SERVICE_NAMES)


def list_services() -> list[dict]:
    return db.fetch_all("SELECT * FROM services ORDER BY sort_order, name")


def set_service_active(service_id: int, active: bool) -> None:
    db.execute("UPDATE services SET active = ? WHERE id = ?", (1 if active else 0, service_id))


def get_setting(key: str, default: str = "") -> str:
    row = db.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, clean_text(value, 500)),
    )


# ===========================================================================
# Clients
# ===========================================================================
def _validate_client(c: ClientInput) -> ClientInput:
    errors = []
    c = ClientInput(
        name=clean_text(c.name, 120),
        phone=clean_text(c.phone, 30),
        whatsapp=clean_text(c.whatsapp, 30),
        email=clean_text(c.email, 160),
        vehicle_make=clean_text(c.vehicle_make, 60),
        vehicle_model=clean_text(c.vehicle_model, 60),
        registration=normalise_registration(clean_text(c.registration, 12)),
        area=clean_text(c.area, 120),
        notes=clean_text(c.notes, 2000),
    )
    if not c.name:
        errors.append("Client name is required.")
    if c.phone and not is_valid_phone(c.phone):
        errors.append("Phone number doesn't look valid (use e.g. 07123 456789 or +44 7123 456789).")
    if c.whatsapp and not is_valid_phone(c.whatsapp):
        errors.append("WhatsApp number doesn't look valid.")
    if c.email and not is_valid_email(c.email):
        errors.append("Email address doesn't look valid.")
    if not is_valid_registration(c.registration):
        errors.append("Registration should only contain letters, numbers and spaces.")
    if errors:
        raise ValidationError(errors)
    return c


def create_client(c: ClientInput) -> int:
    c = _validate_client(c)
    return db.execute(
        """INSERT INTO clients (name, phone, whatsapp, email, vehicle_make, vehicle_model,
                                registration, area, notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (c.name, c.phone, c.whatsapp, c.email, c.vehicle_make, c.vehicle_model,
         c.registration, c.area, c.notes, now_london_str()),
    )


def update_client(client_id: int, c: ClientInput) -> None:
    c = _validate_client(c)
    db.execute(
        """UPDATE clients SET name=?, phone=?, whatsapp=?, email=?, vehicle_make=?,
               vehicle_model=?, registration=?, area=?, notes=? WHERE id=?""",
        (c.name, c.phone, c.whatsapp, c.email, c.vehicle_make, c.vehicle_model,
         c.registration, c.area, c.notes, client_id),
    )


def delete_client(client_id: int) -> None:
    """Deletes the client AND their jobs/payments (receipts are kept as history)."""
    db.execute("DELETE FROM clients WHERE id = ?", (client_id,))


def get_client(client_id: int) -> dict | None:
    return db.fetch_one("SELECT * FROM clients WHERE id = ?", (client_id,))


def list_clients(search: str = "") -> list[dict]:
    """Search by name, phone, WhatsApp, vehicle make/model or registration."""
    search = clean_text(search, 80)
    base = """
        SELECT c.*,
               (SELECT COUNT(*) FROM jobs j WHERE j.client_id = c.id) AS job_count,
               (SELECT MAX(job_date) FROM jobs j WHERE j.client_id = c.id) AS last_job
        FROM clients c
    """
    if not search:
        return db.fetch_all(base + " ORDER BY c.created_at DESC, c.id DESC")
    like = f"%{search}%"
    reg_like = f"%{search.replace(' ', '').upper()}%"
    return db.fetch_all(
        base + """
        WHERE c.name LIKE ? OR c.phone LIKE ? OR c.whatsapp LIKE ? OR c.email LIKE ?
           OR c.vehicle_make LIKE ? OR c.vehicle_model LIKE ?
           OR (c.vehicle_make || ' ' || c.vehicle_model) LIKE ?
           OR REPLACE(c.registration, ' ', '') LIKE ?
        ORDER BY c.name COLLATE NOCASE
        """,
        (like, like, like, like, like, like, like, reg_like),
    )


def client_history(client_id: int) -> list[dict]:
    return db.fetch_all(
        "SELECT * FROM v_jobs WHERE client_id = ? ORDER BY job_date DESC, id DESC", (client_id,)
    )


def client_options() -> dict[int, str]:
    rows = db.fetch_all(
        "SELECT id, name, registration, vehicle_make, vehicle_model FROM clients ORDER BY name COLLATE NOCASE"
    )
    out = {}
    for r in rows:
        extra = " ".join(x for x in [r["vehicle_make"], r["vehicle_model"], r["registration"]] if x)
        out[r["id"]] = f"{r['name']} · {client_code(r['id'])}" + (f" · {extra}" if extra else "")
    return out


# ===========================================================================
# Jobs
# ===========================================================================
def _validate_job(j: JobInput) -> JobInput:
    errors = []
    if not j.client_id or not get_client(int(j.client_id)):
        errors.append("Please select a client.")
    if not j.service:
        errors.append("Service is required.")
    if not parse_date(j.job_date):
        errors.append("Date is required.")
    if j.job_status not in JOB_STATUSES:
        errors.append("Invalid job status.")
    errors += validate_money(j.service_price, "Service price")
    errors += validate_money(j.additional_charges, "Additional charges")
    errors += validate_money(j.discount, "Discount")
    if not errors and j.total_amount < 0:
        errors.append("Discount cannot be larger than the service price plus additional charges.")
    if not is_valid_registration(j.registration or ""):
        errors.append("Registration should only contain letters, numbers and spaces.")
    if errors:
        raise ValidationError(errors)
    j.vehicle = clean_text(j.vehicle, 120)
    j.registration = normalise_registration(clean_text(j.registration, 12))
    j.notes = clean_text(j.notes, 2000)
    j.service = clean_text(j.service, 80)
    return j


def create_job(j: JobInput, initial_payment: float = 0.0, payment_method: str = "Cash") -> int:
    j = _validate_job(j)
    errors = validate_money(initial_payment, "Amount received")
    total_p = to_pence(j.total_amount)
    pay_p = to_pence(initial_payment or 0)
    if not errors and pay_p > total_p:
        errors.append("Amount received cannot be more than the total amount.")
    if errors:
        raise ValidationError(errors)
    now = now_london_str()
    with db.transaction() as conn:
        cur = conn.execute(
            """INSERT INTO jobs (client_id, job_date, vehicle, registration, service,
                   service_price, additional_charges, discount, total_amount,
                   job_status, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (int(j.client_id), parse_date(j.job_date).isoformat(), j.vehicle, j.registration,
             j.service, to_pence(j.service_price), to_pence(j.additional_charges),
             to_pence(j.discount), total_p, j.job_status, j.notes, now, now),
        )
        job_id = cur.lastrowid
        if pay_p > 0:
            conn.execute(
                "INSERT INTO payments (job_id, amount, method, paid_at, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, pay_p, payment_method if payment_method in PAYMENT_METHODS else "Other",
                 parse_date(j.job_date).isoformat(), "Recorded with job", now),
            )
    return job_id


def update_job(job_id: int, j: JobInput) -> None:
    j = _validate_job(j)
    current = get_job(job_id)
    if not current:
        raise ValidationError("Job not found.")
    total_p = to_pence(j.total_amount)
    if total_p < current["amount_received"]:
        raise ValidationError(
            "The new total is less than the amount already received. "
            "Remove or adjust payments first."
        )
    db.execute(
        """UPDATE jobs SET client_id=?, job_date=?, vehicle=?, registration=?, service=?,
               service_price=?, additional_charges=?, discount=?, total_amount=?,
               job_status=?, notes=?, updated_at=? WHERE id=?""",
        (int(j.client_id), parse_date(j.job_date).isoformat(), j.vehicle, j.registration, j.service,
         to_pence(j.service_price), to_pence(j.additional_charges), to_pence(j.discount),
         total_p, j.job_status, j.notes, now_london_str(), job_id),
    )


def delete_job(job_id: int) -> None:
    db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))


def get_job(job_id: int) -> dict | None:
    return db.fetch_one("SELECT * FROM v_jobs WHERE id = ?", (job_id,))


def list_jobs(
    start: date | None = None,
    end: date | None = None,
    client_id: int | None = None,
    services: list[str] | None = None,
    job_statuses: list[str] | None = None,
    payment_statuses: list[str] | None = None,
    search: str = "",
) -> list[dict]:
    where, params = [], []
    if start:
        where.append("job_date >= ?")
        params.append(start.isoformat())
    if end:
        where.append("job_date <= ?")
        params.append(end.isoformat())
    if client_id:
        where.append("client_id = ?")
        params.append(int(client_id))
    for col, values in (("service", services), ("job_status", job_statuses),
                        ("payment_status", payment_statuses)):
        if values:
            where.append(f"{col} IN ({','.join('?' * len(values))})")  # column names are fixed
            params.extend(values)
    search = clean_text(search, 80)
    if search:
        like = f"%{search}%"
        where.append("(client_name LIKE ? OR vehicle LIKE ? OR REPLACE(registration,' ','') LIKE ?)")
        params += [like, like, f"%{search.replace(' ', '').upper()}%"]
    sql = "SELECT * FROM v_jobs"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY job_date DESC, id DESC"
    return db.fetch_all(sql, params)


def job_options(only_outstanding: bool = False) -> dict[int, str]:
    sql = "SELECT id, client_name, service, job_date, total_amount, outstanding FROM v_jobs"
    if only_outstanding:
        sql += " WHERE outstanding > 0 AND job_status != 'Cancelled'"
    sql += " ORDER BY job_date DESC, id DESC"
    from utils import fmt_date, gbp

    return {
        r["id"]: f"{job_code(r['id'])} · {r['client_name']} · {r['service']} · {fmt_date(r['job_date'])}"
                 f" · {gbp(r['outstanding'])} due"
        for r in db.fetch_all(sql)
    }


# ===========================================================================
# Payments
# ===========================================================================
def add_payment(p: PaymentInput) -> int:
    errors = validate_money(p.amount, "Payment amount", allow_zero=False)
    job = get_job(int(p.job_id)) if p.job_id else None
    if not job:
        errors.append("Please select a job.")
    if not parse_date(p.paid_at):
        errors.append("Payment date is required.")
    if p.method not in PAYMENT_METHODS:
        errors.append("Invalid payment method.")
    if errors:
        raise ValidationError(errors)
    amount_p = to_pence(p.amount)
    if amount_p > job["outstanding"]:
        from utils import gbp

        raise ValidationError(
            f"Payment of {gbp(amount_p)} is more than the outstanding balance of {gbp(job['outstanding'])}."
        )
    return db.execute(
        "INSERT INTO payments (job_id, amount, method, paid_at, reference, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (int(p.job_id), amount_p, p.method, parse_date(p.paid_at).isoformat(),
         clean_text(p.reference, 80), clean_text(p.notes, 500), now_london_str()),
    )


def delete_payment(payment_id: int) -> None:
    db.execute("DELETE FROM payments WHERE id = ?", (payment_id,))


def list_payments(start: date | None = None, end: date | None = None, job_id: int | None = None) -> list[dict]:
    where, params = [], []
    if start:
        where.append("p.paid_at >= ?")
        params.append(start.isoformat())
    if end:
        where.append("p.paid_at <= ?")
        params.append(end.isoformat())
    if job_id:
        where.append("p.job_id = ?")
        params.append(int(job_id))
    sql = """SELECT p.*, j.service, j.client_name, j.job_date
             FROM payments p JOIN v_jobs j ON j.id = p.job_id"""
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY p.paid_at DESC, p.id DESC"
    return db.fetch_all(sql, params)


# ===========================================================================
# Receipts - unique sequential numbers per year: JA-2026-0001
# ===========================================================================
def generate_receipt(job_id: int) -> dict:
    job = get_job(job_id)
    if not job:
        raise ValidationError("Job not found.")
    if job["job_status"] == "Cancelled":
        raise ValidationError("Receipts can't be generated for cancelled jobs.")
    prefix = get_setting("receipt_prefix", "JA") or "JA"
    year = today_london().year
    for _attempt in range(5):
        try:
            with db.transaction(immediate=True) as conn:
                row = conn.execute(
                    "SELECT COALESCE(MAX(receipt_seq), 0) + 1 FROM receipts WHERE receipt_year = ?",
                    (year,),
                ).fetchone()
                seq = int(row[0])
                receipt_no = f"{prefix}-{year}-{seq:04d}"
                cur = conn.execute(
                    """INSERT INTO receipts (receipt_no, receipt_year, receipt_seq, job_id, client_name,
                           vehicle, registration, service, job_date, total_amount, amount_received,
                           outstanding, payment_status, issued_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (receipt_no, year, seq, job_id, job["client_name"], job["vehicle"],
                     job["registration"], job["service"], job["job_date"], job["total_amount"],
                     job["amount_received"], job["outstanding"], job["payment_status"],
                     now_london_str()),
                )
                rid = cur.lastrowid
            return get_receipt(rid)
        except sqlite3.IntegrityError:
            log.warning("Receipt number collision, retrying")
    raise ValidationError("Could not generate a unique receipt number - please try again.")


def get_receipt(receipt_id: int) -> dict | None:
    return db.fetch_one("SELECT * FROM receipts WHERE id = ?", (receipt_id,))


def list_receipts(search: str = "") -> list[dict]:
    search = clean_text(search, 80)
    if search:
        like = f"%{search}%"
        return db.fetch_all(
            "SELECT * FROM receipts WHERE receipt_no LIKE ? OR client_name LIKE ? OR registration LIKE ? "
            "ORDER BY id DESC",
            (like, like, like),
        )
    return db.fetch_all("SELECT * FROM receipts ORDER BY id DESC")


def receipts_for_job(job_id: int) -> list[dict]:
    return db.fetch_all("SELECT * FROM receipts WHERE job_id = ? ORDER BY id DESC", (job_id,))


# ===========================================================================
# Enquiries (from the public website)
# ===========================================================================
def create_enquiry(e: EnquiryInput) -> int:
    errors = []
    name = clean_text(e.name, 120)
    phone = clean_text(e.phone, 30)
    email = clean_text(e.email, 160)
    reg = normalise_registration(clean_text(e.registration, 12))
    if not name:
        errors.append("Please enter your name.")
    if not phone:
        errors.append("Please enter your WhatsApp or phone number.")
    elif not is_valid_phone(phone):
        errors.append("Please enter a valid phone number (e.g. 07123 456789).")
    if email and not is_valid_email(email):
        errors.append("Please enter a valid email address, or leave it blank.")
    if not e.service or e.service not in list_service_names(active_only=False):
        errors.append("Please choose a service.")
    if not clean_text(e.vehicle_make, 60):
        errors.append("Please enter your vehicle make.")
    if not clean_text(e.vehicle_model, 60):
        errors.append("Please enter your vehicle model.")
    pdate = parse_date(e.preferred_date)
    if not pdate:
        errors.append("Please choose a preferred date.")
    elif pdate < today_london():
        errors.append("Preferred date can't be in the past.")
    elif pdate.weekday() == 6:
        errors.append("We're closed on Sundays - please choose Monday to Saturday.")
    if not is_valid_registration(reg):
        errors.append("Registration should only contain letters, numbers and spaces.")
    if errors:
        raise ValidationError(errors)
    return db.execute(
        """INSERT INTO enquiries (name, phone, email, vehicle_make, vehicle_model, registration,
               service, preferred_date, preferred_time, notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, phone, email, clean_text(e.vehicle_make, 60), clean_text(e.vehicle_model, 60), reg,
         e.service, pdate.isoformat(), clean_text(e.preferred_time, 40),
         clean_text(e.notes, 1500), now_london_str()),
    )


def list_enquiries(statuses: list[str] | None = None) -> list[dict]:
    if statuses:
        return db.fetch_all(
            f"SELECT * FROM enquiries WHERE status IN ({','.join('?' * len(statuses))}) ORDER BY id DESC",
            statuses,
        )
    return db.fetch_all("SELECT * FROM enquiries ORDER BY id DESC")


def update_enquiry_status(enquiry_id: int, status: str) -> None:
    if status not in ENQUIRY_STATUSES:
        raise ValidationError("Invalid status.")
    db.execute("UPDATE enquiries SET status = ? WHERE id = ?", (status, enquiry_id))


def delete_enquiry(enquiry_id: int) -> None:
    db.execute("DELETE FROM enquiries WHERE id = ?", (enquiry_id,))


def convert_enquiry(enquiry_id: int) -> tuple[int, int]:
    """Create a client + an 'Enquiry' status job from a website enquiry."""
    e = db.fetch_one("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,))
    if not e:
        raise ValidationError("Enquiry not found.")
    client_id = e["client_id"]
    if not client_id or not get_client(client_id):
        client_id = create_client(ClientInput(
            name=e["name"], phone=e["phone"], whatsapp=e["phone"], email=e["email"],
            vehicle_make=e["vehicle_make"], vehicle_model=e["vehicle_model"],
            registration=e["registration"],
            notes=f"Created from website enquiry {enquiry_code(enquiry_id)}.",
        ))
    job_id = create_job(JobInput(
        client_id=client_id,
        job_date=parse_date(e["preferred_date"]) or today_london(),
        service=e["service"],
        service_price=0,
        vehicle=f"{e['vehicle_make']} {e['vehicle_model']}".strip(),
        registration=e["registration"],
        job_status="Enquiry",
        notes=(f"Preferred time: {e['preferred_time']}\n" if e["preferred_time"] else "") + (e["notes"] or ""),
    ))
    db.execute("UPDATE enquiries SET status = 'Converted', client_id = ? WHERE id = ?", (client_id, enquiry_id))
    return client_id, job_id


# ===========================================================================
# Reporting
# ===========================================================================
def jobs_dataframe(f: ReportFilters | None = None) -> pd.DataFrame:
    """All jobs (with live payment figures) as a DataFrame in POUNDS."""
    f = f or ReportFilters()
    rows = list_jobs(start=f.start, end=f.end, services=f.services or None,
                     payment_statuses=f.payment_statuses or None)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=[
            "id", "client_name", "job_date", "service", "job_status", "payment_status",
            "total_amount", "amount_received", "outstanding",
        ])
    df["job_date"] = pd.to_datetime(df["job_date"])
    for col in ("service_price", "additional_charges", "discount", "total_amount",
                "amount_received", "outstanding"):
        df[col] = df[col].astype(float) / 100.0
    return df


def revenue_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Only jobs that count towards revenue (confirmed, not cancelled)."""
    if df.empty:
        return df
    return df[df["job_status"].isin(REVENUE_JOB_STATUSES)]


def overview() -> dict:
    """Headline numbers for the dashboard (pounds). Uses only real DB data."""
    df = jobs_dataframe()
    rev = revenue_jobs(df)
    today = today_london()
    this_month = rev[(rev["job_date"].dt.year == today.year) & (rev["job_date"].dt.month == today.month)] \
        if not rev.empty else rev
    total_clients = db.fetch_one("SELECT COUNT(*) AS n FROM clients")["n"]
    new_enquiries = db.fetch_one("SELECT COUNT(*) AS n FROM enquiries WHERE status = 'New'")["n"]
    return {
        "total_clients": int(total_clients),
        "total_jobs": int(len(df[df["job_status"] != "Cancelled"])) if not df.empty else 0,
        "total_revenue": float(rev["total_amount"].sum()) if not rev.empty else 0.0,
        "month_revenue": float(this_month["total_amount"].sum()) if not this_month.empty else 0.0,
        "outstanding": float(rev["outstanding"].sum()) if not rev.empty else 0.0,
        "received": float(rev["amount_received"].sum()) if not rev.empty else 0.0,
        "completed_jobs": int((df["job_status"] == "Completed").sum()) if not df.empty else 0,
        "pending_jobs": int(df["job_status"].isin(PENDING_JOB_STATUSES).sum()) if not df.empty else 0,
        "new_enquiries": int(new_enquiries),
    }


def monthly_revenue(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """12-row table (Jan-Dec) of revenue, received, outstanding and job count."""
    from models import MONTHS

    base = pd.DataFrame({"month_num": range(1, 13), "Month": MONTHS})
    rev = revenue_jobs(df)
    if not rev.empty:
        rev = rev[rev["job_date"].dt.year == year]
    if rev.empty:
        base[["Revenue", "Received", "Outstanding", "Jobs"]] = 0
        return base
    g = rev.groupby(rev["job_date"].dt.month).agg(
        Revenue=("total_amount", "sum"),
        Received=("amount_received", "sum"),
        Outstanding=("outstanding", "sum"),
        Jobs=("id", "count"),
    )
    out = base.merge(g, left_on="month_num", right_index=True, how="left").fillna(0)
    out["Jobs"] = out["Jobs"].astype(int)
    return out


def service_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    rev = revenue_jobs(df)
    if rev.empty:
        return pd.DataFrame(columns=["Service", "Jobs", "Revenue", "Average Price", "Received", "Outstanding"])
    g = rev.groupby("service").agg(
        Jobs=("id", "count"),
        Revenue=("total_amount", "sum"),
        Received=("amount_received", "sum"),
        Outstanding=("outstanding", "sum"),
    ).reset_index().rename(columns={"service": "Service"})
    g["Average Price"] = g["Revenue"] / g["Jobs"]
    return g[["Service", "Jobs", "Revenue", "Average Price", "Received", "Outstanding"]] \
        .sort_values("Revenue", ascending=False).reset_index(drop=True)


def period_summary(df: pd.DataFrame) -> dict:
    rev = revenue_jobs(df)
    n = int(len(rev))
    total = float(rev["total_amount"].sum()) if n else 0.0
    return {
        "revenue": total,
        "received": float(rev["amount_received"].sum()) if n else 0.0,
        "outstanding": float(rev["outstanding"].sum()) if n else 0.0,
        "jobs": n,
        "average": (total / n) if n else 0.0,
    }


def available_years() -> list[int]:
    rows = db.fetch_all("SELECT DISTINCT substr(job_date, 1, 4) AS y FROM jobs ORDER BY y DESC")
    years = sorted({int(r["y"]) for r in rows if r["y"] and r["y"].isdigit()} | {today_london().year},
                   reverse=True)
    return years


def export_table(table: str) -> pd.DataFrame:
    """Export a whole table for backup (table name is whitelisted)."""
    allowed = {"clients", "jobs", "payments", "receipts", "enquiries", "services"}
    if table not in allowed:
        raise ValueError("Unknown table")
    return pd.DataFrame(db.fetch_all(f"SELECT * FROM {table} ORDER BY id"))
