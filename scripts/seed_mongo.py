from __future__ import annotations

from pathlib import Path
import sys

from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.config import Settings
from src.common.seed_data import DEFAULT_DUMMY_ITEMS


def main() -> None:
    settings = Settings.from_env()
    client = MongoClient(
        settings.mongo_uri,
        tz_aware=True,
        serverSelectionTimeoutMS=2_000,
    )

    try:
        collection = client[settings.mongo_db][settings.mongo_collection]
        collection.delete_many({})
        result = collection.insert_many(DEFAULT_DUMMY_ITEMS)
        print(
            f"Seeded {len(result.inserted_ids)} documents into "
            f"{settings.mongo_db}.{settings.mongo_collection}"
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
