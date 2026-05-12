from datetime import date, datetime
from typing import List, Optional
from datetime import timedelta

from sqlalchemy import and_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Booking, Master, ServiceMaster
from schemas.booking import BookingResponse, BookedSlotInfo


class BookingService:
    """Сервис для работы с бронированиями и слотами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_slots_for_master(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ) -> dict:
        """
        Генерирует слоты для мастера используя хранимую процедуру.
        Только для менеджеров организации.
        """
        master = await self._get_master(master_id)
        if not master:
            raise ValueError(f"Мастер с id {master_id} не найден")

        end_date = end_date or start_date

        stmt = text("""
            CALL generate_5min_slots_for_master(
                p_master_id => :master_id,
                p_start_date => :start_date,
                p_end_date => :end_date,
                p_organization_id => :organization_id
            )
        """)

        await self.session.execute(
            stmt,
            {
                "master_id": master_id,
                "start_date": start_date,
                "end_date": end_date,
                "organization_id": organization_id or master.organization_id
            }
        )
        await self.session.commit()

        # Получаем количество созданных слотов
        slots_count = await self._get_slots_count(
            master_id,
            start_date,
            end_date,
            organization_id or master.organization_id
        )

        return {
            "master_id": master_id,
            "organization_id": organization_id or master.organization_id,
            "start_date": start_date,
            "end_date": end_date,
            "slots_created": slots_count,
            "message": f"Создано {slots_count} слотов для мастера {master_id}"
        }

    async def _get_master(self, master_id: int) -> Optional[Master]:
        """Получает мастера по id"""
        result = await self.session.execute(
            select(Master).where(Master.master_id == master_id)
        )
        return result.scalar_one_or_none()

    async def _get_slots_count(
            self,
            master_id: int,
            start_date: date,
            end_date: date,
            organization_id: int
    ) -> int:
        """Подсчитывает количество слотов за период"""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.master_id == master_id,
                    Booking.organization_id == organization_id,
                    Booking.booking_dt >= start_dt,
                    Booking.booking_dt <= end_dt,
                    Booking.status == 'free'
                )
            )
        )
        slots = result.scalars().all()
        return len(slots)

    async def get_free_slots(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ) -> List[Booking]:  # Return list of Booking objects
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date or start_date, datetime.max.time())

        query = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.status == "free",
                Booking.booking_dt >= start_dt,
                Booking.booking_dt <= end_dt
            )
        )

        if organization_id:
            query = query.where(Booking.organization_id == organization_id)

        query = query.order_by(Booking.booking_dt)

        result = await self.session.execute(query)
        slots = result.scalars().all()

        return slots

    async def clear_master_slots(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ) -> int:
        """
        Помечает свободные слоты как skipped за период
        """

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date or start_date, datetime.max.time())

        query = (
            update(Booking)
            .where(
                and_(
                    Booking.master_id == master_id,
                    Booking.status == "free",
                    Booking.booking_dt >= start_dt,
                    Booking.booking_dt <= end_dt
                )
            )
            .values(status="skipped")
        )

        if organization_id:
            query = query.where(Booking.organization_id == organization_id)

        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount

    async def generate_slots_for_all_masters(
            self,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ) -> dict:
        """
        Генерирует слоты для всех мастеров организации используя хранимую процедуру.
        Только для менеджеров организации.
        """
        if not organization_id:
            raise ValueError("organization_id обязателен для этого метода")

        end_date = end_date or start_date

        # Получаем всех мастеров организации
        masters_result = await self.session.execute(
            select(Master.master_id).where(Master.organization_id == organization_id)
        )
        masters = masters_result.scalars().all()

        if not masters:
            return {
                "organization_id": organization_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_masters": 0,
                "slots_created": 0,
                "message": "В организации нет мастеров"
            }

        total_slots = 0
        errors = []

        for master_id in masters:
            try:
                stmt = text("""
                    CALL generate_5min_slots_for_master(
                        p_master_id => :master_id,
                        p_start_date => :start_date,
                        p_end_date => :end_date,
                        p_organization_id => :organization_id
                    )
                """)

                await self.session.execute(
                    stmt,
                    {
                        "master_id": master_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "organization_id": organization_id
                    }
                )

                slots_count = await self._get_slots_count(
                    master_id,
                    start_date,
                    end_date,
                    organization_id
                )
                total_slots += slots_count

            except Exception as e:
                errors.append(f"Мастер {master_id}: {str(e)}")

        await self.session.commit()

        return {
            "organization_id": organization_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_masters": len(masters),
            "slots_created": total_slots,
            "errors": errors if errors else None,
            "message": f"Создано {total_slots} слотов для {len(masters)} мастеров"
        }

    def _merge_slots(self, slots: List[Booking], step_minutes: int = 5):
        if not slots:
            return []

        intervals = []
        start = slots[0].booking_dt
        prev = slots[0].booking_dt

        for slot in slots[1:]:
            current = slot.booking_dt

            if (current - prev).total_seconds() > step_minutes * 60:
                intervals.append({
                    "from": start,
                    "to": prev
                })
                start = current

            prev = current

        intervals.append({
            "from": start,
            "to": prev
        })

        return intervals

    async def get_free_slots_raw(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ) -> List[Booking]:

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date or start_date, datetime.max.time())

        query = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.status == "free",
                Booking.booking_dt >= start_dt,
                Booking.booking_dt <= end_dt
            )
        )

        if organization_id:
            query = query.where(Booking.organization_id == organization_id)

        query = query.order_by(Booking.booking_dt)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_free_slots(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ):
        slots = await self.get_free_slots_raw(master_id, start_date, end_date, organization_id)
        return self._merge_slots(slots)

    async def book_slot(
            self,
            service_master_id: int,
            client_id: int,
            booking_dt: datetime,
            duration_minutes: int,
            organization_id: Optional[int] = None
    ) -> BookingResponse:
        """
        Бронирует услугу, обновляя существующие атомарные слоты со статусом 'free'.
        """
        if duration_minutes <= 0 or duration_minutes % 5 != 0:
            raise ValueError("Длительность услуги должна быть положительной и кратной 5 минутам.")

        sm_stmt = select(ServiceMaster).where(
            ServiceMaster.service_master_id == service_master_id
        )
        if organization_id:
            sm_stmt = sm_stmt.where(ServiceMaster.organization_id == organization_id)

        result = await self.session.execute(sm_stmt)
        service_master = result.scalar_one_or_none()

        if not service_master:
            raise ValueError(f"ServiceMaster с id {service_master_id} не найден в организации.")

        master_id = service_master.master_id
        org_id = organization_id or service_master.organization_id

        step_minutes = 5
        num_slots = duration_minutes // step_minutes

        slot_datetimes: List[datetime] = []
        current_dt = booking_dt.replace(second=0, microsecond=0)

        for i in range(num_slots):
            slot_datetimes.append(current_dt)
            current_dt += timedelta(minutes=step_minutes)

        check_query = select(Booking.booking_id).where(
            and_(
                Booking.master_id == master_id,
                Booking.booking_dt.in_(slot_datetimes),
                Booking.status == "free"
            )
        )
        if org_id:
            check_query = check_query.where(Booking.organization_id == org_id)

        result = await self.session.execute(check_query)
        free_slot_ids = result.scalars().all()

        if len(free_slot_ids) != num_slots:
            raise ValueError(
                f"Невозможно забронировать. Требуется {num_slots} свободных слотов, "
                f"найдено только {len(free_slot_ids)}. Некоторые слоты уже заняты или отсутствуют."
            )

        # 4. Обновляем все слоты (самое важное изменение!)
        update_stmt = update(Booking).where(
            Booking.booking_id.in_(free_slot_ids)
        ).values(
            client_id=client_id,
            service_id=service_master_id,
            status="booked"
        )

        await self.session.execute(update_stmt)

        select_updated = select(Booking).where(Booking.booking_id.in_(free_slot_ids))
        result = await self.session.execute(select_updated)
        updated_slots = result.scalars().all()

        updated_slots.sort(key=lambda x: x.booking_dt)

        booked_slots_info = [
            BookedSlotInfo(booking_id=slot.booking_id, booking_dt=slot.booking_dt)
            for slot in updated_slots
        ]

        await self.session.commit()

        main_slot = updated_slots[0]

        return BookingResponse(
            booking_id=main_slot.booking_id,
            client_id=client_id,
            service_master_id=service_master_id,
            master_id=master_id,
            booking_dt=booking_dt,
            duration_minutes=duration_minutes,
            status="booked",
            organization_id=org_id,
            booked_slots=booked_slots_info
        )

    async def get_booked_slots_raw(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
    ) -> List[Booking]:
        """
        Возвращает сырые забронированные слоты (для дальнейшей обработки интервалов)
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date or start_date, datetime.max.time())

        query = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.status == "booked",
                Booking.booking_dt >= start_dt,
                Booking.booking_dt <= end_dt
            )
        )

        query = query.order_by(Booking.booking_dt)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_booked_slots_intervals(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
    ) -> tuple[List[dict], int]:
        """
        Возвращает забронированные слоты в виде merged интервалов + общую длительность в минутах
        """
        slots = await self.get_booked_slots_raw(
            master_id=master_id,
            start_date=start_date,
            end_date=end_date,
        )

        if not slots:
            return [], 0

        intervals = self._merge_slots(slots)

        total_minutes = 0
        for interval in intervals:
            duration = (interval["to"] - interval["from"]).total_seconds() / 60
            total_minutes += int(duration)

        return intervals, total_minutes

    async def get_skipped_slots_intervals(
            self,
            master_id: int,
            start_date: date,
            end_date: Optional[date] = None,
            organization_id: Optional[int] = None
    ) -> list[dict]:

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date or start_date, datetime.max.time())

        query = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.status == "skipped",
                Booking.booking_dt >= start_dt,
                Booking.booking_dt <= end_dt
            )
        )

        if organization_id:
            query = query.where(Booking.organization_id == organization_id)

        query = query.order_by(Booking.booking_dt)

        result = await self.session.execute(query)
        slots = result.scalars().all()

        if not slots:
            return []

        merged = self._merge_slots(slots)

        return merged

    async def cancel_booking(
            self,
            master_id: int,
            booking_dt: datetime,
            client_id: int,
            organization_id: Optional[int] = None
    ) -> int:
        """
        Отмена записи:
        освобождает все подряд идущие слоты одной записи
        через проверку client_id + service_id
        """

        start_stmt = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                Booking.booking_dt == booking_dt,
                Booking.client_id == client_id,
                Booking.status == "booked"
            )
        )

        if organization_id:
            start_stmt = start_stmt.where(Booking.organization_id == organization_id)

        result = await self.session.execute(start_stmt)
        start_slot = result.scalar_one_or_none()

        if not start_slot:
            raise ValueError("Стартовый слот не найден или не принадлежит клиенту")

        service_id = start_slot.service_id

        step = timedelta(minutes=5)
        current_dt = booking_dt

        slots_to_free = []

        while True:
            stmt = select(Booking).where(
                and_(
                    Booking.master_id == master_id,
                    Booking.booking_dt == current_dt,
                    Booking.client_id == client_id,
                    Booking.service_id == service_id,
                    Booking.status == "booked"
                )
            )

            if organization_id:
                stmt = stmt.where(Booking.organization_id == organization_id)

            result = await self.session.execute(stmt)
            slot = result.scalar_one_or_none()

            if not slot:
                break

            slots_to_free.append(slot.booking_id)
            current_dt += step

        if not slots_to_free:
            raise ValueError("Не найдено слотов для отмены")

        update_stmt = (
            update(Booking)
            .where(Booking.booking_id.in_(slots_to_free))
            .values(
                client_id=None,
                service_id=None,
                status="free"
            )
        )

        await self.session.execute(update_stmt)
        await self.session.commit()

        return len(slots_to_free)
