from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user
from db.models import Account
from db.session import get_db_session
from schemas.auth import UserRoleResponse
from services.auth.role_service import UserRoleService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/{account_id}/role",
    response_model=UserRoleResponse,
    summary="Получить роль пользователя по account_id"
)
async def get_user_role(
    account_id: int = Path(..., gt=0),
    current_user: Account = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = UserRoleService(session)
    return await service.get_user_role(
        requested_account_id=account_id,
        current_user=current_user
    )