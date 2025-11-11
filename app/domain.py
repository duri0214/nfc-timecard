from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any


ONE_HOUR = timedelta(hours=1)


@dataclass
class WorkRecord:
    work_date: date
    employee_id: str
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    hours: Optional[float] = None  # decimal hours

    def to_row(self) -> Dict[str, Any]:
        return {
            "date": self.work_date.isoformat(),
            "employee_id": self.employee_id,
            "clock_in": self.clock_in.isoformat() if self.clock_in else "",
            "clock_out": self.clock_out.isoformat() if self.clock_out else "",
            "hours": f"{self.hours:.2f}" if self.hours is not None else "",
        }


def compute_hours(clock_in: datetime, clock_out: datetime) -> float:
    """Compute working hours with fixed 1-hour break deducted; min 0."""
    delta = clock_out - clock_in - ONE_HOUR
    if delta.total_seconds() < 0:
        return 0.0
    return round(delta.total_seconds() / 3600.0, 2)


def make_employee_id_from_tag_identifier(identifier: bytes) -> str:
    """Derive a stable, non-PII ID from NFC tag identifier bytes."""
    # Represent as uppercase hex without separators
    return identifier.hex().upper()


def is_likely_my_number_card(tag: Any) -> bool:
    """Best-effort, local-only heuristic to filter My Number cards.

    Notes:
    - Real My Number (JPKI) cards are ISO/IEC 14443 Type B (Type4 Tag).
    - nfcpy exposes different tag classes per chipset; reliable detection can be complex.
    - For KISS and local use, we provide a heuristic and allow override via env.
    """
    import os

    if os.environ.get("ACCEPT_ALL_TAGS", "").lower() in {"1", "true", "yes"}:
        return True

    # Heuristic: Type 4 tags often have 'Type4Tag' in class name; accept those.
    cls_name = type(tag).__name__
    if "Type4Tag" in cls_name:
        return True

    # Fallback deny by default.
    return False
