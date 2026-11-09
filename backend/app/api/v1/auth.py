import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from tortoise.transactions import in_transaction

from app.core.config import get_settings
from app.models.auth import AuditLog, LoginAttempt, Session, User
from app.schemas.auth import LoginInput, UserInput
from app.security.dependencies import current_session
from app.security.passwords import (
    DUMMY_HASH,
    hash_password,
    token_hash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def user_data(user):
    return {
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
    }


@router.post("/login")
async def login(payload: LoginInput, request: Request, response: Response):
    settings = get_settings()
    if request.headers.get("origin") != settings.frontend_origin:
        raise HTTPException(403, "Invalid origin")
    source = token_hash(request.client.host if request.client else "unknown")
    cutoff = datetime.now(UTC) - timedelta(minutes=15)
    async with in_transaction() as conn:
        await conn.execute_query(
            "SELECT pg_advisory_xact_lock($1)", [int(source[:15], 16)]
        )
        if (
            await LoginAttempt.filter(
                source_hash=source, created_at__gte=cutoff
            ).count()
            >= 10
        ):
            raise HTTPException(
                429, "Too many login attempts. Try again in 15 minutes."
            )
        await LoginAttempt.filter(created_at__lt=cutoff).delete()
        await LoginAttempt.create(source_hash=source)
    user = await User.filter(username=payload.username.lower()).first()
    valid = await run_in_threadpool(
        verify_password, user.password_hash if user else DUMMY_HASH, payload.password
    )
    if not user or not valid or not user.active:
        raise HTTPException(401, "Invalid username or password")
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    async with in_transaction():
        await Session.create(
            user=user,
            token_hash=token_hash(token),
            csrf_hash=token_hash(csrf),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.session_hours),
        )
        await AuditLog.create(user=user, action="auth.login")
    response.set_cookie(
        "shop_session",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_hours * 3600,
        path="/api",
    )
    response.set_cookie(
        "shop_csrf",
        csrf,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    return user_data(user)


@router.get("/me")
async def me(session: Annotated[Session, Depends(current_session)]):
    return user_data(session.user)


@router.post("/logout", status_code=204)
async def logout(
    response: Response, session: Annotated[Session, Depends(current_session)]
):
    async with in_transaction():
        await AuditLog.create(user=session.user, action="auth.logout")
        await session.delete()
    response.delete_cookie("shop_session", path="/api")
    response.delete_cookie("shop_csrf", path="/")


@router.post("/users", status_code=201)
async def create_user(
    payload: UserInput, session: Annotated[Session, Depends(current_session)]
):
    if session.user.role != "owner":
        raise HTTPException(403, "Owner access required")
    encoded = await run_in_threadpool(hash_password, payload.password)
    async with in_transaction():
        user = await User.create(
            username=payload.username.lower(),
            display_name=payload.display_name,
            password_hash=encoded,
            role=payload.role,
        )
        await AuditLog.create(
            user=session.user, action="user.create", details={"user_id": str(user.id)}
        )
    return user_data(user)
