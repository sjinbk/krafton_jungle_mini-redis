from __future__ import annotations

from dataclasses import dataclass
from threading import Barrier, Lock, Thread
from time import perf_counter
from typing import Any

from src.common.executor import SingleThreadCommandExecutor
from src.common.validation import validate_request_count, validate_seat_limit


def round_metric(value: float) -> float:
    return round(value, 3)


@dataclass(slots=True)
class ReservationOutcome:
    queue_order: int
    result: str
    seat_number: int | None
    status_code: int


@dataclass(slots=True)
class ReservationMeasurement:
    request_id: str
    started_at: float
    ended_at: float
    queue_order: int
    result: str
    seat_number: int | None
    status_code: int

    @property
    def duration_ms(self) -> float:
        return (self.ended_at - self.started_at) * 1_000


class SeatReservationDemoService:
    def __init__(
        self,
        *,
        command_executor: SingleThreadCommandExecutor,
        clock: Any,
    ) -> None:
        self._command_executor = command_executor
        self._clock = clock

    def run_demo(
        self,
        *,
        seat_limit: int = 50,
        request_count: int = 100,
    ) -> dict[str, Any]:
        validate_seat_limit(seat_limit)
        validate_request_count(request_count)

        reserved = 0
        queue_order = 0
        state_lock = Lock()
        barrier = Barrier(request_count + 1)
        measurements: list[ReservationMeasurement | None] = [None] * request_count
        unexpected_errors: list[Exception] = []
        error_lock = Lock()
        threads: list[Thread] = []

        def reserve_one() -> ReservationOutcome:
            nonlocal reserved
            nonlocal queue_order
            with state_lock:
                queue_order += 1
                current_order = queue_order
                if reserved < seat_limit:
                    reserved += 1
                    return ReservationOutcome(
                        queue_order=current_order,
                        result="reserved",
                        seat_number=reserved,
                        status_code=200,
                    )

                return ReservationOutcome(
                    queue_order=current_order,
                    result="soldOut",
                    seat_number=None,
                    status_code=409,
                )

        def runner(index: int) -> None:
            barrier.wait()
            started_at = perf_counter()
            try:
                outcome = self._command_executor.run(reserve_one)
            except Exception as exc:
                with error_lock:
                    unexpected_errors.append(exc)
                ended_at = perf_counter()
                measurements[index] = ReservationMeasurement(
                    request_id=f"request-{index + 1}",
                    started_at=started_at,
                    ended_at=ended_at,
                    queue_order=index + 1,
                    result="error",
                    seat_number=None,
                    status_code=500,
                )
                return

            ended_at = perf_counter()
            measurements[index] = ReservationMeasurement(
                request_id=f"request-{index + 1}",
                started_at=started_at,
                ended_at=ended_at,
                queue_order=outcome.queue_order,
                result=outcome.result,
                seat_number=outcome.seat_number,
                status_code=outcome.status_code,
            )

        for index in range(request_count):
            thread = Thread(target=runner, args=(index,), daemon=True)
            thread.start()
            threads.append(thread)

        started_at = perf_counter()
        barrier.wait()

        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Seat reservation demo thread did not finish in time")

        if unexpected_errors:
            raise unexpected_errors[0]

        ordered = sorted(
            [item for item in measurements if item is not None],
            key=lambda item: item.queue_order,
        )
        ended_at = max(item.ended_at for item in ordered) if ordered else started_at

        timeline = [
            {
                "requestId": item.request_id,
                "queueOrder": item.queue_order,
                "startedOffsetMs": round_metric((item.started_at - started_at) * 1_000),
                "endedOffsetMs": round_metric((item.ended_at - started_at) * 1_000),
                "durationMs": round_metric(item.duration_ms),
                "result": item.result,
                "seatNumber": item.seat_number,
                "statusCode": item.status_code,
            }
            for item in ordered
        ]

        return {
            "scenario": "seatReservation",
            "seatLimit": seat_limit,
            "requestCount": request_count,
            "reservedCount": sum(1 for item in ordered if item.result == "reserved"),
            "soldOutCount": sum(1 for item in ordered if item.result == "soldOut"),
            "serialExecutor": True,
            "totalElapsedMs": round_metric((ended_at - started_at) * 1_000),
            "timeline": timeline,
        }
