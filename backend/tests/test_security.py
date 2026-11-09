import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.auth import UserInput
from app.security.passwords import hash_password, token_hash, verify_password


def test_argon2id_and_invalid_password():
    encoded = hash_password("a sufficiently long password")
    assert encoded.startswith("$argon2id$")
    assert verify_password(encoded, "a sufficiently long password")
    assert not verify_password(encoded, "incorrect")
    assert not verify_password("invalid hash", "password")


def test_tokens_are_not_stored_raw():
    assert len(token_hash("secret")) == 64
    assert token_hash("secret") != "secret"


def test_worker_cannot_be_created_as_login_role():
    with pytest.raises(ValidationError):
        UserInput(
            username="worker",
            display_name="Worker",
            password="long enough password",
            role="worker",
        )


def test_production_requires_https():
    with pytest.raises(ValidationError):
        Settings(environment="production", _env_file=None)
