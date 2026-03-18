from __future__ import annotations

from typing import Any


class MongoOriginRepository:
    def __init__(self, collection: Any) -> None:
        self._collection = collection

    def fetch_items(self, key: str) -> list[dict[str, Any]]:
        cursor = self._collection.find({"key": key}).sort("itemId", 1)
        return [
            {
                "id": document["itemId"],
                "value": document["value"],
            }
            for document in cursor
        ]

