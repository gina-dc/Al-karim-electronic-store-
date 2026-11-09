import asyncio
import getpass

from pydantic import ValidationError
from tortoise import Tortoise
from tortoise.transactions import in_transaction

from app.db.config import TORTOISE_ORM
from app.models.auth import AuditLog, User
from app.schemas.auth import UserInput
from app.security.passwords import hash_password


def prompt_owner_details() -> UserInput:
    while True:
        username = input("Owner username: ").strip()
        display_name = input("Owner display name: ").strip()
        try:
            UserInput(
                username=username,
                display_name=display_name,
                password="validation-only-password",
                role="owner",
            )
        except ValidationError as exc:
            for error in exc.errors(include_input=False):
                print(f"{error['loc'][0]}: {error['msg']}")
            print("Please enter the account details again.")
            continue
        break
    while True:
        password = getpass.getpass("Password (12-128 characters; typing is hidden): ")
        try:
            payload = UserInput(
                username=username,
                display_name=display_name,
                password=password,
                role="owner",
            )
        except ValidationError:
            print(
                "Password must contain between 12 and 128 characters. Please try again."
            )
            continue
        if password != getpass.getpass("Confirm password: "):
            print("Passwords do not match. Please try again.")
            continue
        return payload


async def main():
    payload = prompt_owner_details()
    async with await Tortoise.init(config=TORTOISE_ORM), in_transaction() as conn:
        await conn.execute_query("SELECT pg_advisory_xact_lock(81234001)")
        if await User.filter(role="owner").exists():
            raise SystemExit(
                "An owner already exists; use authenticated user administration"
            )
        user = await User.create(
            username=payload.username.lower(),
            display_name=payload.display_name,
            password_hash=hash_password(payload.password),
            role="owner",
        )
        await AuditLog.create(user=user, action="owner.bootstrap")
    print("Owner created")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Owner setup cancelled.") from None
