"""
Интеграционные тесты BookingService поверх настоящего PostgreSQL
(контейнер поднимается фикстурой postgres_url в conftest.py).
"""

from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select

from db.models import Booking

from tests.conftest import (
    insert_booked_slots,
    insert_free_slots,
    insert_skipped_slots,
    setup_master_schedule,
)


def make_slot(booking_dt: datetime, booking_id: int = 1):
    return Booking(booking_id=booking_id, booking_dt=booking_dt, status="free")


def slots_every_5min(start: datetime, count: int) -> list[Booking]:
    return [
        make_slot(start + timedelta(minutes=5 * i), booking_id=i + 1)
        for i in range(count)
    ]


# ─────────────────────────────────────────────────────────
# _merge_slots — алгоритм склейки 5-мин слотов в интервалы
# ─────────────────────────────────────────────────────────

class TestMergeSlots:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("case", ["empty", "single", "consecutive", "gap", "three_blocks"])
    async def test_merges_slots_into_intervals(self, booking_service, case):
        base = datetime(2024, 1, 1, 9, 0)

        if case == "empty":
            assert booking_service._merge_slots([]) == []
            return

        if case == "single":
            result = booking_service._merge_slots([make_slot(base)])
            assert len(result) == 1
            assert result[0]["from"] == base and result[0]["to"] == base
            return

        if case == "consecutive":
            # 5 слотов подряд (09:00-09:20) → 1 интервал
            result = booking_service._merge_slots(slots_every_5min(base, 5))
            assert len(result) == 1
            assert result[0]["from"] == base
            assert result[0]["to"] == base + timedelta(minutes=20)
            return

        if case == "gap":
            # пробел между блоками → 2 интервала
            block1 = slots_every_5min(datetime(2024, 1, 1, 9, 0), 3)
            block2 = slots_every_5min(datetime(2024, 1, 1, 10, 0), 2)
            result = booking_service._merge_slots(block1 + block2)
            assert len(result) == 2
            assert result[0]["to"] == datetime(2024, 1, 1, 9, 10)
            assert result[1]["from"] == datetime(2024, 1, 1, 10, 0)
            return

        if case == "three_blocks":
            slots = []
            for hour in (9, 11, 14):
                slots += slots_every_5min(datetime(2024, 1, 1, hour, 0), 2)
            result = booking_service._merge_slots(slots)
            assert len(result) == 3
            assert [r["from"].hour for r in result] == [9, 11, 14]


# ─────────────────────────────────────────────────────────
# book_slot
# ─────────────────────────────────────────────────────────

class TestBookSlot:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_duration", [0, -5, 7, 11])
    async def test_invalid_duration_raises(self, booking_service, bad_duration):
        with pytest.raises(ValueError, match="кратной 5"):
            await booking_service.book_slot(
                service_master_id=1,
                client_id=1,
                booking_dt=datetime(2024, 1, 1, 9, 0),
                duration_minutes=bad_duration,
            )

    @pytest.mark.asyncio
    async def test_rolls_back_when_one_slot_already_booked(
            self, booking_service, session,
            organization, master, client, service_master,
    ):
        """
        09:00 free, 09:05 booked, 09:10 free. Попытка взять 15 мин (3 слота)
        должна упасть, и состояние БД остаться нетронутым.
        Покрывает и edge case "часть слотов занята", и транзакционный откат.
        """
        start = datetime(2024, 1, 1, 9, 0)
        await insert_free_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=start, count=1,
        )
        await insert_booked_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            client_id=client.client_id,
            service_id=service_master.service_master_id,
            start=start + timedelta(minutes=5), count=1,
        )
        await insert_free_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=start + timedelta(minutes=10), count=1,
        )

        with pytest.raises(ValueError, match="Требуется 3.*найдено только 2"):
            await booking_service.book_slot(
                service_master_id=service_master.service_master_id,
                client_id=client.client_id,
                booking_dt=start,
                duration_minutes=15,
            )

        rows = (await session.execute(
            select(Booking)
            .where(Booking.master_id == master.master_id)
            .order_by(Booking.booking_dt)
        )).scalars().all()
        statuses = [r.status for r in rows]
        assert statuses == ["free", "booked", "free"]

    @pytest.mark.asyncio
    async def test_happy_path_books_consecutive_slots(
            self, booking_service, session,
            organization, master, client, service_master,
    ):
        booking_dt = datetime(2024, 1, 1, 9, 0)
        await insert_free_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=booking_dt, count=3,
        )

        response = await booking_service.book_slot(
            service_master_id=service_master.service_master_id,
            client_id=client.client_id,
            booking_dt=booking_dt,
            duration_minutes=15,
        )

        assert response.status == "booked"
        assert response.duration_minutes == 15
        assert len(response.booked_slots) == 3

        rows = (await session.execute(
            select(Booking)
            .where(Booking.master_id == master.master_id)
            .order_by(Booking.booking_dt)
        )).scalars().all()
        assert all(r.status == "booked" for r in rows)
        assert all(r.client_id == client.client_id for r in rows)
        assert all(r.service_id == service_master.service_master_id for r in rows)


# ─────────────────────────────────────────────────────────
# cancel_booking
# ─────────────────────────────────────────────────────────

class TestCancelBooking:

    @pytest.mark.asyncio
    async def test_start_slot_not_found_raises(
            self, booking_service, organization, master, client,
    ):
        with pytest.raises(ValueError, match="Стартовый слот не найден"):
            await booking_service.cancel_booking(
                master_id=master.master_id,
                booking_dt=datetime(2024, 1, 1, 9, 0),
                client_id=client.client_id,
            )

    @pytest.mark.asyncio
    async def test_releases_only_consecutive_block(
            self, booking_service, session,
            organization, master, client, service_master,
    ):
        """
        Два блока брони: 09:00-09:10 (3 слота) и 11:00 (1 слот).
        Отмена в 09:00 → освободит только смежные 3, второй блок останется booked.
        """
        await insert_booked_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            client_id=client.client_id,
            service_id=service_master.service_master_id,
            start=datetime(2024, 1, 1, 9, 0), count=3,
        )
        await insert_booked_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            client_id=client.client_id,
            service_id=service_master.service_master_id,
            start=datetime(2024, 1, 1, 11, 0), count=1,
        )

        released = await booking_service.cancel_booking(
            master_id=master.master_id,
            booking_dt=datetime(2024, 1, 1, 9, 0),
            client_id=client.client_id,
        )

        assert released == 3

        morning = (await session.execute(
            select(Booking).where(
                Booking.booking_dt < datetime(2024, 1, 1, 10, 0)
            )
        )).scalars().all()
        assert all(s.status == "free" for s in morning)
        assert all(s.client_id is None and s.service_id is None for s in morning)

        late = (await session.execute(
            select(Booking).where(
                Booking.booking_dt == datetime(2024, 1, 1, 11, 0)
            )
        )).scalar_one()
        assert late.status == "booked"


# ─────────────────────────────────────────────────────────
# clear_master_slots
# ─────────────────────────────────────────────────────────

class TestClearMasterSlots:

    @pytest.mark.asyncio
    async def test_marks_only_free_as_skipped(
            self, booking_service, session,
            organization, master, client, service_master,
    ):
        """free → skipped; booked не трогается."""
        await insert_free_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=datetime(2024, 1, 1, 9, 0), count=2,
        )
        await insert_booked_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            client_id=client.client_id,
            service_id=service_master.service_master_id,
            start=datetime(2024, 1, 1, 10, 0), count=2,
        )

        rows = await booking_service.clear_master_slots(
            master_id=master.master_id,
            start_date=date(2024, 1, 1),
        )

        assert rows == 2

        skipped = (await session.execute(
            select(Booking).where(Booking.status == "skipped")
        )).scalars().all()
        booked = (await session.execute(
            select(Booking).where(Booking.status == "booked")
        )).scalars().all()
        assert len(skipped) == 2
        assert len(booked) == 2


# ─────────────────────────────────────────────────────────
# get_free_slots
# ─────────────────────────────────────────────────────────

class TestGetFreeSlots:

    @pytest.mark.asyncio
    async def test_merges_intervals_and_filters_by_org(
            self, booking_service, session, organization, master,
    ):
        """09:00-09:10 + 11:00 → 2 интервала; запрос с чужой орг → пусто."""
        await insert_free_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=datetime(2024, 1, 1, 9, 0), count=3,
        )
        await insert_free_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=datetime(2024, 1, 1, 11, 0), count=1,
        )

        intervals = await booking_service.get_free_slots(
            master_id=master.master_id,
            start_date=date(2024, 1, 1),
        )
        assert len(intervals) == 2
        assert intervals[0]["from"] == datetime(2024, 1, 1, 9, 0)
        assert intervals[0]["to"] == datetime(2024, 1, 1, 9, 10)
        assert intervals[1]["from"] == datetime(2024, 1, 1, 11, 0)

        wrong_org = await booking_service.get_free_slots(
            master_id=master.master_id,
            start_date=date(2024, 1, 1),
            organization_id=999,
        )
        assert wrong_org == []


# ─────────────────────────────────────────────────────────
# get_booked_slots_intervals
# ─────────────────────────────────────────────────────────

class TestGetBookedSlots:

    @pytest.mark.asyncio
    async def test_intervals_with_total_minutes(
            self, booking_service, session,
            organization, master, client, service_master,
    ):
        """09:00-09:10 (3 слота, 10 мин) + 11:00-11:05 (2 слота, 5 мин) = 15 мин."""
        await insert_booked_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            client_id=client.client_id,
            service_id=service_master.service_master_id,
            start=datetime(2024, 1, 1, 9, 0), count=3,
        )
        await insert_booked_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            client_id=client.client_id,
            service_id=service_master.service_master_id,
            start=datetime(2024, 1, 1, 11, 0), count=2,
        )

        intervals, total = await booking_service.get_booked_slots_intervals(
            master_id=master.master_id,
            start_date=date(2024, 1, 1),
        )

        assert len(intervals) == 2
        assert total == 15


# ─────────────────────────────────────────────────────────
# get_skipped_slots_intervals
# ─────────────────────────────────────────────────────────

class TestGetSkippedSlots:

    @pytest.mark.asyncio
    async def test_merges_skipped_slots(
            self, booking_service, session, organization, master,
    ):
        await insert_skipped_slots(
            session, master_id=master.master_id,
            organization_id=organization.organization_id,
            start=datetime(2024, 1, 1, 9, 0), count=2,
        )

        result = await booking_service.get_skipped_slots_intervals(
            master_id=master.master_id,
            start_date=date(2024, 1, 1),
        )

        assert len(result) == 1
        assert result[0]["from"] == datetime(2024, 1, 1, 9, 0)
        assert result[0]["to"] == datetime(2024, 1, 1, 9, 5)


# ─────────────────────────────────────────────────────────
# generate_slots_for_master (через хранимую процедуру)
# ─────────────────────────────────────────────────────────

class TestGenerateSlotsForMaster:

    @pytest.mark.asyncio
    async def test_master_not_found_raises(self, booking_service):
        with pytest.raises(ValueError, match="Мастер с id 999 не найден"):
            await booking_service.generate_slots_for_master(
                master_id=999,
                start_date=date(2024, 1, 1),
            )

    @pytest.mark.asyncio
    async def test_creates_slots_per_template(
            self, booking_service, session, organization, master,
    ):
        """
        2024-01-01 = понедельник (DOW=1). Шаблон 09:00-09:30 → 6 слотов по 5 минут.
        """
        await setup_master_schedule(
            session,
            master_id=master.master_id,
            organization_id=organization.organization_id,
            week_day=1,
            time_from=time(9, 0),
            time_to=time(9, 30),
        )

        result = await booking_service.generate_slots_for_master(
            master_id=master.master_id,
            start_date=date(2024, 1, 1),
        )

        assert result["slots_created"] == 6
        assert result["organization_id"] == organization.organization_id

        rows = (await session.execute(
            select(Booking).where(Booking.master_id == master.master_id)
        )).scalars().all()
        assert len(rows) == 6
        assert all(s.status == "free" for s in rows)


# ─────────────────────────────────────────────────────────
# generate_slots_for_all_masters
# ─────────────────────────────────────────────────────────

class TestGenerateSlotsForAllMasters:

    @pytest.mark.asyncio
    async def test_missing_org_id_raises(self, booking_service):
        with pytest.raises(ValueError, match="organization_id обязателен"):
            await booking_service.generate_slots_for_all_masters(
                start_date=date(2024, 1, 1)
            )

    @pytest.mark.asyncio
    async def test_aggregates_slots_for_all_masters(
            self, booking_service, session, organization, master,
    ):
        """Один мастер с шаблоном 09:00-09:15 (DOW=1) → 3 слота."""
        await setup_master_schedule(
            session,
            master_id=master.master_id,
            organization_id=organization.organization_id,
            week_day=1,
            time_from=time(9, 0),
            time_to=time(9, 15),
        )

        result = await booking_service.generate_slots_for_all_masters(
            start_date=date(2024, 1, 1),
            organization_id=organization.organization_id,
        )

        assert result["total_masters"] == 1
        assert result["slots_created"] == 3
        assert result["errors"] is None
