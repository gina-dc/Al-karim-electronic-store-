import os
from datetime import UTC, datetime, timedelta

import pytest

from app.models.auth import Session, User
from app.security.passwords import hash_password

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Set TEST_DATABASE_URL to a dedicated PostgreSQL test database",
)


async def test_session_csrf_authorization_logout(client):
    await User.create(
        username="owner",
        display_name="Owner",
        role="owner",
        password_hash=hash_password("a long owner password"),
    )
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "owner", "password": "a long owner password"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert "httponly" in response.headers.get_list("set-cookie")[0].lower()
    assert (await client.get("/api/v1/auth/me")).json()["role"] == "owner"
    assert (await client.post("/api/v1/auth/logout")).status_code == 403
    csrf = client.cookies.get("shop_csrf")
    payload = {
        "username": "staff",
        "display_name": "Staff",
        "password": "a long staff password",
        "role": "staff",
    }
    assert (
        await client.post(
            "/api/v1/auth/users", json=payload, headers={"X-CSRF-Token": csrf}
        )
    ).status_code == 201
    assert (
        await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    ).status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "staff", "password": "a long staff password"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/users",
            json=payload,
            headers={"X-CSRF-Token": client.cookies.get("shop_csrf")},
        )
    ).status_code == 403
    await Session.all().update(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_login_origin_and_password(client):
    payload = {"username": "missing", "password": "incorrect"}
    assert (await client.post("/api/v1/auth/login", json=payload)).status_code == 403
    assert (
        await client.post(
            "/api/v1/auth/login",
            json=payload,
            headers={"Origin": "http://localhost:5173"},
        )
    ).status_code == 401
