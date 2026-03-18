from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Event, Lock, Thread
from time import perf_counter, sleep
from typing import Any

from src.common.executor import SingleThreadCommandExecutor
from src.service.demo_cache_service import DemoCacheService
from src.service.kv_service import KeyValueService
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


@dataclass(slots=True)
class TimelineEvent:
    phase: str
    key: str
    timestamp: float


class BlockingObservedStore(InMemoryStore):
    def __init__(self, blocked_keys: set[str]) -> None:
        super().__init__()
        self._blocked_keys = blocked_keys
        self._entered: dict[str, Event] = defaultdict(Event)
        self._release: dict[str, Event] = defaultdict(Event)
        self._events: list[TimelineEvent] = []
        self._events_lock = Lock()

    def set(self, key: str, value: Any, expires_at: Any = None) -> None:
        self._record("set-start", key)
        if key in self._blocked_keys:
            self._entered[key].set()
            released = self._release[key].wait(timeout=2)
            if not released:
                raise TimeoutError(f"Timed out waiting to release key: {key}")
        super().set(key, value, expires_at)
        self._record("set-end", key)

    def wait_until_entered(self, key: str, timeout: float = 1.0) -> bool:
        return self._entered[key].wait(timeout=timeout)

    def release_key(self, key: str) -> None:
        self._release[key].set()

    def events_for(self, key: str, phase: str) -> list[TimelineEvent]:
        with self._events_lock:
            return [event for event in self._events if event.key == key and event.phase == phase]

    def _record(self, phase: str, key: str) -> None:
        with self._events_lock:
            self._events.append(
                TimelineEvent(
                    phase=phase,
                    key=key,
                    timestamp=perf_counter(),
                )
            )


class BlockingOriginRepository:
    def __init__(
        self,
        items_by_key: dict[str, list[dict[str, str]]],
        blocked_keys: set[str],
    ) -> None:
        self._items_by_key = items_by_key
        self._blocked_keys = blocked_keys
        self._entered: dict[str, Event] = defaultdict(Event)
        self._release: dict[str, Event] = defaultdict(Event)
        self.calls: list[str] = []
        self.events: list[TimelineEvent] = []
        self._events_lock = Lock()

    def fetch_items(self, key: str) -> list[dict[str, str]]:
        self.calls.append(key)
        self._record("origin-start", key)
        if key in self._blocked_keys:
            self._entered[key].set()
            released = self._release[key].wait(timeout=2)
            if not released:
                raise TimeoutError(f"Timed out waiting to release key: {key}")
        self._record("origin-end", key)
        return list(self._items_by_key.get(key, []))

    def wait_until_entered(self, key: str, timeout: float = 1.0) -> bool:
        return self._entered[key].wait(timeout=timeout)

    def release_key(self, key: str) -> None:
        self._release[key].set()

    def events_for(self, key: str, phase: str) -> list[TimelineEvent]:
        with self._events_lock:
            return [event for event in self.events if event.key == key and event.phase == phase]

    def _record(self, phase: str, key: str) -> None:
        with self._events_lock:
            self.events.append(
                TimelineEvent(
                    phase=phase,
                    key=key,
                    timestamp=perf_counter(),
                )
            )


def _build_kv_service(
    *,
    store: InMemoryStore,
    executor: SingleThreadCommandExecutor,
) -> KeyValueService:
    return KeyValueService(
        store=store,
        clock=ManualClock(),
        command_executor=executor,
    )


def _build_demo_service(
    *,
    store: InMemoryStore,
    executor: SingleThreadCommandExecutor,
    origin_repository: BlockingOriginRepository,
) -> DemoCacheService:
    return DemoCacheService(
        store=store,
        clock=ManualClock(),
        command_executor=executor,
        origin_repository=origin_repository,
        default_ttl_seconds=15,
    )


def _start_call(target: Any, *args: Any, **kwargs: Any) -> tuple[Thread, dict[str, Any]]:
    outcome: dict[str, Any] = {"result": None, "error": None}

    def runner() -> None:
        try:
            outcome["result"] = target(*args, **kwargs)
        except Exception as exc:
            outcome["error"] = exc

    thread = Thread(target=runner)
    thread.start()
    return thread, outcome


def _join_successfully(thread: Thread, outcome: dict[str, Any]) -> Any:
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert outcome["error"] is None
    return outcome["result"]


def test_same_key_requests_are_serialized() -> None:
    executor = SingleThreadCommandExecutor()
    store = BlockingObservedStore({"shared"})
    service = _build_kv_service(store=store, executor=executor)

    try:
        first_thread, first_outcome = _start_call(service.set_value, key="shared", value="first")
        assert store.wait_until_entered("shared")

        second_thread, second_outcome = _start_call(service.set_value, key="shared", value="second")
        sleep(0.1)

        assert len(store.events_for("shared", "set-start")) == 1

        store.release_key("shared")
        _join_successfully(first_thread, first_outcome)
        _join_successfully(second_thread, second_outcome)

        starts = store.events_for("shared", "set-start")
        ends = store.events_for("shared", "set-end")

        assert len(starts) == 2
        assert len(ends) == 2
        assert starts[1].timestamp >= ends[0].timestamp
        assert service.get_value("shared") == {"key": "shared", "value": "second"}
    finally:
        executor.shutdown()


def test_different_keys_are_also_serialized() -> None:
    executor = SingleThreadCommandExecutor()
    store = BlockingObservedStore({"alpha"})
    service = _build_kv_service(store=store, executor=executor)

    try:
        first_thread, first_outcome = _start_call(service.set_value, key="alpha", value="one")
        assert store.wait_until_entered("alpha")

        second_thread, second_outcome = _start_call(service.set_value, key="beta", value="two")
        sleep(0.1)

        assert len(store.events_for("beta", "set-start")) == 0

        store.release_key("alpha")
        _join_successfully(first_thread, first_outcome)
        _join_successfully(second_thread, second_outcome)

        alpha_end = store.events_for("alpha", "set-end")[0]
        beta_start = store.events_for("beta", "set-start")[0]

        assert beta_start.timestamp >= alpha_end.timestamp
        assert service.get_value("alpha") == {"key": "alpha", "value": "one"}
        assert service.get_value("beta") == {"key": "beta", "value": "two"}
    finally:
        executor.shutdown()


def test_kv_and_demo_cache_share_the_same_serial_executor() -> None:
    executor = SingleThreadCommandExecutor()
    store = BlockingObservedStore(set())
    origin_repository = BlockingOriginRepository(
        {
            "sample": [
                {"id": "sample-1", "value": "payload"},
            ]
        },
        {"sample"},
    )
    kv_service = _build_kv_service(store=store, executor=executor)
    demo_service = _build_demo_service(
        store=store,
        executor=executor,
        origin_repository=origin_repository,
    )

    try:
        demo_thread, demo_outcome = _start_call(demo_service.get_data, "sample")
        assert origin_repository.wait_until_entered("sample")

        kv_thread, kv_outcome = _start_call(kv_service.set_value, key="alpha", value="one")
        sleep(0.1)

        assert len(store.events_for("alpha", "set-start")) == 0

        origin_repository.release_key("sample")
        demo_result = _join_successfully(demo_thread, demo_outcome)
        kv_result = _join_successfully(kv_thread, kv_outcome)

        cache_write_end = store.events_for("data:sample", "set-end")[0]
        kv_write_start = store.events_for("alpha", "set-start")[0]

        assert demo_result["source"] == "origin"
        assert kv_result["data"] == {"key": "alpha", "value": "one"}
        assert kv_write_start.timestamp >= cache_write_end.timestamp
    finally:
        executor.shutdown()
