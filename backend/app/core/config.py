from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgres://shop:shop@localhost:5432/shop"
    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False
    session_hours: int = Field(default=12, ge=1, le=168)
    shop_name: str = "Electronics Shop"

    @model_validator(mode="after")
    def secure_production(self):
        if not self.database_url.startswith("postgres://"):
            raise ValueError(
                "DATABASE_URL must use PostgreSQL with the postgres:// scheme"
            )
        origin = urlsplit(self.frontend_origin)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.netloc
            or origin.path
            or origin.query
            or origin.fragment
        ):
            raise ValueError("FRONTEND_ORIGIN must be an HTTP(S) origin without a path")
        if self.environment == "production":
            if not self.cookie_secure or not self.frontend_origin.startswith(
                "https://"
            ):
                raise ValueError(
                    "Production requires secure cookies and an HTTPS frontend origin"
                )
            if "shop:shop@" in self.database_url:
                raise ValueError(
                    "Replace development database credentials in production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
