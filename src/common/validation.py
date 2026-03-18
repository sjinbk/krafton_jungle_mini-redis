from __future__ import annotations

from src.common.errors import (
    invalid_burst_count,
    invalid_iterations,
    invalid_key,
    invalid_scenario,
    invalid_ttl,
)


def validate_key(key: str) -> str:
    if not isinstance(key, str) or not key.strip():
        raise invalid_key()
    return key


def validate_ttl(ttl_seconds: int) -> int:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise invalid_ttl()
    return ttl_seconds


def validate_iterations(iterations: int) -> int:
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 100:
        raise invalid_iterations()
    return iterations


def validate_burst_count(count: int) -> int:
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 50:
        raise invalid_burst_count()
    return count


def validate_scenario(scenario: str, allowed: set[str]) -> str:
    if not isinstance(scenario, str) or scenario not in allowed:
        raise invalid_scenario()
    return scenario

