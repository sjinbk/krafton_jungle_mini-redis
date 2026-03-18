from __future__ import annotations

from src.service.performance_benchmark_service import (
    RequestMeasurement,
    build_burst_metrics,
    build_cache_compare_metrics,
    calculate_p95_ms,
)


def test_build_cache_compare_metrics_returns_saved_and_speedup() -> None:
    metrics = build_cache_compare_metrics(
        cold_durations=[4.0, 6.0],
        warm_durations=[2.0, 2.0],
    )

    assert metrics == {
        "coldAvgMs": 5.0,
        "warmAvgMs": 2.0,
        "savedMs": 3.0,
        "speedupRatio": 2.5,
    }


def test_build_cache_compare_metrics_handles_zero_warm_average() -> None:
    metrics = build_cache_compare_metrics(
        cold_durations=[4.0],
        warm_durations=[0.0],
    )

    assert metrics["speedupRatio"] is None


def test_calculate_p95_ms_uses_nearest_rank() -> None:
    assert calculate_p95_ms([1.0, 2.0, 3.0, 4.0, 100.0]) == 100.0


def test_build_burst_metrics_returns_sorted_timeline_and_summary() -> None:
    measurements = [
        RequestMeasurement(
            request_id="request-2",
            key="beta",
            started_at=10.003,
            ended_at=10.009,
            status="success",
            status_code=200,
            source=None,
        ),
        RequestMeasurement(
            request_id="request-1",
            key="alpha",
            started_at=10.001,
            ended_at=10.004,
            status="success",
            status_code=200,
            source=None,
        ),
    ]

    metrics = build_burst_metrics(
        measurements=measurements,
        started_at=10.0,
        ended_at=10.01,
    )

    assert metrics["totalElapsedMs"] == 10.0
    assert metrics["avgMs"] == 4.5
    assert metrics["p95Ms"] == 6.0
    assert metrics["maxMs"] == 6.0
    assert metrics["successCount"] == 2
    assert metrics["errorCount"] == 0
    assert metrics["timeline"][0]["requestId"] == "request-1"
    assert metrics["timeline"][0]["startedOffsetMs"] == 1.0
    assert metrics["timeline"][1]["requestId"] == "request-2"
    assert metrics["timeline"][1]["durationMs"] == 6.0
