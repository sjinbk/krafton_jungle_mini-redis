from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class StoreEntry:
    value: Any
    expires_at: datetime | None = None


class InMemoryStore:
    def __init__(self) -> None:
        self._entries: dict[str, StoreEntry] = {}

    def get(self, key: str) -> StoreEntry | None:
        return self._entries.get(key)

    def set(self, key: str, value: Any, expires_at: datetime | None = None) -> None:
        self._entries[key] = StoreEntry(value=value, expires_at=expires_at)

    def put(self, key: str, entry: StoreEntry) -> None:
        self._entries[key] = entry

    def delete(self, key: str) -> bool:
        return self._entries.pop(key, None) is not None

    def clear(self) -> None:
        self._entries.clear()

    def size(self) -> int:
        return len(self._entries)

