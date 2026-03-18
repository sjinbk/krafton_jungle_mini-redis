from __future__ import annotations

from src.common.errors import (
    invalid_iterations,
    invalid_key,
    invalid_request_count,
    invalid_seat_limit,
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


def validate_seat_limit(seat_limit: int) -> int:
    if isinstance(seat_limit, bool) or not isinstance(seat_limit, int) or not 1 <= seat_limit <= 100:
        raise invalid_seat_limit()
    return seat_limit


def validate_request_count(request_count: int) -> int:
    if (
        isinstance(request_count, bool)
        or not isinstance(request_count, int)
        or not 1 <= request_count <= 200
    ):
        raise invalid_request_count()
    return request_count

