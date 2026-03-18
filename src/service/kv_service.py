from __future__ import annotations

from typing import Any

from src.common.errors import key_not_found
from src.common.locks import KeyedLockManager
from src.common.validation import validate_key, validate_ttl
from src.store.in_memory import InMemoryStore, StoreEntry
from src.ttl.policy import calculate_expires_at, is_expired, ttl_seconds_remaining


class KeyValueService:
    def __init__(
        self,
        *,
        store: InMemoryStore,
        clock: Any,
        lock_manager: KeyedLockManager,
    ) -> None:
        self._store = store
        self._clock = clock
        self._locks = lock_manager

    def set_value(
        self,
        *,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        validate_key(key)
        if ttl_seconds is not None:
            validate_ttl(ttl_seconds)

        with self._locks.lock(key):
            existing_entry = self._get_live_entry(key)
            created = existing_entry is None
            expires_at = (
                calculate_expires_at(ttl_seconds, self._clock.now())
                if ttl_seconds is not None
                else None
            )
            self._store.set(key, value, expires_at)
            return {
                "created": created,
                "data": {
                    "key": key,
                    "value": value,
                },
            }

    def get_value(self, key: str) -> dict[str, Any]:
        validate_key(key)

        with self._locks.lock(key):
            entry = self._get_live_entry(key)
            if entry is None:
                raise key_not_found()

            return {
                "key": key,
                "value": entry.value,
            }

    def delete_value(self, key: str) -> dict[str, Any]:
        validate_key(key)

        with self._locks.lock(key):
            entry = self._get_live_entry(key)
            if entry is None:
                raise key_not_found()

            self._store.delete(key)
            return {
                "key": key,
                "deleted": True,
            }

    def expire_value(self, key: str, ttl_seconds: int) -> dict[str, Any]:
        validate_key(key)
        validate_ttl(ttl_seconds)

        with self._locks.lock(key):
            entry = self._get_live_entry(key)
            if entry is None:
                raise key_not_found()

            expires_at = calculate_expires_at(ttl_seconds, self._clock.now())
            self._store.put(key, StoreEntry(value=entry.value, expires_at=expires_at))
            return {
                "key": key,
                "hasTtl": True,
                "ttlSecondsRemaining": ttl_seconds_remaining(
                    expires_at,
                    self._clock.now(),
                ),
            }

    def get_ttl(self, key: str) -> dict[str, Any]:
        validate_key(key)

        with self._locks.lock(key):
            entry = self._get_live_entry(key)
            if entry is None:
                raise key_not_found()

            remaining = ttl_seconds_remaining(entry.expires_at, self._clock.now())
            return {
                "key": key,
                "hasTtl": remaining is not None,
                "ttlSecondsRemaining": remaining,
            }

    def _get_live_entry(self, key: str) -> StoreEntry | None:
        entry = self._store.get(key)
        if entry is None:
            return None

        if is_expired(entry.expires_at, self._clock.now()):
            self._store.delete(key)
            return None

        return entry

