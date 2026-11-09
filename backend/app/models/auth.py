import uuid

from tortoise import fields, models


class User(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    username = fields.CharField(max_length=100, unique=True)
    display_name = fields.CharField(max_length=150)
    password_hash = fields.CharField(max_length=255)
    role = fields.CharField(max_length=20, default="staff")
    active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"


class Session(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField(
        "models.User", related_name="sessions", on_delete=fields.CASCADE
    )
    token_hash = fields.CharField(max_length=64, unique=True)
    csrf_hash = fields.CharField(max_length=64)
    expires_at = fields.DatetimeField(db_index=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "sessions"


class AuditLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    action = fields.CharField(max_length=100)
    details = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"


class LoginAttempt(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    source_hash = fields.CharField(max_length=64, db_index=True)
    created_at = fields.DatetimeField(auto_now_add=True, db_index=True)

    class Meta:
        table = "login_attempts"
