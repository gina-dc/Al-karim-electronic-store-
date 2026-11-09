import hashlib
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from tortoise.models import Model


def digest(payload) -> str:
    return hashlib.sha256(payload.model_dump_json().encode()).hexdigest()


def require_role(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, "You do not have permission for this operation")


def today():
    return datetime.now(ZoneInfo("Asia/Karachi")).date()


def valid_date(value, user=None):
    if user and user.role == "staff" and value != today():
        raise HTTPException(403, "Staff may only record transactions for today")
    if value > today():
        raise HTTPException(422, "Future transaction dates are not allowed")


async def get_record(model, record_id, lock=False):
    query = model.filter(id=record_id)
    if lock:
        query = query.select_for_update()
    record = await query.first()
    if not record:
        raise HTTPException(404, "Record not found")
    return record


def scalar(value):
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def record_data(record: Model):
    return {
        field: scalar(getattr(record, field))
        for field in record._meta.db_fields
        if field
        not in {
            "logo",
            "password_hash",
            "token_hash",
            "csrf_hash",
            "request_hash",
            "idempotency_key",
        }
    }


async def total(query, field="amount"):
    from tortoise.functions import Sum

    result = await query.annotate(value=Sum(field)).values("value")
    return Decimal(str(result[0]["value"] or 0)) if result else Decimal(0)


async def idempotent(model, key, payload):
    # Every caller invokes this inside its financial transaction. The transaction
    # connection is inherited so concurrent identical submissions serialize.
    from tortoise import connections

    conn = connections.get("default")
    await conn.execute_query(
        "SELECT pg_advisory_xact_lock($1)", [int(str(key).replace("-", "")[:15], 16)]
    )
    existing = await model.filter(idempotency_key=key).first()
    if existing and existing.request_hash != digest(payload):
        raise HTTPException(409, "Idempotency key was already used for different data")
    return existing
