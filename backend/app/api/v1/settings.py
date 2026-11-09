from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from tortoise.transactions import in_transaction

from app.api.v1.business import Auth
from app.models.auth import AuditLog, Session, User
from app.models.business import ShopSettings
from app.schemas.auth import UserUpdate
from app.schemas.business import SettingsInput
from app.security.passwords import hash_password
from app.services.common import get_record, record_data, require_role

router = APIRouter(tags=["Settings"])


@router.get("/settings")
async def settings_get(session: Auth):
    settings, _ = await ShopSettings.get_or_create(id=1)
    return {**record_data(settings), "has_logo": bool(settings.logo)}


@router.put("/settings")
async def settings_update(payload: SettingsInput, session: Auth):
    require_role(session.user, "owner")
    async with in_transaction():
        settings, _ = await ShopSettings.get_or_create(id=1)
        settings.update_from_dict(payload.model_dump())
        await settings.save()
        await AuditLog.create(user=session.user, action="settings.update")
    return {**record_data(settings), "has_logo": bool(settings.logo)}


@router.get("/users")
async def users(session: Auth):
    require_role(session.user, "owner")
    return [record_data(user) for user in await User.all().order_by("created_at")]


@router.get("/settings/logo")
async def logo_get(session: Auth):
    settings, _ = await ShopSettings.get_or_create(id=1)
    if not settings.logo:
        raise HTTPException(404, "No logo configured")
    return Response(settings.logo, media_type="image/png")


@router.put("/settings/logo")
async def logo_update(request: Request, session: Auth):
    require_role(session.user, "owner")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1_000_000:
            raise HTTPException(413, "Logo must be smaller than 1 MB")
    try:
        image = Image.open(BytesIO(raw))
        if (
            image.format not in {"PNG", "JPEG"}
            or image.width > 2000
            or image.height > 2000
        ):
            raise HTTPException(422, "Use a PNG or JPEG of at most 2000 x 2000 pixels")
        image.load()
        output = BytesIO()
        image.convert("RGBA").save(output, format="PNG")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, "Invalid image") from exc
    async with in_transaction():
        settings, _ = await ShopSettings.get_or_create(id=1)
        settings.logo = output.getvalue()
        await settings.save()
        await AuditLog.create(user=session.user, action="settings.logo")
    return {"has_logo": True}


@router.patch("/users/{record_id}")
async def user_update(record_id: UUID, payload: UserUpdate, session: Auth):
    require_role(session.user, "owner")
    encoded = (
        await run_in_threadpool(hash_password, payload.password)
        if payload.password
        else None
    )
    async with in_transaction() as conn:
        await conn.execute_query("SELECT pg_advisory_xact_lock(81234001)")
        user = await get_record(User, record_id, lock=True)
        if (
            user.role == "owner"
            and user.active
            and (payload.role != "owner" or not payload.active)
            and await User.filter(role="owner", active=True).count() <= 1
        ):
            raise HTTPException(409, "At least one active owner must remain")
        user.display_name, user.role, user.active = (
            payload.display_name,
            payload.role,
            payload.active,
        )
        if encoded:
            user.password_hash = encoded
        await user.save()
        if encoded or not user.active:
            await Session.filter(user=user).delete()
        await AuditLog.create(
            user=session.user, action="user.update", details={"id": str(user.id)}
        )
    return record_data(user)
