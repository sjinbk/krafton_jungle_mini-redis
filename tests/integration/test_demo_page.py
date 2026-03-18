from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.common.config import Settings
from src.store.in_memory import InMemoryStore
from src.ttl.policy import ManualClock


class StubOriginRepository:
    def fetch_items(self, key: str):
        return []


def test_demo_page_is_served_from_root() -> None:
    app = create_app(
        settings=Settings(
            mongo_uri="mongodb://127.0.0.1:27017",
            mongo_db="mini_redis_demo_page",
            mongo_collection="dummy_items",
            default_cache_ttl_seconds=15,
        ),
        store=InMemoryStore(),
        clock=ManualClock(),
        origin_repository=StubOriginRepository(),
    )

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "미니 레디스 데모 페이지" in response.text
    assert "기본 KV 기능" in response.text
    assert "더미 데이터 조회" in response.text
    assert "성능 비교 실행" in response.text
    assert "동시성 확인 실행" in response.text
