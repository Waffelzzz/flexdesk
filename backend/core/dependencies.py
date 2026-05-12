from fastapi import Depends, HTTPException, Request, Path
from fastapi import status as http_status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user
from db.models import Account, Manager, Master, Client
from db.session import get_db_session


async def get_current_manager(
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    """
    Проверяет, что текущий пользователь — менеджер (есть запись в таблице managers).
    Возвращает аккаунт, если проверка пройдена.
    """
    stmt = select(exists().where(Manager.account_id == current_user.account_id))
    result = await session.execute(stmt)
    is_manager = result.scalar()

    if not is_manager:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только менеджерам"
        )

    return current_user


async def get_current_master(
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    """
    Проверяет, что текущий пользователь — мастер (есть запись в таблице masters).
    Возвращает аккаунт, если проверка пройдена.
    """
    stmt = select(exists().where(Master.account_id == current_user.account_id))
    result = await session.execute(stmt)
    is_manager = result.scalar()

    if not is_manager:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только менеджерам"
        )

    return current_user

async def get_current_master_by_id(
    master_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_master),
    session: AsyncSession = Depends(get_db_session),
) -> Master:
    """
    Проверяет, что текущий пользователь — это ИМЕННО этот мастер
    """

    stmt = select(Master).where(
        Master.master_id == master_id,
        Master.account_id == current_user.account_id
    )

    master = (await session.execute(stmt)).scalar_one_or_none()

    if not master:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете доступа к этому мастеру"
        )

    return master


async def get_current_client(
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Account:
    """
    Проверяет, что текущий пользователь — клиент (есть запись в таблице clients).
    Возвращает аккаунт, если проверка пройдена.
    """
    stmt = select(exists().where(Client.account_id == current_user.account_id))
    result = await session.execute(stmt)
    is_manager = result.scalar()

    if not is_manager:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только менеджерам"
        )

    return current_user


def only_from_localhost(request: Request):
    """
    Разрешает доступ к эндпоинту ТОЛЬКО с localhost (127.0.0.1 или IPv6 ::1).
    Работает как внутри Docker, так и на хост-машине.
    """
    client_host = request.client.host if request.client else None

    if client_host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Доступ к этому эндпоинту разрешён только с localhost"
        )

    return True