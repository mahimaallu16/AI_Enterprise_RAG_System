"""
tests/test_auth.py
---------------------
Tests for the simulated login/logout/registration system and route
protection (login_required).
"""

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


def test_root_redirects_to_login_when_unauthenticated(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_protected_api_returns_401_json_when_unauthenticated(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


def test_health_endpoint_is_public(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_login_with_demo_credentials_succeeds(client):
    resp = client.post("/login", data={"username": "demo", "password": "demo123"}, follow_redirects=False)
    assert resp.status_code in (301, 302)
    with client.session_transaction() as sess:
        assert sess["username"] == "demo"


def test_login_with_bad_credentials_fails(client):
    resp = client.post("/login", data={"username": "demo", "password": "wrongpass"})
    assert resp.status_code == 401
    assert b"Invalid username or password" in resp.data


def test_authenticated_user_can_access_dashboard(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    resp = client.get("/")
    assert resp.status_code == 200


def test_authenticated_user_can_access_protected_api(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_logout_clears_session(client):
    client.post("/login", data={"username": "demo", "password": "demo123"})
    client.get("/logout")
    resp = client.get("/api/stats")
    assert resp.status_code == 401


def test_register_new_user_and_auto_login(client):
    resp = client.post(
        "/register",
        data={"username": "newuser1", "password": "securepass123", "display_name": "New User"},
        follow_redirects=False,
    )
    assert resp.status_code in (301, 302)
    with client.session_transaction() as sess:
        assert sess["username"] == "newuser1"


def test_register_duplicate_username_fails(client):
    client.post("/register", data={"username": "dupeuser", "password": "securepass123"})
    client.get("/logout")
    resp = client.post("/register", data={"username": "dupeuser", "password": "anotherpass"})
    assert resp.status_code == 400
    assert b"already taken" in resp.data
