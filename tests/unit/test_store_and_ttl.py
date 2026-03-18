from __future__ import annotations

from datetime import datetime, timezone

from src.store.in_memory import InMemoryStore
from src.ttl.policy import calculate_expires_at, is_expired, ttl_seconds_remaining


def test_store_set_get_delete_round_trip() -> None:
    store = InMemoryStore()

    store.set("sample", {"value": 1})
    entry = store.get("sample")

    assert entry is not None
    assert entry.value == {"value": 1}
    assert store.delete("sample") is True
    assert store.get("sample") is None


def test_calculate_expires_at_and_remaining_seconds() -> None:
    now = datetime(2026, 3, 18, 0, 0, tzinfo=timezone.utc)
    expires_at = calculate_expires_at(5, now)

    assert expires_at.isoformat() == "2026-03-18T00:00:05+00:00"
    assert ttl_seconds_remaining(expires_at, now) == 5


def test_is_expired_only_after_deadline() -> None:
    now = datetime(2026, 3, 18, 0, 0, tzinfo=timezone.utc)
    expires_at = calculate_expires_at(3, now)

    assert is_expired(expires_at, now) is False
    assert is_expired(expires_at, datetime(2026, 3, 18, 0, 0, 3, tzinfo=timezone.utc)) is True

