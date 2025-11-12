from __future__ import annotations

import sys
import time
from datetime import datetime

import nfc

from app.domain import make_employee_id_from_tag_identifier, is_acceptable_card
from app import storage_csv as store


def on_connect(tag) -> bool:
    try:
        if not is_acceptable_card(tag):
            print(f"[WARN] Unsupported tag type ignored: {type(tag).__name__}")
            return True  # keep waiting for the next tag

        # Many tags expose 'identifier' as bytes
        identifier = getattr(tag, "identifier", None)
        if not identifier:
            print("[WARN] Tag has no identifier; ignored")
            return True

        emp_id = make_employee_id_from_tag_identifier(identifier)

        # Get the current state before punch
        rows = store._load_all()
        today = datetime.now().date()
        existing_idx = store._find_row_index(rows, today, emp_id)
        was_complete = False
        if existing_idx is not None:
            r = rows[existing_idx]
            was_complete = bool(r.get("clock_in") and r.get("clock_out"))

        wr = store.punch(emp_id)

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
    except Exception as e:
        print(f"[ERROR] on_connect failed: {e}")
        return True


def main() -> int:
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
