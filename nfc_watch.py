from __future__ import annotations

import sys
import time
from datetime import datetime, date

import nfc

from app.domain.service import TimecardCsvStore, TimecardService
from app.domain.valueobject import EmployeeId


def on_connect(tag) -> bool:
    if not TimecardService.is_acceptable_card(tag):
        print(f"[WARN] Unsupported tag type ignored: {type(tag).__name__}")
        return True  # keep waiting for the next tag

    # Many tags expose 'identifier' as bytes
    identifier = getattr(tag, "identifier", None)
    if not identifier:
        print("[WARN] Tag has no identifier; ignored")
        return True

    emp_id = str(EmployeeId.from_tag_identifier(identifier))

    # Get the current state before punch
    today: date = datetime.now().date()
    recs = TimecardCsvStore.default().get_records(date_filter=today, employee_id=emp_id)
    was_complete = False
    if recs:
        r0 = recs[0]
        was_complete = bool(r0.clock_in and r0.clock_out)

    wr = TimecardCsvStore.default().punch(emp_id)

    # Determine state based on before/after
    if wr.clock_in and not wr.clock_out:
        state = "clock-in"
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] {emp_id} -> {state} | "
            f"in={wr.clock_in} out={wr.clock_out} hours={wr.hours}"
        )
    elif wr.clock_in and wr.clock_out and not was_complete:
        state = "clock-out"
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] {emp_id} -> {state} | "
            f"in={wr.clock_in} out={wr.clock_out} hours={wr.hours}"
        )
    elif wr.clock_in and wr.clock_out and was_complete:
        state = "already-completed"
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] {emp_id} -> {state} | "
            f"Today's timecard is already complete (in={wr.clock_in.strftime('%H:%M:%S')}, "
            f"out={wr.clock_out.strftime('%H:%M:%S')}, hours={wr.hours})"
        )
    else:
        state = "updated"
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] {emp_id} -> {state} | "
            f"in={wr.clock_in} out={wr.clock_out} hours={wr.hours}"
        )

    # Cooldown to prevent double-read from the same tap
    time.sleep(1.0)
    return True


def main() -> int:
    """NFCタイムカード監視プログラムのメイン処理。

    NFCリーダーを使って継続的にタグを監視します。
    タグがタッチされると、on_connect コールバック関数が自動的に呼び出されます。

    動作の流れ:
    1. clf.connect() でNFCリーダーがタグを待機
    2. タグがタッチされる
    3. nfcpyライブラリが自動的に on_connect(tag) を呼び出す
    4. on_connect 内で打刻処理を実行
    5. on_connect が True を返すと次のタグを待ち続ける

    終了方法:
    - Ctrl+C: clf.connect() が False を返し、正常終了

    Returns:
        int: 終了コード (0=正常終了, 1=エラー)
    """
    print("NFC watcher starting... (Ctrl+C to exit)")
    try:
        with nfc.ContactlessFrontend("usb") as clf:
            while True:
                clf.connect(rdwr={"on-connect": on_connect})
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except Exception as e:
        print(f"[ERROR] NFC frontend: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
