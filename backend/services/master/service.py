from sqlalchemy import select, exists, update, union_all, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy.orm import selectinload
from datetime import date, datetime, timedelta

from schemas.account import AccountCreate, AccountOut
from services.account.exceptions import AccountLoginAlreadyExistsError
from services.master.exceptions import NoRelationToOrganizationError, NotManagerOfOrganizationError, ServiceMasterNotFoundError
from db.models import (
    Organization,
    Manager,
    Master,
    ServiceMaster,
    Account,
    Client,
    Booking
)
from schemas.master import (
    MasterCreate,
    MasterOut,
    ServiceMasterOut,
    WorkTimeSlot,
    MasterWorkDayOut, MasterWorkDayDetailedOut, WorkSlotDetailed, SlotClient, SlotService
)

class MasterService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_master_even_disabled(self, id: int) -> ServiceMaster:
        stmt = (
            select( ServiceMaster)
            .where(ServiceMaster.service_master_id == id)
            )
        result = await self.session.execute(stmt)
        master = result.scalar_one_or_none()
        if not master:
            raise ServiceMasterNotFoundError(id)
        return master

    async def _require_manager_for_org(self, current_user: Account, id: int):
        result = await self.session.execute(select(Master.organization_id).where(Master.master_id == id))
        org_id = result.scalar_one_or_none()
        stmt = select(exists().where(
            Manager.account_id == current_user.account_id,
            Manager.organization_id == org_id
        ))
        result = await self.session.execute(stmt)
        if not result.scalar_one():
            raise NotManagerOfOrganizationError(current_user.account_id, self.get_org_id(id))

    async def _require_relation_to_org(self, current_user: Account, org_id: int):
        """Проверяет, имеет ли пользователь отношение к организации (менеджер, мастер или клиент)"""
        if org_id is None:
            raise NoRelationToOrganizationError(current_user.account_id, org_id)

        stmt = select(exists().where(
            or_(
                # Менеджер
                and_(
                    Manager.account_id == current_user.account_id,
                    Manager.organization_id == org_id,
                    Organization.organization_id == org_id,
                    Organization.is_enable.is_(True)
                ),
                # Мастер
                and_(
                    Master.account_id == current_user.account_id,
                    Master.organization_id == org_id,
                    Organization.organization_id == org_id,
                    Organization.is_enable.is_(True)
                ),
                # Клиент
                and_(
                    Client.account_id == current_user.account_id,
                    Client.organization_id == org_id,
                    Organization.organization_id == org_id,
                    Organization.is_enable.is_(True)
                ),
            )
        ))

        result = await self.session.scalar(stmt)

        if not result:
            raise NoRelationToOrganizationError(current_user.account_id, org_id)

    async def get_org_id(self, current_user):
        subquery = union_all(
            select(Manager.organization_id).where(Manager.account_id == current_user.account_id),
            select(Master.organization_id).where(Master.account_id == current_user.account_id),
            select(Client.organization_id).where(Client.account_id == current_user.account_id),
        ).subquery()
        
        query = select(subquery.c.organization_id).limit(1)
        result = await self.session.execute(query)
        org_id = result.scalar_one_or_none()
        
        if not org_id:
            raise ValueError("Текущий пользователь не является менеджером или не привязан к организации")
        return org_id

    async def create_master_from_account(
            self,
            data: MasterCreate,
            current_manager: Account
    ) -> MasterOut:
        """
        Создание мастера для уже существующего аккаунта.
        Аккаунт должен быть зарегистрирован заранее.
        """
        org_id = await self.get_org_id(current_manager)

        # Проверяем, что аккаунт существует и активен
        stmt = select(Account).where(
            Account.account_id == data.account_id,
            Account.is_enable == True
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"Аккаунт с id={data.account_id} не найден или деактивирован")

        # Проверяем, не является ли аккаунт уже мастером в этой организации
        stmt = select(Master).where(
            Master.account_id == data.account_id,
            Master.organization_id == org_id
        )
        result = await self.session.execute(stmt)
        existing_master = result.scalar_one_or_none()

        if existing_master:
            raise ValueError(f"Аккаунт {account.login} уже является мастером в этой организации")

        master = Master(
            organization_id=org_id,
            account_id=data.account_id,
            specialization=data.specialization,
            grade=data.grade
        )

        self.session.add(master)
        await self.session.commit()
        await self.session.refresh(master)

        return MasterOut.model_validate(master)

    async def create_master_with_new_account(
            self,
            account_data: AccountCreate,
            master_data: MasterCreate,
            current_manager: Account
    ) -> tuple[AccountOut, MasterOut]:
        """
        Создание нового аккаунта и мастера в одной транзакции.
        """
        from services.account.service import AccountService

        org_id = await self.get_org_id(current_manager)

        # Создаем аккаунт
        account_service = AccountService(self.session)

        try:
            # Регистрируем аккаунт
            account = await account_service.register(account_data)

            # Создаем мастера
            master = Master(
                organization_id=org_id,
                account_id=account.account_id,
                specialization=master_data.specialization,
                grade=master_data.grade
            )

            self.session.add(master)
            await self.session.commit()
            await self.session.refresh(master)

            return account, MasterOut.model_validate(master)

        except AccountLoginAlreadyExistsError:
            raise ValueError(f"Аккаунт с логином {account_data.login} уже существует")
    
    async def get_org_masters(
            self,
            org_id: int,
            current_user: Account,
    ) -> List[MasterOut]:
        

        stmt = (
            select(Master)
            .options(selectinload(Master.account))
            .where(Master.organization_id == org_id)
        )

        result = await self.session.execute(stmt)
        masters = result.scalars().all()

        return [MasterOut.model_validate(m) for m in masters]
    
    async def get_master(
            self,
            id: int,
            current_user: Account,
    ) -> MasterOut:
        

        stmt = (
            select(Master)
            .options(selectinload(Master.account))
            .where(Master.master_id == id)
        )

        result = await self.session.execute(stmt)
        master = result.unique().scalar_one_or_none()

        await self._require_relation_to_org(current_user, await self.get_org_id(current_user))

        return MasterOut.model_validate(master)

    def _merge_slots(self, slots: List[Booking], step_minutes: int = 5):
        if not slots:
            return []

        slots.sort(key=lambda x: x.booking_dt)

        intervals = []

        start = slots[0].booking_dt
        prev = slots[0].booking_dt

        for slot in slots[1:]:
            current = slot.booking_dt

            if (current - prev).total_seconds() > step_minutes * 60:
                intervals.append({
                    "from": start,
                    "to": prev + timedelta(minutes=step_minutes)
                })
                start = current

            prev = current

        intervals.append({
            "from": start,
            "to": prev + timedelta(minutes=step_minutes)
        })

        return intervals


    async def get_master_work_day(
            self,
            master_id: int,
            work_date: date,
            current_user: Account,
    ) -> MasterWorkDayOut:

        master_stmt = select(Master).where(Master.master_id == master_id)
        master_result = await self.session.execute(master_stmt)
        master = master_result.scalar_one_or_none()

        if not master:
            raise ValueError(f"Мастер с id={master_id} не найден")

        await self._require_relation_to_org(current_user, master.organization_id)

        start_dt = datetime.combine(work_date, datetime.min.time())
        end_dt = datetime.combine(work_date, datetime.max.time())

        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.master_id == master_id,
                    Booking.organization_id == master.organization_id,
                    Booking.status.in_(["free", "booked"]),
                    Booking.booking_dt >= start_dt,
                    Booking.booking_dt <= end_dt
                )
            ).order_by(Booking.booking_dt)
        )

        free_slots = result.scalars().all()

        if not free_slots:
            return MasterWorkDayOut(
                master_id=master_id,
                date=work_date,
                slots=[],
                is_working_day=False
            )

        # --- merge 5-минутных слотов в интервалы ---
        merged = self._merge_slots(free_slots)

        slots: List[WorkTimeSlot] = [
            WorkTimeSlot(
                time_from=interval["from"].time(),
                time_to=interval["to"].time()
            )
            for interval in merged
        ]

        return MasterWorkDayOut(
            master_id=master_id,
            date=work_date,
            slots=slots,
            is_working_day=len(slots) > 0
        )

    
    async def get_service_master(
        self,
        id: int,
        current_user: Account,
    ) -> List[ServiceMasterOut]:
        

        stmt = (
            select(ServiceMaster)
            .where(ServiceMaster.master_id == id)
        )

        result = await self.session.execute(stmt)
        services = result.scalars().all()

        return [ServiceMasterOut.model_validate(s) for s in services]
    
    async def get_service_master_active(
        self,
        id: int,
        current_user: Account,
    ) -> List[ServiceMasterOut]:
        

        stmt = (
            select(ServiceMaster)
            .where(ServiceMaster.master_id == id, ServiceMaster.is_enable)
        )

        result = await self.session.execute(stmt)
        services = result.scalars().all()

        return [ServiceMasterOut.model_validate(s) for s in services]

    
    async def deactivate_servicemaster(
        self,
        service_master_id: int,
        current_user: Account,
    ) -> dict:
        service_master = await self._get_master_even_disabled(service_master_id)
        await self._require_manager_for_org(current_user, service_master.organization_id)

        if not service_master.is_enable:
            return {"message": f"Услуга мастера {service_master_id} уже деактивирована"}

        stmt = (
            update(ServiceMaster)
            .where(ServiceMaster.service_master_id == service_master_id)
            .values(is_enable=False)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Услуга мастера {service_master_id} деактивирована(мягкое удаление)"}
    
    async def activate_service_master(
        self,
        service_master_id: int,
        current_user: Account,
    ) -> dict:
        service_master = await self._get_master_even_disabled(service_master_id)
        await self._require_manager_for_org(current_user, service_master.organization_id)

        if service_master.is_enable:
            return {"message": f"Услуга мастера {service_master_id} уже активирована"}

        stmt = (
            update(ServiceMaster)
            .where(ServiceMaster.service_master_id == service_master_id)
            .values(is_enable=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Услуга мастера {service_master_id} активирована"}

    def _merge_slots_detailed(self, bookings: List[Booking], step_minutes: int = 5):
        if not bookings:
            return []

        bookings.sort(key=lambda x: x.booking_dt)

        def get_key(b: Booking):
            return (
                b.status,
                b.client.client_id if b.client else None,
                b.service_master.service_master_id if b.service_master else None,
            )

        intervals = []

        start = bookings[0]
        prev = bookings[0]

        for current in bookings[1:]:
            same_block = (
                    get_key(current) == get_key(prev)
                    and (current.booking_dt - prev.booking_dt).total_seconds() <= step_minutes * 60
            )

            if not same_block:
                intervals.append((start, prev))
                start = current

            prev = current

        intervals.append((start, prev))

        return intervals

    async def get_master_work_day_detailed(
            self,
            master_id: int,
            work_date: date,
            current_user: Account,
    ) -> MasterWorkDayDetailedOut:

        master = (
            await self.session.execute(
                select(Master).where(Master.master_id == master_id)
            )
        ).scalar_one_or_none()

        if not master:
            raise ValueError(f"Мастер с id={master_id} не найден")

        await self._require_relation_to_org(current_user, master.organization_id)

        start_dt = datetime.combine(work_date, datetime.min.time())
        end_dt = datetime.combine(work_date, datetime.max.time())

        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.client).selectinload(Client.account),
                selectinload(Booking.service_master)
            )
            .where(
                Booking.master_id == master_id,
                Booking.organization_id == master.organization_id,
                Booking.booking_dt >= start_dt,
                Booking.booking_dt <= end_dt,
            )
            .order_by(Booking.booking_dt)
        )

        bookings = (await self.session.execute(stmt)).scalars().all()

        if not bookings:
            return MasterWorkDayDetailedOut(
                master_id=master_id,
                date=work_date,
                slots=[],
                is_working_day=False
            )

        merged = self._merge_slots_detailed(bookings)

        slots = []

        for start, end in merged:
            slot = WorkSlotDetailed(
                time_from=start.booking_dt.time(),
                time_to=(end.booking_dt + timedelta(minutes=5)).time(),
                status=start.status,
            )

            if start.status == "booked":
                slot.client = (
                    SlotClient(
                        id=start.client.client_id,
                        name=start.client.account.login
                    )
                    if start.client else None
                )

                slot.service = (
                    SlotService(
                        id=start.service_master.service_master_id,
                        name=getattr(start.service_master, "name", None)
                    )
                    if start.service_master else None
                )

            slots.append(slot)

        return MasterWorkDayDetailedOut(
            master_id=master_id,
            date=work_date,
            slots=slots,
            is_working_day=True
        )