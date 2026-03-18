from __future__ import annotations

from fastapi.testclient import TestClient


def test_kv_create_get_delete_flow(integration_app) -> None:
    with TestClient(integration_app) as client:
        create_response = client.post(
            "/kv",
            json={"key": "sample", "value": {"status": "ready"}},
        )
        get_response = client.get("/kv/sample")
        delete_response = client.delete("/kv/sample")
        missing_response = client.get("/kv/sample")

    assert create_response.status_code == 201
    assert create_response.json()["data"] == {
        "key": "sample",
        "value": {"status": "ready"},
    }
    assert get_response.status_code == 200
    assert delete_response.status_code == 200
    assert delete_response.json()["data"] == {
        "key": "sample",
        "deleted": True,
    }
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "KEY_NOT_FOUND"


def test_kv_expire_and_ttl_flow(integration_app) -> None:
    with TestClient(integration_app) as client:
        client.post("/kv", json={"key": "ttl-key", "value": "cached"})
        expire_response = client.post("/kv/ttl-key/expire", json={"ttlSeconds": 5})
        ttl_response = client.get("/kv/ttl-key/ttl")

        integration_app.state.clock.advance(seconds=5)
        expired_response = client.get("/kv/ttl-key")
        expired_ttl_response = client.get("/kv/ttl-key/ttl")

    assert expire_response.status_code == 200
    assert expire_response.json()["data"]["hasTtl"] is True
    assert ttl_response.status_code == 200
    assert ttl_response.json()["data"] == {
        "key": "ttl-key",
        "hasTtl": True,
        "ttlSecondsRemaining": 5,
    }
    assert expired_response.status_code == 404
    assert expired_ttl_response.status_code == 404


def test_demo_cache_flow_uses_origin_then_cache_then_origin_after_expiry(integration_app) -> None:
    with TestClient(integration_app) as client:
        first_response = client.get("/demo/data-cache", params={"key": "sample"})
        second_response = client.get("/demo/data-cache", params={"key": "sample"})

        integration_app.state.clock.advance(seconds=16)
        third_response = client.get("/demo/data-cache", params={"key": "sample"})

    assert first_response.status_code == 200
    assert first_response.json()["data"]["source"] == "origin"
    assert len(first_response.json()["data"]["items"]) == 2

    assert second_response.status_code == 200
    assert second_response.json()["data"]["source"] == "cache"
    assert second_response.json()["data"]["ttlSecondsRemaining"] is not None

    assert third_response.status_code == 200
    assert third_response.json()["data"]["source"] == "origin"


def test_demo_cache_empty_result_is_not_cached(integration_app) -> None:
    with TestClient(integration_app) as client:
        first_response = client.get("/demo/data-cache", params={"key": "not-seeded"})
        second_response = client.get("/demo/data-cache", params={"key": "not-seeded"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["data"]["items"] == []
    assert second_response.json()["data"]["items"] == []
    assert first_response.json()["data"]["source"] == "origin"
    assert second_response.json()["data"]["source"] == "origin"


def test_invalid_requests_return_400(integration_app) -> None:
    with TestClient(integration_app) as client:
        invalid_key_response = client.post("/kv", json={"key": "", "value": "bad"})
        invalid_ttl_response = client.post("/kv/ttl-key/expire", json={"ttlSeconds": 0})
        missing_query_response = client.get("/demo/data-cache")

    assert invalid_key_response.status_code == 400
    assert invalid_key_response.json()["error"]["code"] == "INVALID_KEY"
    assert invalid_ttl_response.status_code == 400
    assert invalid_ttl_response.json()["error"]["code"] == "INVALID_TTL"
    assert missing_query_response.status_code == 400

