from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.dependencies import get_current_user, get_current_manager
from db.models import Account
from db.session import get_db_session
from schemas.client import (
    ClientCreate,
    ClientOut,
    ClientWithBookingsOut,
    BookingInfoOut
)
from schemas.account import AccountCreate
from services.client.service import ClientService
from services.client.exceptions import (
    ClientNotFoundError,
    ClientAlreadyExistsError
)

router = APIRouter(prefix="/clients", tags=["Clients"])


def get_client_service(session: AsyncSession = Depends(get_db_session)) -> ClientService:
    return ClientService(session)


@router.post(
    "/with-existing-account",
    response_model=ClientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать клиента из существующего аккаунта"
)
async def create_client_from_account(
    data: ClientCreate,
    organization_id: int = Query(..., gt=0, description="ID организации"),
    current_user: Account = Depends(get_current_manager),
    service: ClientService = Depends(get_client_service),
):
    """Создает клиента для уже зарегистрированного аккаунта"""
    try:
        await service.check_manager_access(current_user.account_id, organization_id)
        return await service.create_client_from_account(data, organization_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClientAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/with-new-account",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Создать клиента с новым аккаунтом"
)
async def create_client_with_new_account(
    account_data: AccountCreate,
    organization_id: int = Query(..., gt=0, description="ID организации"),
    current_user: Account = Depends(get_current_manager),
    service: ClientService = Depends(get_client_service),
):
    """Создает новый аккаунт и связывает его с клиентом"""
    try:
        account, client = await service.create_client_with_new_account(
            account_data, organization_id, current_user
        )
        return {
            "account": account.model_dump(),
            "client": client.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/{client_id}",
    response_model=ClientOut,
    summary="Получить информацию о клиенте"
)
async def get_client(
    client_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    try:
        return await service.get_client(client_id)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{client_id}/bookings",
    response_model=List[BookingInfoOut],
    summary="Получить записи клиента"
)
async def get_client_bookings(
    client_id: int = Path(..., gt=0),
    status: Optional[str] = Query(None, description="Фильтр по статусу (pending, confirmed, cancelled, completed)"),
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    """Получить все записи клиента (только для чтения)"""
    try:
        return await service.get_client_bookings(client_id, status)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{client_id}/full",
    response_model=ClientWithBookingsOut,
    summary="Получить клиента с его записями"
)
async def get_client_with_bookings(
    client_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    """Получить клиента вместе со всеми его записями"""
    try:
        return await service.get_client_with_bookings(client_id)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/by-account/{account_id}",
    response_model=ClientOut,
    summary="Найти клиента по ID аккаунта"
)
async def get_client_by_account(
    account_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    try:
        org_id = await service.get_org_id(current_user)
        return await service.get_client_by_account(account_id, org_id)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/organization/{org_id}",
    response_model=List[ClientOut],
    summary="Получить всех клиентов организации"
)
async def get_org_clients(
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    try:
        return await service.get_org_clients(org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/me/profile",
    response_model=ClientOut,
    summary="Получить свой профиль клиента"
)
async def get_my_client_profile(
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    """Получить профиль клиента для текущего авторизованного пользователя"""
    try:
        org_id = await service.get_org_id(current_user)
        return await service.get_client_by_account(current_user.account_id, org_id)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/me/bookings",
    response_model=List[BookingInfoOut],
    summary="Получить свои записи"
)
async def get_my_bookings(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    current_user: Account = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    """Получить записи текущего клиента"""
    try:
        org_id = await service.get_org_id(current_user)
        client = await service.get_client_by_account(current_user.account_id, org_id)
        return await service.get_client_bookings(client.client_id, status)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))