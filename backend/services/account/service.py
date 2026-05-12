from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from db.models import Account, Manager, Master, Client
from schemas.account import AccountCreate, AccountUpdate, AccountOut, AccountWithRelationsOut
from services.account.exceptions import (
    AccountNotFoundError,
    AccountLoginAlreadyExistsError,
    AccountInvalidPasswordError,
    AccountDisabledError,
)


class AccountService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_account_by_login(self, login: str) -> Account | None:
        """Получить аккаунт по логину"""
        stmt = select(Account).where(Account.login == login.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_account_by_id(self, account_id: int) -> Account:
        """Получить аккаунт по ID"""
        stmt = select(Account).where(Account.account_id == account_id)
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise AccountNotFoundError(account_id)
        return account

    async def _check_login_unique(self, login: str) -> None:
        """Проверить уникальность логина"""
        existing = await self._get_account_by_login(login)
        if existing:
            raise AccountLoginAlreadyExistsError(login)

    async def register(self, data: AccountCreate) -> AccountOut:
        """Регистрация нового аккаунта"""
        await self._check_login_unique(data.login)

        account = Account(
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
            phone=data.phone,
            login=data.login.lower(),
            password=hash_password(data.password),
            comments=data.comments,
            is_enable=True,
        )

        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)

        return AccountOut.model_validate(account)

    async def get_account(self, account_id: int) -> AccountOut:
        """Получить аккаунт по ID"""
        account = await self._get_account_by_id(account_id)
        return AccountOut.model_validate(account)

    async def get_account_with_relations(self, account_id: int) -> AccountWithRelationsOut:
        """Получить аккаунт с его ролями в организациях"""
        account = await self._get_account_by_id(account_id)

        stmt = select(Manager.organization_id).where(Manager.account_id == account_id)
        result = await self.session.execute(stmt)
        manager_orgs = [row for row in result.scalars().all()]

        stmt = select(Master.organization_id).where(Master.account_id == account_id)
        result = await self.session.execute(stmt)
        master_orgs = [row for row in result.scalars().all()]

        stmt = select(Client.organization_id).where(Client.account_id == account_id)
        result = await self.session.execute(stmt)
        client_orgs = [row for row in result.scalars().all()]

        return AccountWithRelationsOut(
            account_id=account.account_id,
            first_name=account.first_name,
            last_name=account.last_name,
            middle_name=account.middle_name,
            phone=account.phone,
            login=account.login,
            is_enable=account.is_enable,
            comments=account.comments,
            manager_orgs=manager_orgs,
            master_orgs=master_orgs,
            client_orgs=client_orgs,
        )

    async def update_account(
        self,
        account_id: int,
        data: AccountUpdate,
        current_user: Account
    ) -> AccountOut:
        """Обновить данные аккаунта (только свой или админ)"""
        if current_user.account_id != account_id:
            raise PermissionError("Вы можете изменять только свои данные")

        account = await self._get_account_by_id(account_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(account, key, value)

        await self.session.commit()
        await self.session.refresh(account)

        return AccountOut.model_validate(account)

    async def change_password(
        self,
        account_id: int,
        old_password: str,
        new_password: str,
        current_user: Account
    ) -> dict:
        """Сменить пароль"""
        if current_user.account_id != account_id:
            raise PermissionError("Вы можете менять только свой пароль")

        account = await self._get_account_by_id(account_id)

        if not verify_password(old_password, account.password):
            raise AccountInvalidPasswordError("Неверный текущий пароль")

        account.password = hash_password(new_password)
        await self.session.commit()

        return {"message": "Пароль успешно изменен"}

    async def deactivate_account(
        self,
        account_id: int,
        current_user: Account
    ) -> dict:
        """Деактивировать аккаунт (мягкое удаление)"""
        account = await self._get_account_by_id(account_id)

        if not account.is_enable:
            return {"message": f"Аккаунт {account_id} уже деактивирован"}

        account.is_enable = False
        await self.session.commit()

        return {"message": f"Аккаунт {account_id} деактивирован"}

    async def activate_account(
        self,
        account_id: int,
        current_user: Account
    ) -> dict:
        """Активировать аккаунт"""
        account = await self._get_account_by_id(account_id)

        if account.is_enable:
            return {"message": f"Аккаунт {account_id} уже активирован"}

        account.is_enable = True
        await self.session.commit()

        return {"message": f"Аккаунт {account_id} активирован"}

    async def get_account_by_login(self, login: str) -> AccountOut:
        """Получить аккаунт по логину"""
        account = await self._get_account_by_login(login)
        if not account:
            raise AccountNotFoundError(f"Аккаунт с логином '{login}' не найден")
        return AccountOut.model_validate(account)