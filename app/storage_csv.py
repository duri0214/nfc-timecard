from __future__ import annotations

from datetime import datetime, date

from app.domain.service import TimecardCsvStore, WorkRecord


def get_records(
    date_filter: date | None = None, employee_id: str | None = None
) -> list[WorkRecord]:
    return TimecardCsvStore.default().get_records(
        date_filter=date_filter, employee_id=employee_id
    )


def punch(employee_id: str, now: datetime | None = None) -> WorkRecord:
    return TimecardCsvStore.default().punch(employee_id=employee_id, now=now)


def daily_summary(d: date) -> dict[str, float]:
    return TimecardCsvStore.default().daily_summary(d)
