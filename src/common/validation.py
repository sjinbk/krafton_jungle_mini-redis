from __future__ import annotations

from src.common.errors import invalid_key, invalid_ttl


def validate_key(key: str) -> str:
    if not isinstance(key, str) or not key.strip():
        raise invalid_key()
    return key


def validate_ttl(ttl_seconds: int) -> int:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise invalid_ttl()
    return ttl_seconds

