from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user
from db.models import Account, Client, Master, Manager
from schemas.auth import UserRoleResponse


class UserRoleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_role(
        self,
        requested_account_id: int,
        current_user: Account,
    ) -> UserRoleResponse:
        """
        Основная бизнес-логика получения роли пользователя.

        Правила доступа:
        - Любой авторизованный пользователь может смотреть свою роль
        - Только менеджеры могут смотреть чужие роли
        """
        if requested_account_id != current_user.account_id:

            is_manager = await self.session.execute(
                select(exists().where(Manager.account_id == current_user.account_id))
            )
            if not is_manager.scalar_one():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Только менеджеры могут просматривать роли других пользователей"
                )

        # target
        user_stmt = select(Account).where(Account.account_id == requested_account_id)
        user_result = await self.session.execute(user_stmt)
        target_user = user_result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        # roles
        roles: List[str] = []

        client_exists = await self.session.execute(
            select(exists().where(Client.account_id == requested_account_id))
        )
        if client_exists.scalar_one():
            roles.append("client")

        master_exists = await self.session.execute(
            select(exists().where(Master.account_id == requested_account_id))
        )
        if master_exists.scalar_one():
            roles.append("master")

        manager_exists = await self.session.execute(
            select(exists().where(Manager.account_id == requested_account_id))
        )
        if manager_exists.scalar_one():
            roles.append("manager")

        primary_role = roles[0] if roles else "account"

        return UserRoleResponse(
            account_id=target_user.account_id,
            login=target_user.login,
            role=primary_role,
            additional_roles=roles if len(roles) > 1 else None
        )
