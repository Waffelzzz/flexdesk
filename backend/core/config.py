import os
import secrets
from typing import Optional

from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"


class Settings(BaseSettings):
    """
    Настройки приложения.
    """

    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=30, ge=5, le=10080, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., env="POSTGRES_DB")
    postgres_host: str = Field(default="db", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")

    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="URL для подключения к Redis "
                    "(включая пароль, db, TLS и т.д.)"
    )
    redis_prefix: str = Field(
        default="fastapi-cache",
        env="REDIS_CACHE_PREFIX",
        description="Префикс для ключей кэша"
    )

    redis_socket_timeout: Optional[float] = None
    redis_socket_connect_timeout: Optional[float] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def effective_secret_key(self) -> str:
        if not self.secret_key.strip():
            raise ValueError("SECRET_KEY не задан в переменных окружения!")
        return self.secret_key


settings = Settings()
