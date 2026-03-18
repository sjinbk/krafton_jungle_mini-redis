from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from threading import Lock, Thread
from time import perf_counter, sleep
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.executor import SingleThreadCommandExecutor
from src.service.demo_cache_service import DemoCacheService
from src.service.kv_service import KeyValueService
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


@dataclass(slots=True)
class TimelineEvent:
    label: str
    timestamp: float


class Timeline:
    def __init__(self) -> None:
        self._events: list[TimelineEvent] = []
        self._lock = Lock()

    def record(self, label: str) -> None:
        with self._lock:
            self._events.append(TimelineEvent(label=label, timestamp=perf_counter()))

    def snapshot(self) -> list[TimelineEvent]:
        with self._lock:
            return list(self._events)


class LoggedDelayedStore(InMemoryStore):
    def __init__(self, *, timeline: Timeline, delay_by_key: dict[str, float]) -> None:
        super().__init__()
        self._timeline = timeline
        self._delay_by_key = delay_by_key

    def set(self, key: str, value: Any, expires_at: Any = None) -> None:
        self._timeline.record(f"store:set-start:{key}")
        sleep(self._delay_by_key.get(key, 0.0))
        super().set(key, value, expires_at)
        self._timeline.record(f"store:set-end:{key}")


class DelayedOriginRepository:
    def __init__(
        self,
        *,
        timeline: Timeline,
        delay_by_key: dict[str, float],
        items_by_key: dict[str, list[dict[str, str]]],
    ) -> None:
        self._timeline = timeline
        self._delay_by_key = delay_by_key
        self._items_by_key = items_by_key

    def fetch_items(self, key: str) -> list[dict[str, str]]:
        self._timeline.record(f"origin:fetch-start:{key}")
        sleep(self._delay_by_key.get(key, 0.0))
        self._timeline.record(f"origin:fetch-end:{key}")
        return list(self._items_by_key.get(key, []))


def build_kv_service(
    *,
    store: InMemoryStore,
    executor: SingleThreadCommandExecutor,
) -> KeyValueService:
    return KeyValueService(
        store=store,
        clock=ManualClock(),
        command_executor=executor,
    )


def build_demo_service(
    *,
    store: InMemoryStore,
    executor: SingleThreadCommandExecutor,
    origin_repository: DelayedOriginRepository,
) -> DemoCacheService:
    return DemoCacheService(
        store=store,
        clock=ManualClock(),
        command_executor=executor,
        origin_repository=origin_repository,
        default_ttl_seconds=15,
    )


def run_in_thread(target: Any, *args: Any, **kwargs: Any) -> tuple[Thread, dict[str, Any]]:
    outcome: dict[str, Any] = {"error": None}

    def runner() -> None:
        try:
            target(*args, **kwargs)
        except Exception as exc:
            outcome["error"] = exc

    thread = Thread(target=runner)
    thread.start()
    return thread, outcome


def join_thread(thread: Thread, outcome: dict[str, Any]) -> None:
    thread.join()
    if outcome["error"] is not None:
        raise outcome["error"]


def print_timeline(*, title: str, started_at: float, ended_at: float, timeline: Timeline) -> None:
    print(f"=== {title} ===")
    for index, event in enumerate(sorted(timeline.snapshot(), key=lambda item: item.timestamp), start=1):
        print(f"{index}. {event.label} at {event.timestamp - started_at:.3f}s")
    print(f"total elapsed={ended_at - started_at:.3f}s\n")


def run_same_key_demo() -> None:
    executor = SingleThreadCommandExecutor()
    timeline = Timeline()
    store = LoggedDelayedStore(timeline=timeline, delay_by_key={"shared": 0.4})
    service = build_kv_service(store=store, executor=executor)

    started_at = perf_counter()
    first_thread, first_outcome = run_in_thread(service.set_value, key="shared", value="first")
    second_thread, second_outcome = run_in_thread(service.set_value, key="shared", value="second")
    join_thread(first_thread, first_outcome)
    join_thread(second_thread, second_outcome)
    ended_at = perf_counter()

    try:
        print_timeline(
            title="Same Key Serialization",
            started_at=started_at,
            ended_at=ended_at,
            timeline=timeline,
        )
        print("expected: the second command starts only after the first command fully finishes\n")
    finally:
        executor.shutdown()


def run_different_key_demo() -> None:
    executor = SingleThreadCommandExecutor()
    timeline = Timeline()
    store = LoggedDelayedStore(timeline=timeline, delay_by_key={"alpha": 0.4, "beta": 0.4})
    service = build_kv_service(store=store, executor=executor)

    started_at = perf_counter()
    first_thread, first_outcome = run_in_thread(service.set_value, key="alpha", value="one")
    second_thread, second_outcome = run_in_thread(service.set_value, key="beta", value="two")
    join_thread(first_thread, first_outcome)
    join_thread(second_thread, second_outcome)
    ended_at = perf_counter()

    try:
        print_timeline(
            title="Different Key Serialization",
            started_at=started_at,
            ended_at=ended_at,
            timeline=timeline,
        )
        print("expected: different keys also wait in line, so total time is close to two delay windows\n")
    finally:
        executor.shutdown()


def run_cross_service_demo() -> None:
    executor = SingleThreadCommandExecutor()
    timeline = Timeline()
    store = LoggedDelayedStore(
        timeline=timeline,
        delay_by_key={"data:sample": 0.2, "alpha": 0.2},
    )
    origin_repository = DelayedOriginRepository(
        timeline=timeline,
        delay_by_key={"sample": 0.4},
        items_by_key={"sample": [{"id": "sample-1", "value": "payload"}]},
    )
    kv_service = build_kv_service(store=store, executor=executor)
    demo_service = build_demo_service(
        store=store,
        executor=executor,
        origin_repository=origin_repository,
    )

    started_at = perf_counter()
    first_thread, first_outcome = run_in_thread(demo_service.get_data, "sample")
    second_thread, second_outcome = run_in_thread(kv_service.set_value, key="alpha", value="one")
    join_thread(first_thread, first_outcome)
    join_thread(second_thread, second_outcome)
    ended_at = perf_counter()

    try:
        print_timeline(
            title="Cross Service Serialization",
            started_at=started_at,
            ended_at=ended_at,
            timeline=timeline,
        )
        print("expected: demo cache and KV commands also share one serial execution lane\n")
    finally:
        executor.shutdown()


if __name__ == "__main__":
    run_same_key_demo()
    run_different_key_demo()
    run_cross_service_demo()
