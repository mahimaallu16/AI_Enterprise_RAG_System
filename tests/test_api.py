"""
tests/test_api.py
-------------------
Basic Flask route/integration tests using the test client. These focus on
request/response contracts (status codes, JSON shape) rather than actual
model calls, so they run without requiring Gemini API access.
"""

import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client(client):
    """A test client that's already logged in as the demo user."""
    client.post("/login", data={"username": "demo", "password": "demo123"})
    return client


def test_home_page_loads(auth_client):
    resp = auth_client.get("/")
    assert resp.status_code == 200


def test_home_page_redirects_when_not_logged_in(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302)


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_stats_endpoint_shape(auth_client):
    resp = auth_client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    for key in ("total_documents", "total_pages", "total_chunks"):
        assert key in body["data"]


def test_usage_endpoint_shape(auth_client):
    resp = auth_client.get("/api/usage")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "estimated_cost_usd" in body["data"]


def test_upload_with_no_files_returns_400(auth_client):
    resp = auth_client.post("/api/upload", data={})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_upload_rejects_unsupported_extension(auth_client):
    data = {"files": (io.BytesIO(b"not a real file"), "malware.exe")}
    resp = auth_client.post("/api/upload", data=data, content_type="multipart/form-data")
    body = resp.get_json()
    # Overall request succeeds (200) since it's per-file reporting, but
    # the individual file result must indicate failure.
    assert body["data"][0]["success"] is False


def test_upload_txt_file_succeeds(auth_client):
    content = b"This is a simple test document about enterprise RAG systems."
    data = {"files": (io.BytesIO(content), "sample.txt")}
    resp = auth_client.post("/api/upload", data=data, content_type="multipart/form-data")
    body = resp.get_json()
    assert body["data"][0]["success"] is True
    assert body["data"][0]["document"]["total_chunks"] >= 1


def test_chat_ask_without_question_returns_400(auth_client):
    resp = auth_client.post("/api/chat/ask", json={"question": ""})
    assert resp.status_code == 400


def test_chat_ask_requires_login(client):
    resp = client.post("/api/chat/ask", json={"question": "hello"})
    assert resp.status_code == 401


def test_chat_clear_endpoint(auth_client):
    resp = auth_client.post("/api/chat/clear", json={"session_id": "test-session"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_documents_list_endpoint(auth_client):
    resp = auth_client.get("/api/documents")
    assert resp.status_code == 200
    assert isinstance(resp.get_json()["data"], list)
