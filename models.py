"""
Domain models and constants.

Money is stored in the database as integer PENCE to avoid floating-point
rounding errors. The dataclasses below use pounds (float) at the UI boundary
and are converted with ``utils.to_pence`` / ``utils.from_pence``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

# --- Status vocabularies ----------------------------------------------------
PAYMENT_STATUSES = ["Paid", "Partially Paid", "Unpaid"]
JOB_STATUSES = ["Enquiry", "Booked", "In Progress", "Completed", "Cancelled"]
ENQUIRY_STATUSES = ["New", "Contacted", "Converted", "Closed"]
PAYMENT_METHODS = ["Cash", "Bank Transfer", "Card", "Other"]

# Jobs with these statuses count towards revenue figures.
# "Enquiry" (not yet confirmed) and "Cancelled" jobs are excluded.
REVENUE_JOB_STATUSES = ["Booked", "In Progress", "Completed"]
PENDING_JOB_STATUSES = ["Enquiry", "Booked", "In Progress"]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class ValidationError(Exception):
    """Raised when user input fails validation. ``errors`` is a list of messages."""

    def __init__(self, errors: list[str] | str):
        if isinstance(errors, str):
            errors = [errors]
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class ClientInput:
    name: str
    phone: str = ""
    whatsapp: str = ""
    email: str = ""
    vehicle_make: str = ""
    vehicle_model: str = ""
    registration: str = ""
    area: str = ""
    notes: str = ""


@dataclass
class JobInput:
    client_id: int
    job_date: date
    service: str
    service_price: float
    vehicle: str = ""
    registration: str = ""
    additional_charges: float = 0.0
    discount: float = 0.0
    job_status: str = "Booked"
    notes: str = ""

    @property
    def total_amount(self) -> float:
        return round(self.service_price + self.additional_charges - self.discount, 2)


@dataclass
class PaymentInput:
    job_id: int
    amount: float
    paid_at: date
    method: str = "Cash"
    reference: str = ""
    notes: str = ""


@dataclass
class EnquiryInput:
    name: str
    phone: str
    service: str
    preferred_date: Optional[date]
    preferred_time: str = ""
    email: str = ""
    vehicle_make: str = ""
    vehicle_model: str = ""
    registration: str = ""
    notes: str = ""


@dataclass
class ReportFilters:
    start: Optional[date] = None
    end: Optional[date] = None
    services: list[str] = field(default_factory=list)
    payment_statuses: list[str] = field(default_factory=list)
