from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from src.api.responses import build_error_response, build_success_response
from src.api.schemas import (
    ConcurrencyBurstRequest,
    ExpireRequest,
    PerformanceCompareRequest,
    SetValueRequest,
)
from src.common.config import Settings
from src.common.executor import SingleThreadCommandExecutor
from src.common.errors import AppError
from src.service.demo_cache_service import DemoCacheService
from src.service.demo_cache_service import OriginRepository
from src.service.kv_service import KeyValueService
from src.service.mongo_origin import MongoOriginRepository
from src.service.performance_benchmark_service import PerformanceBenchmarkService
from src.store.in_memory import InMemoryStore
from src.ttl.policy import SystemClock


def _map_validation_error(exc: RequestValidationError) -> tuple[str, str]:
    code = "INVALID_KEY"
    message = "Request validation failed"

    for error in exc.errors():
        location = error.get("loc", ())
        field = location[-1] if location else None
        if field == "ttlSeconds":
            return "INVALID_TTL", "ttlSeconds must be a positive integer greater than zero"
        if field == "iterations":
            return "INVALID_ITERATIONS", "iterations must be an integer between 1 and 100"
        if field == "count":
            return "INVALID_BURST_COUNT", "count must be an integer between 1 and 50"
        if field == "scenario":
            return (
                "INVALID_SCENARIO",
                "scenario must be one of sameKeyKvGetBurst, differentKeyKvGetBurst, demoCacheGetBurst",
            )
        if field == "key":
            code = "INVALID_KEY"
            message = "Key must be a non-empty string"

    return code, message


def create_app(
    *,
    settings: Settings | None = None,
    store: InMemoryStore | None = None,
    clock: Any | None = None,
    mongo_client: MongoClient | None = None,
    command_executor: SingleThreadCommandExecutor | None = None,
    origin_repository: OriginRepository | None = None,
    include_performance_routes: bool = True,
) -> FastAPI:
    settings = settings or Settings.from_env()
    store = store or InMemoryStore()
    clock = clock or SystemClock()
    owns_command_executor = command_executor is None
    command_executor = command_executor or SingleThreadCommandExecutor()

    owns_mongo_client = mongo_client is None and origin_repository is None
    if origin_repository is None:
        mongo_client = mongo_client or MongoClient(
            settings.mongo_uri,
            tz_aware=True,
            serverSelectionTimeoutMS=1_000,
        )
        origin_repository = MongoOriginRepository(
            mongo_client[settings.mongo_db][settings.mongo_collection]
        )

    kv_service = KeyValueService(
        store=store,
        clock=clock,
        command_executor=command_executor,
    )
    demo_cache_service = DemoCacheService(
        store=store,
        clock=clock,
        command_executor=command_executor,
        origin_repository=origin_repository,
        default_ttl_seconds=settings.default_cache_ttl_seconds,
    )
    performance_benchmark_service = None
    if include_performance_routes:
        performance_benchmark_service = PerformanceBenchmarkService(
            settings=settings,
            app_factory=create_app,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            if owns_command_executor:
                command_executor.shutdown()
            if owns_mongo_client and mongo_client is not None:
                mongo_client.close()

    app = FastAPI(title="Mini Redis", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.store = store
    app.state.clock = clock
    app.state.mongo_client = mongo_client
    app.state.command_executor = command_executor
    app.state.kv_service = kv_service
    app.state.demo_cache_service = demo_cache_service
    app.state.performance_benchmark_service = performance_benchmark_service

    @app.exception_handler(AppError)
    def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        code, message = _map_validation_error(exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=build_error_response(code, message),
        )

    @app.exception_handler(Exception)
    def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=build_error_response("INTERNAL_ERROR", str(exc)),
        )

    @app.post("/kv")
    def set_value(payload: SetValueRequest, request: Request, response: Response) -> dict[str, Any]:
        result = request.app.state.kv_service.set_value(
            key=payload.key,
            value=payload.value,
            ttl_seconds=payload.ttlSeconds,
        )
        response.status_code = (
            status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK
        )
        return build_success_response(result["data"])

    @app.get("/kv/{key}")
    def get_value(key: str, request: Request) -> dict[str, Any]:
        data = request.app.state.kv_service.get_value(key)
        return build_success_response(data)

    @app.delete("/kv/{key}")
    def delete_value(key: str, request: Request) -> dict[str, Any]:
        data = request.app.state.kv_service.delete_value(key)
        return build_success_response(data)

    @app.post("/kv/{key}/expire")
    def expire_value(key: str, payload: ExpireRequest, request: Request) -> dict[str, Any]:
        data = request.app.state.kv_service.expire_value(key, payload.ttlSeconds)
        return build_success_response(data)

    @app.get("/kv/{key}/ttl")
    def get_ttl(key: str, request: Request) -> dict[str, Any]:
        data = request.app.state.kv_service.get_ttl(key)
        return build_success_response(data)

    @app.get("/demo/data-cache")
    def get_demo_data_cache(
        request: Request,
        key: str = Query(..., min_length=1),
    ) -> dict[str, Any]:
        data = request.app.state.demo_cache_service.get_data(key)
        return build_success_response(data)

    if include_performance_routes:
        @app.post("/demo/performance/cache-compare")
        def compare_demo_cache_performance(
            request: Request,
            payload: PerformanceCompareRequest | None = None,
        ) -> dict[str, Any]:
            payload = payload or PerformanceCompareRequest()
            data = request.app.state.performance_benchmark_service.compare_cache(
                key=payload.key,
                iterations=payload.iterations,
            )
            return build_success_response(data)

        @app.post("/demo/performance/concurrency-burst")
        def run_concurrency_burst(
            request: Request,
            payload: ConcurrencyBurstRequest,
        ) -> dict[str, Any]:
            data = request.app.state.performance_benchmark_service.run_concurrency_burst(
                scenario=payload.scenario,
                count=payload.count,
                key=payload.key,
            )
            return build_success_response(data)

    return app


app = create_app()
