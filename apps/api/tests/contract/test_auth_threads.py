"""Contract tests for auth + threads OpenAPI paths (fail until DB wired in CI)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_login_requires_body() -> None:
    res = client.post("/v1/auth/login", json={})
    assert res.status_code == 422


def test_me_requires_auth() -> None:
    res = client.get("/v1/auth/me")
    assert res.status_code == 401


def test_threads_requires_auth() -> None:
    res = client.get("/v1/threads")
    assert res.status_code == 401
