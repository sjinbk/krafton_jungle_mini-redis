from __future__ import annotations

import pytest

from src.common.executor import SingleThreadCommandExecutor
from src.service.demo_cache_service import DemoCacheService
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


class FakeOriginRepository:
    def __init__(self, items_by_key: dict[str, list[dict[str, str]]]) -> None:
        self._items_by_key = items_by_key
        self.calls: list[str] = []

    def fetch_items(self, key: str) -> list[dict[str, str]]:
        self.calls.append(key)
        return list(self._items_by_key.get(key, []))


@pytest.fixture()
def demo_service() -> tuple[DemoCacheService, FakeOriginRepository, InMemoryStore, ManualClock]:
    repository = FakeOriginRepository(
        {
            "sample": [
                {"id": "sample-1", "value": "example payload 1"},
                {"id": "sample-2", "value": "example payload 2"},
            ]
        }
    )
    store = InMemoryStore()
    clock = ManualClock()
    executor = SingleThreadCommandExecutor()
    service = DemoCacheService(
        store=store,
        clock=clock,
        command_executor=executor,
        origin_repository=repository,
        default_ttl_seconds=15,
    )
    yield service, repository, store, clock
    executor.shutdown()


def test_origin_result_is_cached(
    demo_service: tuple[DemoCacheService, FakeOriginRepository, InMemoryStore, ManualClock]
) -> None:
    service, repository, _, _ = demo_service

    first = service.get_data("sample")
    second = service.get_data("sample")

    assert first["source"] == "origin"
    assert second["source"] == "cache"
    assert second["ttlSecondsRemaining"] is not None
    assert repository.calls == ["sample"]


def test_empty_origin_result_is_not_cached(
    demo_service: tuple[DemoCacheService, FakeOriginRepository, InMemoryStore, ManualClock]
) -> None:
    service, repository, store, _ = demo_service

    first = service.get_data("not-seeded")
    second = service.get_data("not-seeded")

    assert first["items"] == []
    assert second["items"] == []
    assert first["source"] == "origin"
    assert second["source"] == "origin"
    assert repository.calls == ["not-seeded", "not-seeded"]
    assert store.get("data:not-seeded") is None


def test_expired_cache_triggers_origin_refetch(
    demo_service: tuple[DemoCacheService, FakeOriginRepository, InMemoryStore, ManualClock]
) -> None:
    service, repository, store, clock = demo_service

    service.get_data("sample")
    clock.advance(seconds=16)
    refreshed = service.get_data("sample")

    assert refreshed["source"] == "origin"
    assert repository.calls == ["sample", "sample"]
    assert store.get("data:sample") is not None
