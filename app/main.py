from __future__ import annotations

from datetime import date, datetime

from fastapi import FastAPI, Query

from app.domain.service import TimecardCsvStore

app = FastAPI(title="NFC Timecard (Local)")

# ストアのデフォルト実装（CSV）
store = TimecardCsvStore.default()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/records")
def list_records(
    date_str: str | None = Query(None, description="YYYY-MM-DD"),
    employee_id: str | None = Query(None),
) -> list[dict[str, str]]:
    d = date.fromisoformat(date_str) if date_str else None
    records = store.get_records(date_filter=d, employee_id=employee_id)
    return [r.to_row() for r in records]


@app.get("/records/{employee_id}")
def list_records_by_employee(employee_id: str) -> list[dict[str, str]]:
    records = store.get_records(employee_id=employee_id)
    return [r.to_row() for r in records]


@app.post("/punch")
def punch(employee_id: str) -> dict[str, str]:
    wr = store.punch(employee_id=employee_id, now=datetime.now())
    return wr.to_row()


@app.get("/summary/daily")
def summary_daily(
    date_str: str = Query(..., description="YYYY-MM-DD")
) -> dict[str, float]:
    d = date.fromisoformat(date_str)
    return store.daily_summary(d)
