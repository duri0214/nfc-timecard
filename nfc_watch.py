from __future__ import annotations

import sys
import time
from datetime import datetime

import nfc

from app.domain import make_employee_id_from_tag_identifier, is_likely_my_number_card
from app import storage_csv as store


def on_connect(tag) -> bool:
    try:
        if not is_likely_my_number_card(tag):
            print(f"[WARN] Non-MyNumber tag ignored: {type(tag).__name__}")
            return True  # keep waiting for the next tag

        # Many tags expose 'identifier' as bytes
        identifier = getattr(tag, "identifier", None)
        if not identifier:
            print("[WARN] Tag has no identifier; ignored")
            return True

        emp_id = make_employee_id_from_tag_identifier(identifier)
        wr = store.punch(emp_id)
        state = (
            "clock-in" if wr.clock_in and not wr.clock_out else
            "clock-out" if wr.clock_in and wr.clock_out else "updated"
        )
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
