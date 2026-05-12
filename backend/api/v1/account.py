from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.models import Account
from db.session import get_db_session
from schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountOut,
    AccountWithRelationsOut,
    AccountPasswordChange,
)
from services.account.exceptions import (
    AccountNotFoundError,
    AccountLoginAlreadyExistsError,
    AccountInvalidPasswordError,
)
from services.account.service import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def get_account_service(session: AsyncSession = Depends(get_db_session)) -> AccountService:
    return AccountService(session)


@router.post(
    "/register",
    response_model=AccountOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового аккаунта",
    description="""
    Создаёт новый аккаунт в системе.

    - **login**: уникальный логин (только буквы, цифры, _)
    - **password**: минимум 6 символов
    - Остальные поля опциональны
    """,
    responses={
        400: {"description": "Логин уже занят или ошибка валидации"},
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def register_account(
        account_data: AccountCreate,
        service: AccountService = Depends(get_account_service),
) -> AccountOut:
    try:
        return await service.register(account_data)
    except AccountLoginAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при регистрации. Попробуйте позже."
        )


@router.get(
    "/{account_id}",
    response_model=AccountOut,
    summary="Получить информацию об аккаунте",
)
async def get_account(
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> AccountOut:
    """Получить данные аккаунта (доступ только своему аккаунту или админу)"""
    if current_user.account_id != account_id:
        # TODO: добавить проверку на админа
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Вы можете просматривать только свой аккаунт"
        )

    try:
        return await service.get_account(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/full",
    response_model=AccountWithRelationsOut,
    summary="Получить полную информацию об аккаунте с ролями",
)
async def get_account_with_relations(
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> AccountWithRelationsOut:
    """Получить данные аккаунта с его ролями в организациях"""
    if current_user.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )

    try:
        return await service.get_account_with_relations(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/{account_id}",
    response_model=AccountOut,
    summary="Обновить данные аккаунта",
)
async def update_account(
        account_data: AccountUpdate,
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> AccountOut:
    try:
        return await service.update_account(account_id, account_data, current_user)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{account_id}/change-password",
    summary="Сменить пароль",
)
async def change_password(
        password_data: AccountPasswordChange,
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> dict:
    try:
        return await service.change_password(
            account_id,
            password_data.old_password,
            password_data.new_password,
            current_user
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AccountInvalidPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{account_id}/deactivate",
    summary="Деактивировать аккаунт",
)
async def deactivate_account(
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> dict:
    """Деактивация аккаунта (требует прав администратора)"""
    try:
        return await service.deactivate_account(account_id, current_user)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{account_id}/activate",
    summary="Активировать аккаунт",
)
async def activate_account(
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> dict:
    """Активация аккаунта (требует прав администратора)"""
    try:
        return await service.activate_account(account_id, current_user)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/by-login/{login}",
    response_model=AccountOut,
    summary="Найти аккаунт по логину",
)
async def get_account_by_login(
        login: str,
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> AccountOut:
    """Поиск аккаунта по логину"""
    try:
        return await service.get_account_by_login(login)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/roles",
    response_model=dict,
    summary="Получить роли аккаунта в организациях",
    description="""
    Возвращает список организаций, где пользователь является:
    - менеджером
    - мастером
    - клиентом
    """,
)
async def get_account_roles(
        account_id: int = Path(..., gt=0),
        current_user: Account = Depends(get_current_user),
        service: AccountService = Depends(get_account_service),
) -> dict:
    """Получить роли аккаунта в организациях"""
    if current_user.account_id != account_id:
        # TODO: добавить проверку на админа
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Вы можете просматривать только свой аккаунт"
        )

    try:
        account_with_roles = await service.get_account_with_relations(account_id)

        return {
            "account_id": account_with_roles.account_id,
            "login": account_with_roles.login,
            "first_name": account_with_roles.first_name,
            "last_name": account_with_roles.last_name,
            "roles": {
                "manager_in": account_with_roles.manager_orgs,
                "master_in": account_with_roles.master_orgs,
                "client_in": account_with_roles.client_orgs
            }
        }
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))