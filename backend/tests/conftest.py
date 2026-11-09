import os

import httpx
import pytest
from aerich import Command
from tortoise import Tortoise, connections

from app.db.config import TORTOISE_ORM


@pytest.fixture
async def db():
    url = os.getenv("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL for PostgreSQL integration tests")
    if not url.startswith("postgres://") or not url.rsplit("/", 1)[-1].endswith(
        "_test"
    ):
        raise RuntimeError(
            "Tests require a dedicated PostgreSQL database ending in _test"
        )
    config = {**TORTOISE_ORM, "connections": {"default": url}}
    async with await Tortoise.init(config=config):
        command = Command(tortoise_config=config)
        await command.init()
        await command.upgrade()
        # Only a validated dedicated test database can reach this cleanup.
        tables = [
            m._meta.db_table
            for m in Tortoise.apps["models"].values()
            if m._meta.db_table != "aerich"
        ]
        statement = (
            "TRUNCATE " + ", ".join('"' + table + '"' for table in tables) + " CASCADE"
        )
        await connections.get("default").execute_script(statement)
        yield
        await connections.get("default").execute_script(statement)


@pytest.fixture
async def client(db):
    from app.main import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        yield client


@pytest.fixture
async def owner(db):
    from app.models.auth import User

    return await User.create(
        username="owner",
        display_name="Owner",
        role="owner",
        password_hash="test-only-unused",
    )


@pytest.fixture
async def owner_client(client):
    from datetime import UTC, datetime, timedelta

    from app.models.auth import Session, User
    from app.security.passwords import token_hash

    user = await User.create(
        username="owner",
        display_name="Owner",
        role="owner",
        password_hash="test-only-unused",
    )
    await Session.create(
        user=user,
        token_hash=token_hash("test-owner-session"),
        csrf_hash=token_hash("test-csrf"),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    client.cookies.set("shop_session", "test-owner-session", path="/api")
    client.headers["X-CSRF-Token"] = "test-csrf"
    return client, user
