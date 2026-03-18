from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator


class KeyedLockManager:
    def __init__(self) -> None:
        self._locks: dict[str, Lock] = {}
        self._guard = Lock()

    @contextmanager
    def lock(self, key: str) -> Iterator[None]:
        with self._guard:
            if key not in self._locks:
                self._locks[key] = Lock()
            lock = self._locks[key]

        lock.acquire()
        try:
            yield
        finally:
            lock.release()

