from __future__ import annotations

from src.common.executor import SingleThreadCommandExecutor
from src.service.seat_reservation_demo_service import SeatReservationDemoService
from src.ttl.policy import ManualClock


def test_run_demo_reserves_only_up_to_seat_limit() -> None:
    executor = SingleThreadCommandExecutor()
    service = SeatReservationDemoService(command_executor=executor, clock=ManualClock())

    try:
        result = service.run_demo(seat_limit=50, request_count=100)
    finally:
        executor.shutdown()

    assert result["scenario"] == "seatReservation"
    assert result["seatLimit"] == 50
    assert result["requestCount"] == 100
    assert result["reservedCount"] == 50
    assert result["soldOutCount"] == 50
    assert result["serialExecutor"] is True
    assert len(result["timeline"]) == 100

    reserved = [item for item in result["timeline"] if item["result"] == "reserved"]
    sold_out = [item for item in result["timeline"] if item["result"] == "soldOut"]

    assert len(reserved) == 50
    assert len(sold_out) == 50
    assert sorted(item["seatNumber"] for item in reserved) == list(range(1, 51))
    assert all(item["seatNumber"] is None for item in sold_out)
    assert [item["queueOrder"] for item in result["timeline"]] == list(range(1, 101))


def test_run_demo_timeline_is_serialized_by_queue_order() -> None:
    executor = SingleThreadCommandExecutor()
    service = SeatReservationDemoService(command_executor=executor, clock=ManualClock())

    try:
        result = service.run_demo(seat_limit=3, request_count=6)
    finally:
        executor.shutdown()

    assert [item["queueOrder"] for item in result["timeline"]] == [1, 2, 3, 4, 5, 6]
    assert [item["result"] for item in result["timeline"]] == [
        "reserved",
        "reserved",
        "reserved",
        "soldOut",
        "soldOut",
        "soldOut",
    ]

    for item in result["timeline"]:
        assert item["startedOffsetMs"] >= 0
        assert item["endedOffsetMs"] >= item["startedOffsetMs"]
        assert item["durationMs"] >= 0
