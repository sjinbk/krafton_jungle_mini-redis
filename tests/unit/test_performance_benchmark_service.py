from __future__ import annotations

from src.service.performance_benchmark_service import build_cache_compare_metrics


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
