from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_manager, get_current_user, get_current_master_by_id
from db.session import get_db_session
from db.models import Account, Master
from schemas.account import AccountCreate
from schemas.master import (
    MasterCreate,
    AssignServiceMaster,
    MasterOut,
    ServiceMasterOut,
    MasterWorkDayOut,
    MasterCreateData, MasterWorkDayDetailedOut
)
from services.master.service import MasterService

router = APIRouter(prefix="/masters", tags=["Masters"])


@router.post(
        "/service",
        response_model=ServiceMasterOut,
        status_code=status.HTTP_201_CREATED
    )
async def assign_srevice_to_master(
    data: AssignServiceMaster,
    current_manager: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.assign_service_to_master(data, current_manager)

@router.post(
    "/with-existing-account",
    response_model=MasterOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать мастера из существующего аккаунта"
)
async def create_master_from_account(
    data: MasterCreate,
    current_manager: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    """Создает мастера для уже зарегистрированного аккаунта"""
    service = MasterService(session)
    try:
        return await service.create_master_from_account(data, current_manager)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/with-new-account",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Создать мастера с новым аккаунтом"
)
async def create_master_with_new_account(
    account_data: AccountCreate,
    master_data: MasterCreateData,
    current_manager: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Создает новый аккаунт и связывает его с мастером.
    Возвращает данные аккаунта и мастера.
    """
    service = MasterService(session)
    try:
        account, master = await service.create_master_with_new_account(
            account_data, master_data, current_manager
        )
        return {
            "account": account.model_dump(),
            "master": master.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/{service_master_id}/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Деактивировать сервис у мастера(мягкое удаление)"
)
async def deactivate_servicemaster(
    service_master_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.deactivate_servicemaster(service_master_id, current_user)

@router.post(
    "/{service_master_id}/activate",
    status_code=status.HTTP_200_OK,
    summary="Активировать сервис у мастера"
)
async def activate_service_master(
    service_master_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.activate_service_master(service_master_id, current_user)

@router.get(
    "/of_org/{org_id}",
    response_model=List[MasterOut],
    summary="Получить информацию об мастерах организации "
)
async def get_org_masters(
    org_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.get_org_masters(org_id, current_user)


@router.get(
    "/{master_id}/workday/{work_date}",
    response_model=MasterWorkDayOut,
    summary="Получить рабочий день мастера на дату"
)
async def get_master_work_day(
    master_id: int = Path(..., gt=0),
    work_date: date = Path(..., description="Дата в формате YYYY-MM-DD"),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.get_master_work_day(master_id, work_date, current_user)

@router.get(
    "/info/{id}",
    response_model=MasterOut,
    summary="Получить информацию об мастере "
)
async def get_org_masters(
    id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.get_master(id, current_user)

@router.get(
    "/{id}/service",
    response_model=List[ServiceMasterOut],
    summary="Получить услуги мастера "
)
async def get_service_master(
        id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.get_service_master(id, current_user)

@router.get(
    "/{id}/service/active",
    response_model=List[ServiceMasterOut],
    summary="Получить только активные услуги мастера "
)
async def get_service_master_active(
        id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)
    return await service.get_service_master_active(id, current_user)

@router.get(
    "/{master_id}/me",
    summary="Доступ мастера только к самому себе"
)
async def get_my_master_data(
    master: Master = Depends(get_current_master_by_id),
    session: AsyncSession = Depends(get_db_session),
):
    service = MasterService(session)

    return await service.get_master(master.master_id, master.account)

@router.get(
    "/{master_id}/work-day-detailed/{work_date}",
    response_model=MasterWorkDayDetailedOut,
    summary="Получить детальный рабочий план мастера на дату"
)
async def get_master_work_day_detailed(
    master_id: int = Path(..., gt=0),
    work_date: date = Path(..., description="Дата в формате YYYY-MM-DD"),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Возвращает детальный рабочий план мастера с информацией о каждом слоте"""
    service = MasterService(session)
    return await service.get_master_work_day_detailed(master_id, work_date, current_user)


@router.get(
    "/{master_id}/work-week/{start_date}",
    response_model=dict,
    summary="Получить рабочую неделю мастера"
)
async def get_master_work_week(
    master_id: int = Path(..., gt=0),
    start_date: date = Path(..., description="Дата начала недели в формате YYYY-MM-DD"),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Возвращает рабочий план мастера на неделю"""
    service = MasterService(session)
    return await service.get_master_work_week(master_id, start_date, current_user)

@router.get(
    "/{master_id}/work-month/{year}/{month}",
    response_model=dict,
    summary="Получить рабочий месяц мастера"
)
async def get_master_work_month(
    master_id: int = Path(..., gt=0),
    year: int = Path(..., ge=2020, le=2100),
    month: int = Path(..., ge=1, le=12),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Возвращает рабочий план мастера на месяц"""
    service = MasterService(session)
    return await service.get_master_work_month(master_id, year, month, current_user)


@router.get(
    "/{master_id}/work-range",
    response_model=dict,
    summary="Получить рабочий план мастера за период"
)
async def get_master_work_range(
    master_id: int = Path(..., gt=0),
    date_from: date = Query(..., description="Дата начала"),
    date_to: date = Query(..., description="Дата окончания"),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Возвращает рабочий план мастера за произвольный период"""
    service = MasterService(session)
    return await service.get_master_work_range(master_id, date_from, date_to, current_user)
