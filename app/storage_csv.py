from __future__ import annotations

from datetime import datetime, date

from app.domain.service import TimecardCsvStore, WorkRecord

# 互換用の薄いアダプタ。今後は TimecardCsvStore を直接利用してください。
_store = TimecardCsvStore.default()


def get_records(
    date_filter: date | None = None, employee_id: str | None = None
) -> list[WorkRecord]:
    return _store.get_records(date_filter=date_filter, employee_id=employee_id)


def punch(employee_id: str, now: datetime | None = None) -> WorkRecord:
    return _store.punch(employee_id=employee_id, now=now)


def daily_summary(d: date) -> dict[str, float]:
    return _store.daily_summary(d)
