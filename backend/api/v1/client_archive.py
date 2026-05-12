from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_manager, get_current_user
from core.security import get_current_user as get_current_user_security  # если разные
from db.session import get_db_session
from db.models import Account
from schemas.client_archive import (
    ClientArchiveInsert,
    ClientArchiveSelectOut,
    ClientArchiveUpdate
)
from services.client_archive.service import ClientArchiveService

router = APIRouter(prefix="/client-archive", tags=["ClientArchive"])


@router.post(
    "/{client_id}/insert",
    status_code=status.HTTP_200_OK,
    summary="Добавление данных в архив клиента"
)
async def client_archive_insert(
    data: ClientArchiveInsert,
    client_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = ClientArchiveService(session)
    return await service.client_archive_insert(data, client_id, current_user)

@router.post(
    "/{client_archive_id}/delete",
    status_code=status.HTTP_200_OK,
    summary="Удаление данных в архив клиента"
)
async def client_archive_delete(
    client_archive_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = ClientArchiveService(session)
    return await service.client_archive_delete(client_archive_id, current_user)

@router.post(
    "/{client_archive_id}/update",
    status_code=status.HTTP_200_OK,
    summary="Изменение данных в архив клиента"
)
async def client_archive_update(
    data: ClientArchiveUpdate,
    client_archive_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = ClientArchiveService(session)
    return await service.client_archive_update(client_archive_id, data, current_user)


@router.get(
    "/{client_archive_id}/select",
    response_model=ClientArchiveSelectOut,
    summary="Получить информацию из архива"
)
async def client_archive_select(
    client_archive_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = ClientArchiveService(session)
    return await service.client_archive_select(client_archive_id, current_user)