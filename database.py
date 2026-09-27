"""
Database layer (SQLite).

All SQL lives in this module and ``services.py`` and ALWAYS uses parameterised
queries - user input is never concatenated into SQL.

Migrating to PostgreSQL later
-----------------------------
Only this file needs to change substantially: swap ``sqlite3`` for
``psycopg`` in ``get_connection``, change ``?`` placeholders to ``%s``, and
translate the schema below (INTEGER PRIMARY KEY AUTOINCREMENT -> SERIAL /
IDENTITY, TEXT dates -> DATE/TIMESTAMP). ``services.py`` talks to the
database only through ``fetch_all``, ``fetch_one``, ``execute`` and
``transaction``.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from config import DATA_DIR, SERVICES

log = logging.getLogger("ja_detailing.db")

DB_PATH = Path(os.environ.get("JA_DB_PATH", DATA_DIR / "database.db"))

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    active      INTEGER NOT NULL DEFAULT 1,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    phone         TEXT NOT NULL DEFAULT '',
    whatsapp      TEXT NOT NULL DEFAULT '',
    email         TEXT NOT NULL DEFAULT '',
    vehicle_make  TEXT NOT NULL DEFAULT '',
    vehicle_model TEXT NOT NULL DEFAULT '',
    registration  TEXT NOT NULL DEFAULT '',
    area          TEXT NOT NULL DEFAULT '',
    notes         TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);
CREATE INDEX IF NOT EXISTS idx_clients_reg  ON clients(registration);

CREATE TABLE IF NOT EXISTS jobs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id          INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    job_date           TEXT NOT NULL,
    vehicle            TEXT NOT NULL DEFAULT '',
    registration       TEXT NOT NULL DEFAULT '',
    service            TEXT NOT NULL,
    service_price      INTEGER NOT NULL DEFAULT 0,   -- pence
    additional_charges INTEGER NOT NULL DEFAULT 0,   -- pence
    discount           INTEGER NOT NULL DEFAULT 0,   -- pence
    total_amount       INTEGER NOT NULL DEFAULT 0,   -- pence
    job_status         TEXT NOT NULL DEFAULT 'Booked',
    notes              TEXT NOT NULL DEFAULT '',
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (total_amount >= 0)
);
CREATE INDEX IF NOT EXISTS idx_jobs_client ON jobs(client_id);
CREATE INDEX IF NOT EXISTS idx_jobs_date   ON jobs(job_date);

CREATE TABLE IF NOT EXISTS payments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    amount     INTEGER NOT NULL,                     -- pence
    method     TEXT NOT NULL DEFAULT 'Cash',
    paid_at    TEXT NOT NULL,
    reference  TEXT NOT NULL DEFAULT '',
    notes      TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (amount > 0)
);
CREATE INDEX IF NOT EXISTS idx_payments_job ON payments(job_id);

-- Receipts keep a snapshot of the figures at the time they were issued,
-- so historic receipts never change even if the job is edited later.
CREATE TABLE IF NOT EXISTS receipts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no      TEXT NOT NULL UNIQUE,
    receipt_year    INTEGER NOT NULL,
    receipt_seq     INTEGER NOT NULL,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    client_name     TEXT NOT NULL,
    vehicle         TEXT NOT NULL DEFAULT '',
    registration    TEXT NOT NULL DEFAULT '',
    service         TEXT NOT NULL,
    job_date        TEXT NOT NULL,
    total_amount    INTEGER NOT NULL,
    amount_received INTEGER NOT NULL,
    outstanding     INTEGER NOT NULL,
    payment_status  TEXT NOT NULL,
    issued_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (receipt_year, receipt_seq)
);

CREATE TABLE IF NOT EXISTS enquiries (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    phone          TEXT NOT NULL,
    email          TEXT NOT NULL DEFAULT '',
    vehicle_make   TEXT NOT NULL DEFAULT '',
    vehicle_model  TEXT NOT NULL DEFAULT '',
    registration   TEXT NOT NULL DEFAULT '',
    service        TEXT NOT NULL,
    preferred_date TEXT,
    preferred_time TEXT NOT NULL DEFAULT '',
    notes          TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'New',
    client_id      INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Jobs with live payment figures. Payment status is derived, never stored,
-- so it can never drift out of sync with the payments table.
CREATE VIEW IF NOT EXISTS v_jobs AS
SELECT
    j.*,
    c.name AS client_name,
    c.phone AS client_phone,
    COALESCE(p.received, 0) AS amount_received,
    j.total_amount - COALESCE(p.received, 0) AS outstanding,
    CASE
        WHEN j.total_amount > 0 AND COALESCE(p.received, 0) >= j.total_amount THEN 'Paid'
        WHEN j.total_amount = 0 AND j.job_status = 'Completed' THEN 'Paid'
        WHEN COALESCE(p.received, 0) > 0 THEN 'Partially Paid'
        ELSE 'Unpaid'
    END AS payment_status
FROM jobs j
JOIN clients c ON c.id = j.client_id
LEFT JOIN (
    SELECT job_id, SUM(amount) AS received FROM payments GROUP BY job_id
) p ON p.job_id = j.id;
"""


def get_connection() -> sqlite3.Connection:
    """Open a new connection. SQLite connections are cheap; one per operation
    keeps things safe across Streamlit's multi-threaded reruns."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15, detect_types=0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def transaction(immediate: bool = False) -> Iterator[sqlite3.Connection]:
    """Context manager that commits on success and rolls back on error.

    ``immediate=True`` takes the write lock up front - used when generating
    sequential numbers (receipts) so two sessions can't grab the same number.
    """
    conn = get_connection()
    try:
        if immediate:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
    finally:
        conn.close()


def fetch_one(sql: str, params: Iterable[Any] = ()) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(sql, tuple(params)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """Run a single write statement. Returns lastrowid."""
    with transaction() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.lastrowid


def init_db() -> None:
    """Create tables if needed and seed the service list and default settings.

    Safe to call on every app start (idempotent). The database starts EMPTY of
    clients, jobs and revenue - no fake business data is created.
    """
    with transaction() as conn:
        conn.executescript(SCHEMA)
        for order, svc in enumerate(SERVICES):
            conn.execute(
                "INSERT OR IGNORE INTO services (name, description, sort_order) VALUES (?, ?, ?)",
                (svc["name"], svc["description"], order),
            )
        defaults = {
            "schema_version": str(SCHEMA_VERSION),
            "receipt_footer": "Thank you for choosing JA Detailing London.",
            "receipt_prefix": "JA",
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )
    log.info("Database ready at %s", DB_PATH)
