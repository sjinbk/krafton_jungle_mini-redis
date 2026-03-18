from __future__ import annotations

from typing import Any, Protocol

from src.common.locks import KeyedLockManager
from src.common.validation import validate_key
from src.store.in_memory import InMemoryStore, StoreEntry
from src.ttl.policy import (
    calculate_expires_at,
    format_utc_timestamp,
    is_expired,
    ttl_seconds_remaining,
)


class OriginRepository(Protocol):
    def fetch_items(self, key: str) -> list[dict[str, Any]]:
        ...


class DemoCacheService:
    def __init__(
        self,
        *,
        store: InMemoryStore,
        clock: Any,
        lock_manager: KeyedLockManager,
        origin_repository: OriginRepository,
        default_ttl_seconds: int,
    ) -> None:
        self._store = store
        self._clock = clock
        self._locks = lock_manager
        self._origin_repository = origin_repository
        self._default_ttl_seconds = default_ttl_seconds

    def get_data(self, key: str) -> dict[str, Any]:
        validate_key(key)
        cache_key = self._cache_key(key)

        with self._locks.lock(cache_key):
            cached_entry = self._get_live_entry(cache_key)
            if cached_entry is not None:
                payload = cached_entry.value
                return {
                    "key": key,
                    "source": "cache",
                    "originType": "mongodb",
                    "cacheKey": cache_key,
                    "ttlSecondsRemaining": ttl_seconds_remaining(
                        cached_entry.expires_at,
                        self._clock.now(),
                    ),
                    "originFetchedAt": payload["originFetchedAt"],
                    "items": payload["items"],
                }

            fetched_at = format_utc_timestamp(self._clock.now())
            items = self._origin_repository.fetch_items(key)
            if not items:
                return {
                    "key": key,
                    "source": "origin",
                    "originType": "mongodb",
                    "cacheKey": cache_key,
                    "ttlSecondsRemaining": None,
                    "originFetchedAt": fetched_at,
                    "items": [],
                }

            payload = {
                "originFetchedAt": fetched_at,
                "items": items,
            }
            expires_at = calculate_expires_at(self._default_ttl_seconds, self._clock.now())
            self._store.set(cache_key, payload, expires_at)

            return {
                "key": key,
                "source": "origin",
                "originType": "mongodb",
                "cacheKey": cache_key,
                "ttlSecondsRemaining": None,
                "originFetchedAt": fetched_at,
                "items": items,
            }

    def clear_cache_key(self, key: str) -> bool:
        return self._store.delete(self._cache_key(key))

    @staticmethod
    def _cache_key(key: str) -> str:
        return f"data:{key}"

    def _get_live_entry(self, key: str) -> StoreEntry | None:
        entry = self._store.get(key)
        if entry is None:
            return None

        if is_expired(entry.expires_at, self._clock.now()):
            self._store.delete(key)
            return None

        return entry

