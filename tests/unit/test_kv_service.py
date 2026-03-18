from __future__ import annotations

import pytest

from src.common.errors import AppError
from src.common.locks import KeyedLockManager
from src.service.kv_service import KeyValueService
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


@pytest.fixture()
def kv_service() -> tuple[KeyValueService, InMemoryStore, ManualClock]:
    store = InMemoryStore()
    clock = ManualClock()
    service = KeyValueService(
        store=store,
        clock=clock,
        lock_manager=KeyedLockManager(),
    )
    return service, store, clock


def test_set_and_get_value(kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]) -> None:
    service, _, _ = kv_service

    result = service.set_value(key="sample", value={"name": "mini-redis"})

    assert result["created"] is True
    assert service.get_value("sample") == {
        "key": "sample",
        "value": {"name": "mini-redis"},
    }


def test_missing_key_returns_key_not_found(
    kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]
) -> None:
    service, _, _ = kv_service

    with pytest.raises(AppError) as exc:
        service.get_value("missing")

    assert exc.value.code == "KEY_NOT_FOUND"


def test_delete_removes_key(kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]) -> None:
    service, _, _ = kv_service
    service.set_value(key="sample", value="cached")

    assert service.delete_value("sample") == {
        "key": "sample",
        "deleted": True,
    }

    with pytest.raises(AppError):
        service.get_value("sample")


def test_overwrite_without_ttl_clears_existing_expiration(
    kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]
) -> None:
    service, _, clock = kv_service
    service.set_value(key="sample", value="first", ttl_seconds=10)
    clock.advance(seconds=3)

    overwrite_result = service.set_value(key="sample", value="second")
    ttl_result = service.get_ttl("sample")

    assert overwrite_result["created"] is False
    assert ttl_result == {
        "key": "sample",
        "hasTtl": False,
        "ttlSecondsRemaining": None,
    }


def test_ttl_expiration_removes_key_lazily(
    kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]
) -> None:
    service, store, clock = kv_service
    service.set_value(key="sample", value="ephemeral", ttl_seconds=5)

    assert service.get_value("sample") == {
        "key": "sample",
        "value": "ephemeral",
    }

    clock.advance(seconds=5)

    with pytest.raises(AppError) as exc:
        service.get_value("sample")

    assert exc.value.code == "KEY_NOT_FOUND"
    assert store.get("sample") is None


def test_invalid_key_is_rejected(kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]) -> None:
    service, _, _ = kv_service

    with pytest.raises(AppError) as exc:
        service.set_value(key="   ", value="invalid")

    assert exc.value.code == "INVALID_KEY"


def test_invalid_ttl_is_rejected(kv_service: tuple[KeyValueService, InMemoryStore, ManualClock]) -> None:
    service, _, _ = kv_service

    with pytest.raises(AppError) as exc:
        service.expire_value("sample", 0)

    assert exc.value.code == "INVALID_TTL"

