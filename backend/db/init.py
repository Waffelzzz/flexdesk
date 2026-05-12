import asyncio

import asyncpg
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from core.config import (
    DATABASE_URL,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_USER,
)


async def init_database(retries=10, delay=1) -> AsyncEngine:
    """Проверяем подключение к базе данных"""
    for i in range(retries):
        try:

            conn = await asyncpg.connect(
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                host=POSTGRES_HOST,
                port=5432,
            )
            await conn.close()

            engine: AsyncEngine = create_async_engine(
                DATABASE_URL,
                connect_args={"server_settings": {"client_encoding": "utf8"}},
                echo=True,
                future=True,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            print("Успешное подключение к базе данных")
            return engine

        except Exception as e:
            print(f"Попытка {i + 1}/{retries} не удалась: {e}")
            if i < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise Exception(
                    f"Не удалось подключиться к базе после {retries} попыток"
                )
