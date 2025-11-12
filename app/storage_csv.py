from __future__ import annotations

import csv
import os
from datetime import datetime, date
from typing import List, Dict, Optional

from .domain import WorkRecord, compute_hours

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "records.csv")
FIELDS = ["date", "employee_id", "clock_in", "clock_out", "hours"]


def _ensure_store() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def _load_all() -> List[Dict[str, str]]:
    _ensure_store()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _save_all(rows: List[Dict[str, str]]) -> None:
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _parse_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def get_records(date_filter: Optional[date] = None, employee_id: Optional[str] = None) -> List[WorkRecord]:
    rows = _load_all()
    out: List[WorkRecord] = []
    for r in rows:
        d = date.fromisoformat(r["date"]) if r.get("date") else None
        if d is None:
            continue
        if date_filter and d != date_filter:
            continue
        if employee_id and r.get("employee_id") != employee_id:
            continue
        wr = WorkRecord(
            work_date=d,
            employee_id=r.get("employee_id", ""),
            clock_in=_parse_dt(r.get("clock_in", "")),
            clock_out=_parse_dt(r.get("clock_out", "")),
            hours=float(r["hours"]) if r.get("hours") else None,
        )
        out.append(wr)
    return out


def _find_row_index(rows: List[Dict[str, str]], d: date, employee_id: str) -> Optional[int]:
    for i, r in enumerate(rows):
        if r.get("date") == d.isoformat() and r.get("employee_id") == employee_id:
            return i
    return None


def punch(employee_id: str, now: Optional[datetime] = None) -> WorkRecord:
    """Toggle clock-in/clock-out for today for the given employee.

    First punch of the day sets clock_in. Second sets clock_out and computes hours.
    Subsequent punches append a new row with clock_in again (simple behavior).
    """
    _ensure_store()
    now = now or datetime.now()
    today = now.date()
    rows = _load_all()

    idx = _find_row_index(rows, today, employee_id)
    if idx is None:
        wr = WorkRecord(work_date=today, employee_id=employee_id, clock_in=now)
        rows.append(wr.to_row())
        _save_all(rows)
        return wr

    # existing row
    r = rows[idx]
    ci = _parse_dt(r.get("clock_in", ""))
    co = _parse_dt(r.get("clock_out", ""))
    if ci is None:
        r["clock_in"] = now.isoformat()
        rows[idx] = r
        _save_all(rows)
    elif co is None:
        r["clock_out"] = now.isoformat()
        hrs = compute_hours(ci, now)
        r["hours"] = f"{hrs:.2f}"
        rows[idx] = r
        _save_all(rows)
    else:
        # both exist already; ignore further punches for today
        pass  # Do nothing, return existing record

    return WorkRecord(
        work_date=today,
        employee_id=employee_id,
        clock_in=_parse_dt(r.get("clock_in", "")),
        clock_out=_parse_dt(r.get("clock_out", "")),
        hours=float(r["hours"]) if r.get("hours") else None,
    )


def daily_summary(d: date) -> Dict[str, float]:
    """Sum of hours by employee_id for the date."""
    records = get_records(date_filter=d)
    total: Dict[str, float] = {}
    for r in records:
        if r.hours is not None:
            total[r.employee_id] = total.get(r.employee_id, 0.0) + r.hours
    return total
