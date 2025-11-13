from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Final, Literal

from .valueobject import EmployeeId


ONE_HOUR: Final[timedelta] = timedelta(hours=1)


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


# 明示的に扱うタグのクラス名（nfcpyなどの代表）
TagClassName = Literal["FeliCa", "Type3Tag", "Type4Tag", "Type4BTag"]


class TimecardService:
    """アプリケーションサービス。

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
    def is_acceptable_card_name(tag_class: TagClassName) -> bool:
        """許可する既知のタグクラス名か判定。"""
        # FeliCa/Type3 は安定UID
        if tag_class in ("FeliCa", "Type3Tag"):
            return True
        # Type4/Type4B はUIDランダムの可能性があるので非推奨だが許可
        if tag_class in ("Type4Tag", "Type4BTag"):
            return True
        return False  # Literalで型は絞っているが将来の保険

    @staticmethod
    def is_acceptable_card(tag: object) -> bool:
        """NFCタグが受け入れ可能か判定。

        環境変数 ACCEPT_ALL_TAGS=1/true/yes で強制許可。
        既知のタグクラス名以外は ValueError を送出して明示的に拒否。
        """
        import os

        if os.environ.get("ACCEPT_ALL_TAGS", "").lower() in {"1", "true", "yes"}:
            return True

        cls_name = type(tag).__name__
        if any(key in cls_name for key in ("FeliCa", "Type3Tag")):
            return True
        if "Type4" in cls_name:  # Type4Tag / Type4BTag など
            return True

        # 既知以外は例外で通知（Anyを避け、明示的に制限）
        raise ValueError(f"未対応のタグ種別です: {cls_name}")


# 既存互換のトップレベル関数（既存コードからの呼び出しを壊さないため）
def compute_hours(clock_in: datetime, clock_out: datetime) -> float:
    return TimecardService.compute_hours(clock_in, clock_out)


def is_acceptable_card(tag: object) -> bool:
    return TimecardService.is_acceptable_card(tag)
