from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str
    mongo_collection: str
    default_cache_ttl_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        default_ttl = int(os.getenv("MINI_REDIS_DEFAULT_TTL_SECONDS", "15"))
        if default_ttl <= 0:
            raise ValueError("MINI_REDIS_DEFAULT_TTL_SECONDS must be greater than zero")

        return cls(
            mongo_uri=os.getenv("MINI_REDIS_MONGO_URI", "mongodb://127.0.0.1:27017"),
            mongo_db=os.getenv("MINI_REDIS_MONGO_DB", "mini_redis"),
            mongo_collection=os.getenv("MINI_REDIS_MONGO_COLLECTION", "dummy_items"),
            default_cache_ttl_seconds=default_ttl,
        )

