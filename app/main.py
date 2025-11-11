from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Query

from . import storage_csv as store

app = FastAPI(title="NFC Timecard (Local)")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/records")
def list_records(
    date_str: Optional[str] = Query(None, description="YYYY-MM-DD"),
    employee_id: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    d = date.fromisoformat(date_str) if date_str else None
    records = store.get_records(date_filter=d, employee_id=employee_id)
    return [r.to_row() for r in records]


@app.get("/records/{employee_id}")
def list_records_by_employee(employee_id: str) -> List[Dict[str, Any]]:
    records = store.get_records(employee_id=employee_id)
    return [r.to_row() for r in records]


@app.post("/punch")
def punch(employee_id: str) -> Dict[str, Any]:
    wr = store.punch(employee_id=employee_id, now=datetime.now())
    return wr.to_row()


@app.get("/summary/daily")
def summary_daily(date_str: str = Query(..., description="YYYY-MM-DD")) -> Dict[str, float]:
    d = date.fromisoformat(date_str)
    return store.daily_summary(d)
