from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any

from .valueobject import EmployeeId


ONE_HOUR = timedelta(hours=1)


@dataclass
class WorkRecord:
    work_date: date
    employee_id: EmployeeId
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    hours: Optional[float] = None  # decimal hours

    def to_row(self) -> Dict[str, Any]:
        return {
            "date": self.work_date.isoformat(),
            "employee_id": str(self.employee_id),
            "clock_in": self.clock_in.isoformat() if self.clock_in else "",
            "clock_out": self.clock_out.isoformat() if self.clock_out else "",
            "hours": f"{self.hours:.2f}" if self.hours is not None else "",
        }


def compute_hours(clock_in: datetime, clock_out: datetime) -> float:
    """Compute working hours with a fixed 1-hour break deducted; min 0."""
    delta = clock_out - clock_in - ONE_HOUR
    if delta.total_seconds() < 0:
        return 0.0
    return round(delta.total_seconds() / 3600.0, 2)


def is_acceptable_card(tag: Any) -> bool:
    """Check if the tag is an acceptable card type for the timecard system.

    Notes:
    - Accepts FeliCa cards (PASMO, Suica, etc.) - recommended
    - Accepts Type4 tags (My Number cards) - but UID is randomized, not recommended
    - For local use and testing flexibility, allow override via env.
    """
    import os

    if os.environ.get("ACCEPT_ALL_TAGS", "").lower() in {"1", "true", "yes"}:
        return True

    cls_name = type(tag).__name__

    # Accept FeliCa cards (PASMO, Suica, etc.) - these have stable IDs
    if "FeliCa" in cls_name or "Type3Tag" in cls_name:
        return True

    # Accept Type 4 tags (including Type4BTag for My Number cards)
    # Note: My Number cards have randomized UIDs, so not ideal for identification
    if "Type4" in cls_name:
        return True

    # Fallback deny by default.
    return False
