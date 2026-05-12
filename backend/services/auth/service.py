from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, hash_password, verify_password
from db.models import Account
from schemas.auth import Token, UserLogin
from schemas.user import UserCreate, UserOut
from services.auth.exceptions import (
    InvalidPasswordError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_account_by_login(
        self, login: str, raise_if_not_found: bool = True
    ) -> Account | None:
        """Получить аккаунт по логину"""
        stmt = select(Account).where(Account.login == login)
        result = await self.session.execute(stmt)
        account = result.scalars().first()

        if not account and raise_if_not_found:
            raise UserNotFoundError(f"Пользователь с логином '{login}' не найден")

        return account

    async def register(self, data: UserCreate) -> UserOut:
        """
        Регистрация нового аккаунта.
        Заполняются все поля, которые переданы в UserCreate.
        """
        if await self._get_account_by_login(data.login, raise_if_not_found=False):
            raise UsernameAlreadyExistsError(data.login)

        hashed_password = hash_password(data.password)

        account = Account(
            login=data.login,
            password=hashed_password,
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
            phone=data.phone,
            comments=data.comments,
            is_enable=True,
        )

        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)

        return UserOut.model_validate(account)

    async def login(self, credentials: UserLogin) -> Token:
        """
        Аутентификация по логину и паролю.
        Возвращает JWT-токен.
        """
        account = await self._get_account_by_login(
            credentials.login,
            raise_if_not_found=False
        )

        if not account:
            raise UserNotFoundError()

        if not verify_password(credentials.password, account.password):
            raise InvalidPasswordError()

        access_token = create_access_token(data={"sub": account.login})

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=account.account_id,
            login=account.login,
        )
