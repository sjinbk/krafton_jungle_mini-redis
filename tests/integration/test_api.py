from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Event, Lock, Thread
from time import perf_counter, sleep
from typing import Any

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.common.config import Settings
from src.common.seed_data import DEFAULT_DUMMY_ITEMS
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


SEEDED_SAMPLE_ITEM_COUNT = sum(1 for item in DEFAULT_DUMMY_ITEMS if item["key"] == "sample")


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

    def fetch_items(self, key: str) -> list[dict[str, str]]:
        if key in self._blocked_keys:
            self._entered[key].set()
            released = self._release[key].wait(timeout=2)
            if not released:
                raise TimeoutError(f"Timed out waiting to release key: {key}")
        return list(self._items_by_key.get(key, []))

    def wait_until_entered(self, key: str, timeout: float = 1.0) -> bool:
        return self._entered[key].wait(timeout=timeout)

    def release_key(self, key: str) -> None:
        self._release[key].set()


def _build_test_app(
    *,
    store: InMemoryStore,
    origin_repository: BlockingOriginRepository,
):
    return create_app(
        settings=Settings(
            mongo_uri="mongodb://127.0.0.1:27017",
            mongo_db="mini_redis_test",
            mongo_collection="dummy_items",
            default_cache_ttl_seconds=15,
        ),
        store=store,
        clock=ManualClock(),
        origin_repository=origin_repository,
    )


def _start_request(
    client: TestClient,
    method: str,
    path: str,
    **kwargs: Any,
) -> tuple[Thread, dict[str, Any]]:
    outcome: dict[str, Any] = {"response": None, "error": None}

    def runner() -> None:
        try:
            outcome["response"] = client.request(method, path, **kwargs)
        except Exception as exc:
            outcome["error"] = exc

    thread = Thread(target=runner)
    thread.start()
    return thread, outcome


def _join_response(thread: Thread, outcome: dict[str, Any]) -> Any:
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert outcome["error"] is None
    return outcome["response"]


def test_kv_create_get_delete_flow(integration_app) -> None:
    with TestClient(integration_app) as client:
        create_response = client.post(
            "/kv",
            json={"key": "sample", "value": {"status": "ready"}},
        )
        get_response = client.get("/kv/sample")
        delete_response = client.delete("/kv/sample")
        missing_response = client.get("/kv/sample")

    assert create_response.status_code == 201
    assert create_response.json()["data"] == {
        "key": "sample",
        "value": {"status": "ready"},
    }
    assert get_response.status_code == 200
    assert delete_response.status_code == 200
    assert delete_response.json()["data"] == {
        "key": "sample",
        "deleted": True,
    }
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "KEY_NOT_FOUND"


def test_kv_expire_and_ttl_flow(integration_app) -> None:
    with TestClient(integration_app) as client:
        client.post("/kv", json={"key": "ttl-key", "value": "cached"})
        expire_response = client.post("/kv/ttl-key/expire", json={"ttlSeconds": 5})
        ttl_response = client.get("/kv/ttl-key/ttl")

        integration_app.state.clock.advance(seconds=5)
        expired_response = client.get("/kv/ttl-key")
        expired_ttl_response = client.get("/kv/ttl-key/ttl")

    assert expire_response.status_code == 200
    assert expire_response.json()["data"]["hasTtl"] is True
    assert ttl_response.status_code == 200
    assert ttl_response.json()["data"] == {
        "key": "ttl-key",
        "hasTtl": True,
        "ttlSecondsRemaining": 5,
    }
    assert expired_response.status_code == 404
    assert expired_ttl_response.status_code == 404


def test_demo_cache_flow_uses_origin_then_cache_then_origin_after_expiry(integration_app) -> None:
    with TestClient(integration_app) as client:
        first_response = client.get("/demo/data-cache", params={"key": "sample"})
        second_response = client.get("/demo/data-cache", params={"key": "sample"})

        integration_app.state.clock.advance(seconds=16)
        third_response = client.get("/demo/data-cache", params={"key": "sample"})

    assert first_response.status_code == 200
    assert first_response.json()["data"]["source"] == "origin"
    assert len(first_response.json()["data"]["items"]) == SEEDED_SAMPLE_ITEM_COUNT

    assert second_response.status_code == 200
    assert second_response.json()["data"]["source"] == "cache"
    assert second_response.json()["data"]["ttlSecondsRemaining"] is not None

    assert third_response.status_code == 200
    assert third_response.json()["data"]["source"] == "origin"


def test_demo_cache_empty_result_is_not_cached(integration_app) -> None:
    with TestClient(integration_app) as client:
        first_response = client.get("/demo/data-cache", params={"key": "not-seeded"})
        second_response = client.get("/demo/data-cache", params={"key": "not-seeded"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["data"]["items"] == []
    assert second_response.json()["data"]["items"] == []
    assert first_response.json()["data"]["source"] == "origin"
    assert second_response.json()["data"]["source"] == "origin"


def test_invalid_requests_return_400(integration_app) -> None:
    with TestClient(integration_app) as client:
        invalid_key_response = client.post("/kv", json={"key": "", "value": "bad"})
        invalid_ttl_response = client.post("/kv/ttl-key/expire", json={"ttlSeconds": 0})
        missing_query_response = client.get("/demo/data-cache")

    assert invalid_key_response.status_code == 400
    assert invalid_key_response.json()["error"]["code"] == "INVALID_KEY"
    assert invalid_ttl_response.status_code == 400
    assert invalid_ttl_response.json()["error"]["code"] == "INVALID_TTL"
    assert missing_query_response.status_code == 400


def test_cache_compare_performance_api_returns_expected_metrics(integration_app) -> None:
    with TestClient(integration_app) as client:
        response = client.post("/demo/performance/cache-compare")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["scenario"] == "cacheCompare"
    assert data["key"] == "sample"
    assert data["iterations"] == 20
    assert data["originType"] == "mongodb"
    assert data["measuredAt"]

    for timing_key in ("apiTiming", "serviceTiming"):
        timing = data[timing_key]
        assert timing["coldAvgMs"] >= 0
        assert timing["warmAvgMs"] >= 0
        assert timing["savedMs"] is not None
        assert timing["speedupRatio"] is not None


def test_cache_compare_performance_api_accepts_custom_input(integration_app) -> None:
    with TestClient(integration_app) as client:
        response = client.post(
            "/demo/performance/cache-compare",
            json={"key": "alpha", "iterations": 3},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["key"] == "alpha"
    assert data["iterations"] == 3


def test_concurrency_burst_api_supports_all_scenarios(integration_app) -> None:
    scenarios = [
        ("sameKeyKvGetBurst", {"scenario": "sameKeyKvGetBurst", "count": 4, "key": "sample"}),
        ("differentKeyKvGetBurst", {"scenario": "differentKeyKvGetBurst", "count": 4}),
        ("demoCacheGetBurst", {"scenario": "demoCacheGetBurst", "count": 4, "key": "sample"}),
    ]

    with TestClient(integration_app) as client:
        for expected_scenario, payload in scenarios:
            response = client.post("/demo/performance/concurrency-burst", json=payload)
            assert response.status_code == 200

            data = response.json()["data"]
            assert data["scenario"] == expected_scenario
            assert data["count"] == 4
            assert data["measuredAt"]

            for timing_key in ("apiTiming", "serviceTiming"):
                timing = data[timing_key]
                assert timing["totalElapsedMs"] >= 0
                assert timing["avgMs"] >= 0
                assert timing["p95Ms"] >= 0
                assert timing["maxMs"] >= 0
                assert timing["throughputRps"] is not None
                assert timing["successCount"] == 4
                assert timing["errorCount"] == 0
                assert len(timing["timeline"]) == 4

            if expected_scenario == "demoCacheGetBurst":
                for timing_key in ("apiTiming", "serviceTiming"):
                    assert {item["source"] for item in data[timing_key]["timeline"]} == {"cache"}


def test_performance_apis_return_expected_validation_errors(integration_app) -> None:
    with TestClient(integration_app) as client:
        invalid_iterations = client.post(
            "/demo/performance/cache-compare",
            json={"iterations": 0},
        )
        invalid_count = client.post(
            "/demo/performance/concurrency-burst",
            json={"scenario": "sameKeyKvGetBurst", "count": 0, "key": "sample"},
        )
        invalid_scenario = client.post(
            "/demo/performance/concurrency-burst",
            json={"scenario": "unknownScenario", "count": 2, "key": "sample"},
        )

    assert invalid_iterations.status_code == 400
    assert invalid_iterations.json()["error"]["code"] == "INVALID_ITERATIONS"
    assert invalid_count.status_code == 400
    assert invalid_count.json()["error"]["code"] == "INVALID_BURST_COUNT"
    assert invalid_scenario.status_code == 400
    assert invalid_scenario.json()["error"]["code"] == "INVALID_SCENARIO"


def test_performance_apis_return_not_found_for_missing_benchmark_data(integration_app) -> None:
    with TestClient(integration_app) as client:
        cache_compare_response = client.post(
            "/demo/performance/cache-compare",
            json={"key": "not-seeded", "iterations": 2},
        )
        concurrency_response = client.post(
            "/demo/performance/concurrency-burst",
            json={"scenario": "demoCacheGetBurst", "count": 2, "key": "not-seeded"},
        )

    assert cache_compare_response.status_code == 404
    assert cache_compare_response.json()["error"]["code"] == "BENCHMARK_DATA_NOT_FOUND"
    assert concurrency_response.status_code == 404
    assert concurrency_response.json()["error"]["code"] == "BENCHMARK_DATA_NOT_FOUND"


def test_concurrent_kv_requests_are_globally_serialized() -> None:
    store = BlockingObservedStore({"alpha"})
    app = _build_test_app(
        store=store,
        origin_repository=BlockingOriginRepository({}, set()),
    )

    with TestClient(app) as client:
        first_thread, first_outcome = _start_request(
            client,
            "POST",
            "/kv",
            json={"key": "alpha", "value": "one"},
        )
        assert store.wait_until_entered("alpha")

        second_thread, second_outcome = _start_request(
            client,
            "POST",
            "/kv",
            json={"key": "beta", "value": "two"},
        )
        sleep(0.1)

        assert len(store.events_for("beta", "set-start")) == 0

        store.release_key("alpha")
        first_response = _join_response(first_thread, first_outcome)
        second_response = _join_response(second_thread, second_outcome)

    alpha_end = store.events_for("alpha", "set-end")[0]
    beta_start = store.events_for("beta", "set-start")[0]

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert beta_start.timestamp >= alpha_end.timestamp


def test_kv_and_demo_cache_requests_share_the_same_serial_executor() -> None:
    store = BlockingObservedStore(set())
    origin_repository = BlockingOriginRepository(
        {"sample": [{"id": "sample-1", "value": "payload"}]},
        {"sample"},
    )
    app = _build_test_app(store=store, origin_repository=origin_repository)

    with TestClient(app) as client:
        first_thread, first_outcome = _start_request(
            client,
            "GET",
            "/demo/data-cache",
            params={"key": "sample"},
        )
        assert origin_repository.wait_until_entered("sample")

        second_thread, second_outcome = _start_request(
            client,
            "POST",
            "/kv",
            json={"key": "alpha", "value": "one"},
        )
        sleep(0.1)

        assert len(store.events_for("alpha", "set-start")) == 0

        origin_repository.release_key("sample")
        first_response = _join_response(first_thread, first_outcome)
        second_response = _join_response(second_thread, second_outcome)

    cache_write_end = store.events_for("data:sample", "set-end")[0]
    alpha_write_start = store.events_for("alpha", "set-start")[0]

    assert first_response.status_code == 200
    assert first_response.json()["data"]["source"] == "origin"
    assert second_response.status_code == 201
    assert alpha_write_start.timestamp >= cache_write_end.timestamp
