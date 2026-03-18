from __future__ import annotations

from contextlib import contextmanager
from statistics import mean
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from fastapi.testclient import TestClient
from pymongo import MongoClient

from src.common.config import Settings
from src.common.errors import benchmark_data_not_found
from src.common.executor import SingleThreadCommandExecutor
from src.common.seed_data import DEFAULT_DUMMY_ITEMS
from src.common.validation import validate_iterations, validate_key
from src.store.in_memory import InMemoryStore
from src.ttl.policy import SystemClock, format_utc_timestamp


def round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 3)


def build_cache_compare_metrics(*, cold_durations: list[float], warm_durations: list[float]) -> dict[str, float | None]:
    cold_avg = mean(cold_durations)
    warm_avg = mean(warm_durations)
    saved = cold_avg - warm_avg
    speedup = None if warm_avg == 0 else cold_avg / warm_avg
    return {
        "coldAvgMs": round_metric(cold_avg),
        "warmAvgMs": round_metric(warm_avg),
        "savedMs": round_metric(saved),
        "speedupRatio": round_metric(speedup),
    }


class PerformanceBenchmarkService:
    def __init__(
        self,
        *,
        settings: Settings,
        app_factory: Callable[..., Any],
    ) -> None:
        self._settings = settings
        self._app_factory = app_factory

    def compare_cache(self, *, key: str = "sample", iterations: int = 20) -> dict[str, Any]:
        validate_key(key)
        validate_iterations(iterations)

        api_timing = self._measure_cache_compare_api(key=key, iterations=iterations)
        service_timing = self._measure_cache_compare_service(key=key, iterations=iterations)
        return {
            "scenario": "cacheCompare",
            "key": key,
            "iterations": iterations,
            "originType": "mongodb",
            "measuredAt": format_utc_timestamp(SystemClock().now()),
            "apiTiming": api_timing,
            "serviceTiming": service_timing,
        }

    def _measure_cache_compare_api(self, *, key: str, iterations: int) -> dict[str, float | None]:
        with self._benchmark_context() as app:
            with TestClient(app) as client:
                cold_durations = self._measure_cold_api_requests(client=client, key=key, iterations=iterations)
                warm_durations = self._measure_warm_api_requests(client=client, key=key, iterations=iterations)
        return build_cache_compare_metrics(cold_durations=cold_durations, warm_durations=warm_durations)

    def _measure_cache_compare_service(self, *, key: str, iterations: int) -> dict[str, float | None]:
        with self._benchmark_context() as app:
            service = app.state.demo_cache_service
            cold_durations = self._measure_cold_service_requests(service=service, key=key, iterations=iterations)
            warm_durations = self._measure_warm_service_requests(service=service, key=key, iterations=iterations)
        return build_cache_compare_metrics(cold_durations=cold_durations, warm_durations=warm_durations)

    def _measure_cold_api_requests(self, *, client: TestClient, key: str, iterations: int) -> list[float]:
        durations: list[float] = []
        for _ in range(iterations):
            client.app.state.demo_cache_service.clear_cache_key(key)
            started_at = perf_counter()
            response = client.get("/demo/data-cache", params={"key": key})
            ended_at = perf_counter()
            data = self._extract_demo_cache_data(response.status_code, response.json())
            if data["source"] != "origin":
                raise RuntimeError("Cold cache benchmark expected source=origin")
            durations.append((ended_at - started_at) * 1_000)
        return durations

    def _measure_warm_api_requests(self, *, client: TestClient, key: str, iterations: int) -> list[float]:
        durations: list[float] = []
        client.app.state.demo_cache_service.clear_cache_key(key)
        prime_response = client.get("/demo/data-cache", params={"key": key})
        prime_data = self._extract_demo_cache_data(prime_response.status_code, prime_response.json())
        if prime_data["source"] != "origin":
            raise RuntimeError("Warm cache benchmark expected priming source=origin")

        for _ in range(iterations):
            started_at = perf_counter()
            response = client.get("/demo/data-cache", params={"key": key})
            ended_at = perf_counter()
            data = self._extract_demo_cache_data(response.status_code, response.json())
            if data["source"] != "cache":
                raise RuntimeError("Warm cache benchmark expected source=cache")
            durations.append((ended_at - started_at) * 1_000)
        return durations

    def _measure_cold_service_requests(self, *, service: Any, key: str, iterations: int) -> list[float]:
        durations: list[float] = []
        for _ in range(iterations):
            service.clear_cache_key(key)
            started_at = perf_counter()
            data = service.get_data(key)
            ended_at = perf_counter()
            self._ensure_demo_cache_payload(data)
            if data["source"] != "origin":
                raise RuntimeError("Cold cache benchmark expected source=origin")
            durations.append((ended_at - started_at) * 1_000)
        return durations

    def _measure_warm_service_requests(self, *, service: Any, key: str, iterations: int) -> list[float]:
        durations: list[float] = []
        service.clear_cache_key(key)
        prime_data = service.get_data(key)
        self._ensure_demo_cache_payload(prime_data)
        if prime_data["source"] != "origin":
            raise RuntimeError("Warm cache benchmark expected priming source=origin")

        for _ in range(iterations):
            started_at = perf_counter()
            data = service.get_data(key)
            ended_at = perf_counter()
            self._ensure_demo_cache_payload(data)
            if data["source"] != "cache":
                raise RuntimeError("Warm cache benchmark expected source=cache")
            durations.append((ended_at - started_at) * 1_000)
        return durations

    def _extract_demo_cache_data(self, status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
        if status_code != 200:
            raise RuntimeError(payload)
        data = payload["data"]
        self._ensure_demo_cache_payload(data)
        return data

    @staticmethod
    def _ensure_demo_cache_payload(payload: dict[str, Any]) -> None:
        if payload["items"] == []:
            raise benchmark_data_not_found()

    @contextmanager
    def _benchmark_context(self):
        database_name = f"mini_redis_bm_{uuid4().hex[:12]}"
        mongo_client = MongoClient(
            self._settings.mongo_uri,
            tz_aware=True,
            serverSelectionTimeoutMS=1_000,
        )
        command_executor = SingleThreadCommandExecutor(thread_name="mini-redis-benchmark-executor")
        benchmark_settings = Settings(
            mongo_uri=self._settings.mongo_uri,
            mongo_db=database_name,
            mongo_collection=self._settings.mongo_collection,
            default_cache_ttl_seconds=self._settings.default_cache_ttl_seconds,
        )
        collection = mongo_client[database_name][self._settings.mongo_collection]
        collection.insert_many(DEFAULT_DUMMY_ITEMS)
        app = self._app_factory(
            settings=benchmark_settings,
            store=InMemoryStore(),
            clock=SystemClock(),
            mongo_client=mongo_client,
            command_executor=command_executor,
            include_performance_routes=False,
        )

        try:
            yield app
        finally:
            command_executor.shutdown()
            mongo_client.drop_database(database_name)
            mongo_client.close()
