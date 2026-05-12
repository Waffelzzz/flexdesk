from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional

from db.models import Client, Account, Booking, ServiceMaster, Master
from schemas.client import (
    ClientCreate, ClientOut, ClientWithBookingsOut, BookingInfoOut
)
from schemas.account import AccountCreate, AccountOut
from services.client.exceptions import (
    ClientNotFoundError,
    ClientAlreadyExistsError
)
from services.account.exceptions import AccountLoginAlreadyExistsError


class ClientService:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_org_id(self, current_user: Account) -> int:
        """Получить ID организации текущего пользователя"""
        stmt = select(Client.organization_id).where(
            Client.account_id == current_user.account_id
        )
        result = await self.session.execute(stmt)
        org_id = result.scalar_one_or_none()

        if not org_id:
            raise ValueError("Текущий пользователь не привязан к организации")
        return org_id

    async def _get_client_by_id(self, client_id: int) -> Client:
        """Получить клиента по ID"""
        stmt = select(Client).where(Client.client_id == client_id)
        result = await self.session.execute(stmt)
        client = result.scalar_one_or_none()
        if not client:
            raise ClientNotFoundError(client_id)
        return client

    async def _get_client_by_account(self, account_id: int, org_id: int) -> Optional[Client]:
        """Получить клиента по аккаунту и организации"""
        stmt = select(Client).where(
            Client.account_id == account_id,
            Client.organization_id == org_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def check_manager_access(self, account_id: int, org_id: int) -> None:
        """Проверить, что пользователь является менеджером организации"""
        from db.models import Manager

        stmt = select(Manager).where(
            Manager.account_id == account_id,
            Manager.organization_id == org_id
        )
        result = await self.session.execute(stmt)
        manager = result.scalar_one_or_none()

        if not manager:
            raise PermissionError(f"Пользователь не является менеджером организации {org_id}")

    async def create_client_from_account(
            self,
            data: ClientCreate,
            org_id: int,  # Теперь передается как параметр
            current_user: Account
    ) -> ClientOut:
        """Создание клиента из существующего аккаунта"""
        # Проверяем, что аккаунт существует и активен
        stmt = select(Account).where(
            Account.account_id == data.account_id,
            Account.is_enable == True
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"Аккаунт с id={data.account_id} не найден или деактивирован")

        # Проверяем, не является ли аккаунт уже клиентом в этой организации
        existing = await self._get_client_by_account(data.account_id, org_id)
        if existing:
            raise ClientAlreadyExistsError(data.account_id, org_id)

        client = Client(
            organization_id=org_id,
            account_id=data.account_id
        )

        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)

        return ClientOut.model_validate(client)

    async def create_client_with_new_account(
            self,
            account_data: AccountCreate,
            org_id: int,  # Добавили параметр
            current_user: Account
    ) -> tuple[AccountOut, ClientOut]:
        """Создание нового аккаунта и клиента"""
        from services.account.service import AccountService

        account_service = AccountService(self.session)

        try:
            # Создаем аккаунт
            account = await account_service.register(account_data)

            # Создаем клиента
            client = Client(
                organization_id=org_id,  # Используем переданный org_id
                account_id=account.account_id
            )

            self.session.add(client)
            await self.session.commit()
            await self.session.refresh(client)

            return account, ClientOut.model_validate(client)

        except AccountLoginAlreadyExistsError:
            raise ValueError(f"Аккаунт с логином {account_data.login} уже существует")

    async def get_client(self, client_id: int) -> ClientOut:
        """Получить клиента по ID"""
        stmt = (
            select(Client)
            .options(selectinload(Client.account))
            .where(Client.client_id == client_id)
        )
        result = await self.session.execute(stmt)
        client = result.unique().scalar_one_or_none()

        if not client:
            raise ClientNotFoundError(client_id)

        return ClientOut.model_validate(client)

    async def get_client_by_account(self, account_id: int, org_id: int) -> ClientOut:
        """Получить клиента по ID аккаунта и организации"""
        client = await self._get_client_by_account(account_id, org_id)
        if not client:
            raise ClientNotFoundError(f"Клиент с account_id={account_id} не найден")

        return ClientOut.model_validate(client)

    async def get_client_with_bookings(self, client_id: int) -> ClientWithBookingsOut:
        """Получить клиента с его записями (только для чтения)"""
        stmt = (
            select(Client)
            .options(selectinload(Client.account))
            .where(Client.client_id == client_id)
        )
        result = await self.session.execute(stmt)
        client = result.unique().scalar_one_or_none()

        if not client:
            raise ClientNotFoundError(client_id)

        # Получаем записи клиента
        bookings_stmt = (
            select(Booking)
            .where(Booking.client_id == client_id)
            .order_by(Booking.booking_dt)
        )
        bookings_result = await self.session.execute(bookings_stmt)
        bookings = bookings_result.scalars().all()

        # Преобразуем записи в нужный формат
        bookings_info = []
        for booking in bookings:
            # Получаем информацию об услуге и мастере
            service_stmt = (
                select(ServiceMaster, Master)
                .join(Master, ServiceMaster.master_id == Master.master_id)
                .where(ServiceMaster.service_master_id == booking.service_id)
            )
            service_result = await self.session.execute(service_stmt)
            service_master, master = service_result.first() or (None, None)

            bookings_info.append(BookingInfoOut(
                booking_id=booking.booking_id,
                service_name=None,  # Можно добавить из Service
                master_name=f"{master.account.first_name} {master.account.last_name}" if master and master.account else None,
                booking_dt=booking.booking_dt,
                status=booking.status,
                price=None  # Можно добавить из ServiceMaster
            ))

        result = ClientWithBookingsOut.model_validate(client)
        result.bookings = bookings_info

        return result

    async def get_org_clients(self, org_id: int) -> List[ClientOut]:
        """Получить всех клиентов организации"""
        stmt = (
            select(Client)
            .options(selectinload(Client.account))
            .where(Client.organization_id == org_id)
        )
        result = await self.session.execute(stmt)
        clients = result.unique().scalars().all()

        return [ClientOut.model_validate(c) for c in clients]

    async def get_client_bookings(self, client_id: int, status: Optional[str] = None) -> List[BookingInfoOut]:
        """Получить записи клиента (только для чтения)"""
        client = await self._get_client_by_id(client_id)

        stmt = select(Booking).where(Booking.client_id == client_id)

        if status:
            stmt = stmt.where(Booking.status == status)

        stmt = stmt.order_by(Booking.booking_dt)

        result = await self.session.execute(stmt)
        bookings = result.scalars().all()

        bookings_info = []
        for booking in bookings:
            # Получаем информацию об услуге и мастере
            service_stmt = (
                select(ServiceMaster, Master)
                .join(Master, ServiceMaster.master_id == Master.master_id)
                .options(selectinload(Master.account))
                .where(ServiceMaster.service_master_id == booking.service_id)
            )
            service_result = await self.session.execute(service_stmt)
            row = service_result.first()

            service_master = None
            master = None
            if row:
                service_master, master = row

            bookings_info.append(BookingInfoOut(
                booking_id=booking.booking_id,
                service_name=None,  # Можно добавить из Service
                master_name=f"{master.account.first_name} {master.account.last_name}" if master and master.account else None,
                booking_dt=booking.booking_dt,
                status=booking.status,
                price=service_master.price if service_master else None
            ))

        return bookings_info