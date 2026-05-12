from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_manager, get_current_user
from db.session import get_db_session
from db.models import Account
from schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationOut
)
from services.organization.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "/",
    response_model=OrganizationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую организацию (только авторизованный менеджер)"
)
async def create_organization(
    data: OrganizationCreate,
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    return await service.create_organization(data, current_user)


@router.get(
    "/my",
    response_model=List[OrganizationOut],
    summary="Получить все активные организации текущего пользователя"
)
async def get_my_organizations(
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    return await service.get_my_organizations(current_user)


@router.get(
    "/{org_id}",
    response_model=OrganizationOut,
    summary="Получить информацию об активной организации (только для связанных пользователей)"
)
async def get_organization(
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    return await service.get_organization(org_id, current_user)


@router.patch(
    "/{org_id}",
    response_model=OrganizationOut,
    summary="Обновить организацию (только менеджер своей организации)"
)
async def update_organization(
    data: OrganizationUpdate,
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    return await service.update_organization(org_id, data, current_user)


@router.post(
    "/{org_id}/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Деактивировать организацию (мягкое удаление)"
)
async def deactivate_organization(
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    return await service.deactivate_organization(org_id, current_user)


@router.post(
    "/{org_id}/activate",
    response_model=OrganizationOut,
    status_code=status.HTTP_200_OK,
    summary="Активировать ранее деактивированную организацию"
)
async def activate_organization(
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = OrganizationService(session)
    return await service.activate_organization(org_id, current_user)