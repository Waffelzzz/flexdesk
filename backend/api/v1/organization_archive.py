from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_manager, get_current_user
from core.security import get_current_user as get_current_user_security  # если разные
from db.session import get_db_session
from db.models import Account
from schemas.organization_archive import (
    OrganizationArchiveIn,
    OrganizationArchiveSelectOut,
    OrganizationArchiveDate,
    OrganizationArchiveUpdate
)
from services.organization_archive.service import OrganizationArchiveService

router = APIRouter(prefix="/organization-archive", tags=["OrganizationArchive"])


@router.post(
    "/{org_id}/insert",
    status_code=status.HTTP_200_OK,
    summary="Добавление данных в архив организации"
)
async def client_archive_insert(
    data: OrganizationArchiveIn,
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationArchiveService(session)
    return await service.organization_archive_insert(data, org_id, current_user)

@router.post(
    "/{organization_archive_id}/delete",
    status_code=status.HTTP_200_OK,
    summary="Удаление данных в архив организации"
)
async def organization_archive_delete(
    organization_archive_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationArchiveService(session)
    return await service.organization_archive_delete(organization_archive_id, current_user)

@router.post(
    "/{organization_archive_id}/update",
    status_code=status.HTTP_200_OK,
    summary="Изменение данных в архив организации"
)
async def organization_archive_update(
    data: OrganizationArchiveUpdate,
    organization_archive_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationArchiveService(session)
    return await service.organization_archive_update(organization_archive_id, data, current_user)


@router.get(
    "/{organization_archive_id}/select",
    response_model=OrganizationArchiveSelectOut,
    summary="Получить информацию из архива"
)
async def organization_archive_select(
    data: OrganizationArchiveDate,
    organization_archive_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationArchiveService(session)
    return await service.organization_archive_select(organization_archive_id, data, current_user)