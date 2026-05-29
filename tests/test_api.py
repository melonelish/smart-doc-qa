import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_no_file(client):
    response = client.post("/api/v1/documents/upload")
    assert response.status_code == 422


def test_ask_without_body(client):
    response = client.post("/api/v1/qa/ask")
    assert response.status_code == 422


def test_ask_invalid_json(client):
    response = client.post(
        "/api/v1/qa/ask",
        json={"document_id": "test-id"},
    )
    assert response.status_code == 422
