from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from pymongo import MongoClient

from src.api.app import create_app
from src.common.config import Settings
from src.common.seed_data import DEFAULT_DUMMY_ITEMS
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


@pytest.fixture()
def manual_clock() -> ManualClock:
    return ManualClock()


@pytest.fixture()
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture()
def mongo_client() -> MongoClient:
    client = MongoClient(
        "mongodb://127.0.0.1:27017",
        tz_aware=True,
        serverSelectionTimeoutMS=1_000,
    )

    try:
        client.admin.command("ping")
    except Exception as exc:
        client.close()
        pytest.skip(f"MongoDB is not available: {exc}")

    yield client
    client.close()


@pytest.fixture()
def integration_app(mongo_client: MongoClient):
    database_name = f"mini_redis_test_{uuid4().hex}"
    collection = mongo_client[database_name]["dummy_items"]
    collection.delete_many({})
    collection.insert_many(DEFAULT_DUMMY_ITEMS)

    app = create_app(
        settings=Settings(
            mongo_uri="mongodb://127.0.0.1:27017",
            mongo_db=database_name,
            mongo_collection="dummy_items",
            default_cache_ttl_seconds=15,
        ),
        store=InMemoryStore(),
        clock=ManualClock(),
        mongo_client=mongo_client,
    )

    yield app

    mongo_client.drop_database(database_name)
