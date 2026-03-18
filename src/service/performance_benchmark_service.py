from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from math import ceil
from statistics import mean
from threading import Barrier, Lock, Thread
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from fastapi.testclient import TestClient
from pymongo import MongoClient

from src.common.config import Settings
from src.common.errors import AppError, benchmark_data_not_found
from src.common.executor import SingleThreadCommandExecutor
from src.common.seed_data import DEFAULT_DUMMY_ITEMS
from src.common.validation import (
    validate_burst_count,
    validate_iterations,
    validate_key,
    validate_scenario,
)
from src.store.in_memory import InMemoryStore
from src.ttl.policy import SystemClock, format_utc_timestamp


BURST_SCENARIOS = {
    "sameKeyKvGetBurst",
    "differentKeyKvGetBurst",
    "demoCacheGetBurst",
}


@dataclass(slots=True)
class CallOutcome:
    status_code: int
    source: str | None = None


@dataclass(slots=True)
class RequestMeasurement:
    request_id: str
    key: str
    started_at: float
    ended_at: float
    status: str
    status_code: int
    source: str | None

    @property
    def duration_ms(self) -> float:
        return (self.ended_at - self.started_at) * 1_000


@dataclass(slots=True)
class BenchmarkOperation:
    request_id: str
    key: str
    call: Callable[[], CallOutcome]


@dataclass(slots=True)
class BenchmarkContext:
    app: Any
    mongo_client: MongoClient
    database_name: str
    command_executor: SingleThreadCommandExecutor


def round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 3)


def calculate_p95_ms(durations_ms: list[float]) -> float:
    if not durations_ms:
        return 0.0

    ordered = sorted(durations_ms)
    rank = ceil(len(ordered) * 0.95)
    return ordered[rank - 1]


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


def build_burst_metrics(
    *,
    measurements: list[RequestMeasurement],
    started_at: float,
    ended_at: float,
) -> dict[str, Any]:
    ordered = sorted(measurements, key=lambda item: item.started_at)
    durations = [item.duration_ms for item in ordered]
    success_count = sum(1 for item in ordered if item.status == "success")
    total_elapsed_ms = (ended_at - started_at) * 1_000
    throughput = None
    if total_elapsed_ms > 0:
        throughput = success_count / (total_elapsed_ms / 1_000)

    timeline = [
        {
            "requestId": item.request_id,
            "key": item.key,
            "startedOffsetMs": round_metric((item.started_at - started_at) * 1_000),
            "endedOffsetMs": round_metric((item.ended_at - started_at) * 1_000),
            "durationMs": round_metric(item.duration_ms),
            "status": item.status,
            "statusCode": item.status_code,
            "source": item.source,
        }
        for item in ordered
    ]

    return {
        "totalElapsedMs": round_metric(total_elapsed_ms),
        "avgMs": round_metric(mean(durations)),
        "p95Ms": round_metric(calculate_p95_ms(durations)),
        "maxMs": round_metric(max(durations)),
        "throughputRps": round_metric(throughput),
        "successCount": success_count,
        "errorCount": len(ordered) - success_count,
        "timeline": timeline,
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

    def run_concurrency_burst(
        self,
        *,
        scenario: str,
        count: int = 10,
        key: str = "sample",
    ) -> dict[str, Any]:
        validate_scenario(scenario, BURST_SCENARIOS)
        validate_burst_count(count)
        if scenario != "differentKeyKvGetBurst":
            validate_key(key)

        api_timing = self._measure_concurrency_api(scenario=scenario, count=count, key=key)
        service_timing = self._measure_concurrency_service(
            scenario=scenario,
            count=count,
            key=key,
        )
        return {
            "scenario": scenario,
            "count": count,
            "measuredAt": format_utc_timestamp(SystemClock().now()),
            "apiTiming": api_timing,
            "serviceTiming": service_timing,
        }

    def _measure_cache_compare_api(self, *, key: str, iterations: int) -> dict[str, float | None]:
        with self._benchmark_context() as context:
            with TestClient(context.app) as client:
                cold_durations = self._measure_cold_api_requests(client=client, key=key, iterations=iterations)
                warm_durations = self._measure_warm_api_requests(client=client, key=key, iterations=iterations)
        return build_cache_compare_metrics(
            cold_durations=cold_durations,
            warm_durations=warm_durations,
        )

    def _measure_cache_compare_service(self, *, key: str, iterations: int) -> dict[str, float | None]:
        with self._benchmark_context() as context:
            service = context.app.state.demo_cache_service
            cold_durations = self._measure_cold_service_requests(service=service, key=key, iterations=iterations)
            warm_durations = self._measure_warm_service_requests(service=service, key=key, iterations=iterations)
        return build_cache_compare_metrics(
            cold_durations=cold_durations,
            warm_durations=warm_durations,
        )

    def _measure_concurrency_api(self, *, scenario: str, count: int, key: str) -> dict[str, Any]:
        with self._benchmark_context() as context:
            with TestClient(context.app) as client:
                operations = self._build_api_operations(
                    client=client,
                    context=context,
                    scenario=scenario,
                    count=count,
                    key=key,
                )
                metrics = self._run_parallel_operations(operations)

        if scenario == "demoCacheGetBurst":
            self._assert_expected_cache_sources(metrics["timeline"])
        return metrics

    def _measure_concurrency_service(self, *, scenario: str, count: int, key: str) -> dict[str, Any]:
        with self._benchmark_context() as context:
            operations = self._build_service_operations(
                context=context,
                scenario=scenario,
                count=count,
                key=key,
            )
            metrics = self._run_parallel_operations(operations)

        if scenario == "demoCacheGetBurst":
            self._assert_expected_cache_sources(metrics["timeline"])
        return metrics

    def _measure_cold_api_requests(
        self,
        *,
        client: TestClient,
        key: str,
        iterations: int,
    ) -> list[float]:
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

    def _measure_warm_api_requests(
        self,
        *,
        client: TestClient,
        key: str,
        iterations: int,
    ) -> list[float]:
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

    def _measure_cold_service_requests(
        self,
        *,
        service: Any,
        key: str,
        iterations: int,
    ) -> list[float]:
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

    def _measure_warm_service_requests(
        self,
        *,
        service: Any,
        key: str,
        iterations: int,
    ) -> list[float]:
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

    def _build_api_operations(
        self,
        *,
        client: TestClient,
        context: BenchmarkContext,
        scenario: str,
        count: int,
        key: str,
    ) -> list[BenchmarkOperation]:
        if scenario == "sameKeyKvGetBurst":
            context.app.state.kv_service.set_value(key=key, value={"mode": "same-key"})
            return [
                BenchmarkOperation(
                    request_id=f"request-{index + 1}",
                    key=key,
                    call=lambda key=key: self._call_http_get(client, f"/kv/{key}"),
                )
                for index in range(count)
            ]

        if scenario == "differentKeyKvGetBurst":
            keys = [f"burst-{index + 1}" for index in range(count)]
            for entry_key in keys:
                context.app.state.kv_service.set_value(
                    key=entry_key,
                    value={"mode": "different-key", "key": entry_key},
                )
            return [
                BenchmarkOperation(
                    request_id=f"request-{index + 1}",
                    key=entry_key,
                    call=lambda entry_key=entry_key: self._call_http_get(client, f"/kv/{entry_key}"),
                )
                for index, entry_key in enumerate(keys)
            ]

        self._prime_demo_cache(context.app.state.demo_cache_service, key)
        return [
            BenchmarkOperation(
                request_id=f"request-{index + 1}",
                key=key,
                call=lambda key=key: self._call_http_get(
                    client,
                    "/demo/data-cache",
                    params={"key": key},
                ),
            )
            for index in range(count)
        ]

    def _build_service_operations(
        self,
        *,
        context: BenchmarkContext,
        scenario: str,
        count: int,
        key: str,
    ) -> list[BenchmarkOperation]:
        if scenario == "sameKeyKvGetBurst":
            context.app.state.kv_service.set_value(key=key, value={"mode": "same-key"})
            return [
                BenchmarkOperation(
                    request_id=f"request-{index + 1}",
                    key=key,
                    call=lambda key=key: self._call_service_kv_get(context.app.state.kv_service, key),
                )
                for index in range(count)
            ]

        if scenario == "differentKeyKvGetBurst":
            keys = [f"burst-{index + 1}" for index in range(count)]
            for entry_key in keys:
                context.app.state.kv_service.set_value(
                    key=entry_key,
                    value={"mode": "different-key", "key": entry_key},
                )
            return [
                BenchmarkOperation(
                    request_id=f"request-{index + 1}",
                    key=entry_key,
                    call=lambda entry_key=entry_key: self._call_service_kv_get(
                        context.app.state.kv_service,
                        entry_key,
                    ),
                )
                for index, entry_key in enumerate(keys)
            ]

        self._prime_demo_cache(context.app.state.demo_cache_service, key)
        return [
            BenchmarkOperation(
                request_id=f"request-{index + 1}",
                key=key,
                call=lambda key=key: self._call_service_demo_cache_get(
                    context.app.state.demo_cache_service,
                    key,
                ),
            )
            for index in range(count)
        ]

    @staticmethod
    def _call_http_get(
        client: TestClient,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> CallOutcome:
        response = client.get(path, params=params)
        payload = response.json()
        source = None
        if response.status_code == 200 and isinstance(payload.get("data"), dict):
            source = payload["data"].get("source")
        return CallOutcome(status_code=response.status_code, source=source)

    @staticmethod
    def _call_service_kv_get(service: Any, key: str) -> CallOutcome:
        service.get_value(key)
        return CallOutcome(status_code=200)

    @staticmethod
    def _call_service_demo_cache_get(service: Any, key: str) -> CallOutcome:
        data = service.get_data(key)
        return CallOutcome(status_code=200, source=data.get("source"))

    def _prime_demo_cache(self, service: Any, key: str) -> None:
        service.clear_cache_key(key)
        payload = service.get_data(key)
        self._ensure_demo_cache_payload(payload)
        if payload["source"] != "origin":
            raise RuntimeError("Demo cache burst expected priming source=origin")

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

    @staticmethod
    def _assert_expected_cache_sources(timeline: list[dict[str, Any]]) -> None:
        for item in timeline:
            if item["statusCode"] != 200 or item["source"] != "cache":
                raise RuntimeError("Demo cache burst expected source=cache for all requests")

    def _run_parallel_operations(self, operations: list[BenchmarkOperation]) -> dict[str, Any]:
        barrier = Barrier(len(operations) + 1)
        threads: list[Thread] = []
        measurements: list[RequestMeasurement | None] = [None] * len(operations)
        unexpected_errors: list[Exception] = []
        error_lock = Lock()

        def runner(index: int, operation: BenchmarkOperation) -> None:
            barrier.wait()
            started_at = perf_counter()
            try:
                outcome = operation.call()
                status_code = outcome.status_code
                source = outcome.source
            except AppError as exc:
                status_code = exc.status_code
                source = None
            except Exception as exc:
                with error_lock:
                    unexpected_errors.append(exc)
                status_code = 500
                source = None
            ended_at = perf_counter()

            measurements[index] = RequestMeasurement(
                request_id=operation.request_id,
                key=operation.key,
                started_at=started_at,
                ended_at=ended_at,
                status="success" if 200 <= status_code < 400 else "error",
                status_code=status_code,
                source=source,
            )

        for index, operation in enumerate(operations):
            thread = Thread(target=runner, args=(index, operation), daemon=True)
            thread.start()
            threads.append(thread)

        started_at = perf_counter()
        barrier.wait()

        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Concurrent benchmark thread did not finish in time")

        if unexpected_errors:
            raise unexpected_errors[0]

        ended_at = perf_counter()
        return build_burst_metrics(
            measurements=[item for item in measurements if item is not None],
            started_at=started_at,
            ended_at=ended_at,
        )

    @contextmanager
    def _benchmark_context(self):
        database_name = f"mini_redis_bm_{uuid4().hex[:12]}"
        mongo_client = MongoClient(
            self._settings.mongo_uri,
            tz_aware=True,
            serverSelectionTimeoutMS=1_000,
        )
        command_executor = SingleThreadCommandExecutor(
            thread_name="mini-redis-benchmark-executor"
        )
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
            yield BenchmarkContext(
                app=app,
                mongo_client=mongo_client,
                database_name=database_name,
                command_executor=command_executor,
            )
        finally:
            command_executor.shutdown()
            mongo_client.drop_database(database_name)
            mongo_client.close()
