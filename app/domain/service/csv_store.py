from __future__ import annotations

import csv
import os
from datetime import datetime, date

from .timecard import WorkRecord, TimecardService
from ..valueobject import EmployeeId


class TimecardCsvStore:
    """CSV バックエンドのストア。

    - 単純な CSV を永続化先として利用
    - アプリ内のユースケースからはクラス経由で利用する
    """

    FIELDS = ["date", "employee_id", "clock_in", "clock_out", "hours"]

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.csv_path = os.path.join(self.data_dir, "records.csv")

    @classmethod
    def default(cls) -> TimecardCsvStore:
        # app/ からの相対で data/ ディレクトリ
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.path.join(base, "data")
        return cls(data_dir)

    # 内部ユーティリティ
    def _ensure_store(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS)
                writer.writeheader()

    def _load_all(self) -> list[dict[str, str]]:
        self._ensure_store()
        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _save_all(self, rows: list[dict[str, str]]) -> None:
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    @staticmethod
    def _parse_dt(s: str) -> datetime | None:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    # Public API
    def get_records(
        self, date_filter: date | None = None, employee_id: str | None = None
    ) -> list[WorkRecord]:
        rows = self._load_all()
        out: list[WorkRecord] = []
        for r in rows:
            d = date.fromisoformat(r["date"]) if r.get("date") else None
            if d is None:
                continue
            if date_filter and d != date_filter:
                continue
            if employee_id and r.get("employee_id") != employee_id:
                continue
            emp = r.get("employee_id", "")
            if not emp:
                continue
            wr = WorkRecord(
                work_date=d,
                employee_id=EmployeeId.from_raw(emp),
                clock_in=self._parse_dt(r.get("clock_in", "")),
                clock_out=self._parse_dt(r.get("clock_out", "")),
                hours=float(r["hours"]) if r.get("hours") else None,
            )
            out.append(wr)
        return out

    @staticmethod
    def _find_row_index(
        rows: list[dict[str, str]], d: date, employee_id: str
    ) -> int | None:
        for i, r in enumerate(rows):
            if r.get("date") == d.isoformat() and r.get("employee_id") == employee_id:
                return i
        return None

    def punch(self, employee_id: str, now: datetime | None = None) -> WorkRecord:
        """トグル動作: 当日の clock-in/out を切替。2回目で hours を計算。"""
        self._ensure_store()
        now = now or datetime.now()
        today = now.date()
        rows = self._load_all()

        idx = self._find_row_index(rows, today, employee_id)
        if idx is None:
            wr = WorkRecord(
                work_date=today,
                employee_id=EmployeeId.from_raw(employee_id),
                clock_in=now,
            )
            rows.append(wr.to_row())
            self._save_all(rows)
            return wr

        # 既存行更新
        r = rows[idx]
        ci = self._parse_dt(r.get("clock_in", ""))
        co = self._parse_dt(r.get("clock_out", ""))
        if ci is None:
            r["clock_in"] = now.isoformat()
            rows[idx] = r
            self._save_all(rows)
        elif co is None:
            r["clock_out"] = now.isoformat()
            hrs = TimecardService.compute_hours(ci, now)
            r["hours"] = f"{hrs:.2f}"
            rows[idx] = r
            self._save_all(rows)
        else:
            # それ以降の打刻は無視
            pass

        return WorkRecord(
            work_date=today,
            employee_id=EmployeeId.from_raw(employee_id),
            clock_in=self._parse_dt(r.get("clock_in", "")),
            clock_out=self._parse_dt(r.get("clock_out", "")),
            hours=float(r["hours"]) if r.get("hours") else None,
        )

    def daily_summary(self, d: date) -> dict[str, float]:
        records = self.get_records(date_filter=d)
        total: dict[str, float] = {}
        for r in records:
            if r.hours is not None:
                key = str(r.employee_id)
                total[key] = total.get(key, 0.0) + r.hours
        return total
