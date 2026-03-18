from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.executor import SingleThreadCommandExecutor
from src.service.seat_reservation_demo_service import SeatReservationDemoService
from src.ttl.policy import ManualClock


def main() -> None:
    executor = SingleThreadCommandExecutor()
    service = SeatReservationDemoService(command_executor=executor, clock=ManualClock())

    try:
        result = service.run_demo(seat_limit=50, request_count=100)
    finally:
        executor.shutdown()

    preview = result["timeline"][:12]
    print("=== Seat Reservation Demo ===")
    print(f"reservedCount={result['reservedCount']}")
    print(f"soldOutCount={result['soldOutCount']}")
    print(f"serialExecutor={result['serialExecutor']}")
    print("preview:")
    print(json.dumps(preview, indent=2))


if __name__ == "__main__":
    main()
