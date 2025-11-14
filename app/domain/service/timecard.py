from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, date

from ..valueobject import EmployeeId


# 休憩1時間
ONE_HOUR = timedelta(hours=1)


@dataclass
class WorkRecord:
    work_date: date
    employee_id: EmployeeId
    clock_in: datetime | None = None
    clock_out: datetime | None = None
    hours: float | None = None  # decimal hours

    def to_row(self) -> dict[str, str]:
        return {
            "date": self.work_date.isoformat(),
            "employee_id": str(self.employee_id),
            "clock_in": self.clock_in.isoformat() if self.clock_in else "",
            "clock_out": self.clock_out.isoformat() if self.clock_out else "",
            "hours": f"{self.hours:.2f}" if self.hours is not None else "",
        }


class TimecardService:
    """タイムカード関連のドメインサービス。

    - 勤務時間計算
    - NFCタグ受け入れ可否
    """

    @staticmethod
    def compute_hours(clock_in: datetime, clock_out: datetime) -> float:
        """1時間休憩を差し引いた実働時間（時間）を小数で返す。最小0。"""
        delta = clock_out - clock_in - ONE_HOUR
        if delta.total_seconds() < 0:
            return 0.0
        return round(delta.total_seconds() / 3600.0, 2)

    @staticmethod
    def is_acceptable_card(tag: object) -> bool:
        """NFCタグが受け入れ可能か判定。

        PASMO等のFeliCa (Type3Tag) のみを受け付けます。
        環境変数 ACCEPT_ALL_TAGS=1/true/yes で強制許可。
        FeliCa/Type3Tag以外は ValueError を送出して明示的に拒否。
        """
        if os.environ.get("ACCEPT_ALL_TAGS", "").lower() in {"1", "true", "yes"}:
            return True

        cls_name = type(tag).__name__
        # FeliCa / Type3Tag は安定UID (PASMO等)
        if ("FeliCa" in cls_name) or ("Type3Tag" in cls_name):
            return True

        raise ValueError(f"未対応のタグ種別です: {cls_name}")
