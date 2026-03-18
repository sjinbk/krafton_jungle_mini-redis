from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import ceil


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class ManualClock:
    def __init__(self, start: datetime | None = None) -> None:
        self._current = start or datetime(2026, 3, 18, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._current

    def advance(self, *, seconds: int = 0) -> None:
        self._current = self._current + timedelta(seconds=seconds)


def calculate_expires_at(ttl_seconds: int, now: datetime) -> datetime:
    return now + timedelta(seconds=ttl_seconds)


def is_expired(expires_at: datetime | None, now: datetime) -> bool:
    return expires_at is not None and expires_at <= now


def ttl_seconds_remaining(expires_at: datetime | None, now: datetime) -> int | None:
    if expires_at is None:
        return None

    return max(0, ceil((expires_at - now).total_seconds()))


def format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

