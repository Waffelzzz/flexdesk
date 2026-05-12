from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


async def get_db_session(request: Request) -> AsyncSession:
    """Зависимость: возвращает асинхронную сессию ORM"""
    engine: AsyncEngine = request.app.state.db_engine
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
