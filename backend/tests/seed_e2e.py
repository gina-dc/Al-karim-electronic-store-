import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aerich import Command
from tortoise import Tortoise

from app.db.config import TORTOISE_ORM
from app.models.auth import LoginAttempt, User
from app.security.passwords import hash_password


async def main():
    url = TORTOISE_ORM["connections"]["default"]
    if not url.endswith("/shop_e2e_test"):
        raise RuntimeError(
            "This setup only permits the dedicated shop_e2e_test database"
        )
    async with await Tortoise.init(config=TORTOISE_ORM):
        command = Command(tortoise_config=TORTOISE_ORM)
        await command.init()
        await command.upgrade()
        await User.update_or_create(
            username="e2e_owner",
            defaults={
                "display_name": "E2E Owner",
                "role": "owner",
                "active": True,
                "password_hash": hash_password("test-only-long-password-2026"),
            },
        )
        await LoginAttempt.all().delete()


asyncio.run(main())
