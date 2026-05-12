import logging
import secrets
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import (
    login,
    users,
    organization,
    master,
    booking,
    client_archive, organization_archive,
    account, client, master_archive
)
from db.init import init_database
from core.config import settings
from services.admin.init import ensure_default_accounts

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация базы данных...")
    engine = await init_database()
    app.state.db_engine = engine

    logger.info("Проверка существования администратора...")

    async with AsyncSession(engine, expire_on_commit=False) as session:
        await ensure_default_accounts(session)
        await session.commit()

    logger.info("Подключение к Redis...")
    redis_client = aioredis.from_url(
        str(settings.redis_url),
        encoding="utf8",
        decode_responses=False,
    )
    FastAPICache.init(
        RedisBackend(redis_client),
        prefix=settings.redis_prefix
    )
    app.state.redis = redis_client

    logger.info(f"Redis подключён (prefix: {settings.redis_prefix})")
    logger.info("Приложение запущено и готово к работе")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("Закрытие подключения к БД...")
    await engine.dispose()

    logger.info("Закрытие подключения к Redis...")
    await redis_client.close()

    logger.info("Engine и Redis закрыты")

app = FastAPI(lifespan=lifespan)

SECRET_KEY = secrets.token_urlsafe(48)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_id",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
)

origins = [
    # for dev
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://localhost:8081"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "X-Requested-With",
    ],
    max_age=3600,
)

app.include_router(login.router, prefix="/v1", tags=["Auth API v1"])
app.include_router(users.router, prefix="/v1", tags=["Users API v1"])
app.include_router(organization.router, prefix="/v1", tags=["Organization API v1"])
app.include_router(master.router, prefix="/v1", tags=["Masters API v1"])
app.include_router(client_archive.router, prefix="/v1", tags=["Client-Archive API v1"])
app.include_router(organization_archive.router, prefix="/v1", tags=["Organization-Archive API v1"])
app.include_router(booking.router, prefix="/v1", tags=["Booking API v1"])
app.include_router(account.router, prefix="/v1", tags=["Accounts API v1"])
app.include_router(client.router, prefix="/v1", tags=["Client API v1"])
app.include_router(master_archive.router, prefix="/v1", tags=["Master Archive API v1"])

