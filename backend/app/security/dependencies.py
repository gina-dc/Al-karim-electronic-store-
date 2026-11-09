from datetime import UTC, datetime
from hmac import compare_digest

from fastapi import HTTPException, Request

from app.models.auth import Session
from app.security.passwords import token_hash


async def current_session(request: Request) -> Session:
    token = request.cookies.get("shop_session", "")
    session = (
        await Session.filter(
            token_hash=token_hash(token), expires_at__gt=datetime.now(UTC)
        )
        .select_related("user")
        .first()
    )
    if not session or not session.user.active:
        raise HTTPException(401, "Authentication required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf = request.headers.get("X-CSRF-Token", "")
        if not csrf or not compare_digest(session.csrf_hash, token_hash(csrf)):
            raise HTTPException(403, "Invalid CSRF token")
    return session
