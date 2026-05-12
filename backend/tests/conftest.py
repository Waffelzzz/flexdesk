"""
Тестовая инфраструктура: поднимаем PostgreSQL в контейнере (testcontainers),
накатываем схему через Base.metadata.create_all + ручные ALTER/INDEX/PROCEDURE
из alembic-миграции. Каждый тест получает чистую БД (TRUNCATE в teardown).

Внимание: процедура generate_5min_slots_for_master в исходной alembic-миграции
ссылается на несуществующий параметр p_service_id и упадёт при выполнении.
В тестах применяем исправленную версию (p_service_id заменён на NULL),
функционально эквивалентную задумке.
"""

import asyncio
import os
import sys
from datetime import date, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import (  # noqa: E402
    Account,
    Base,
    Booking,
    Client,
    Master,
    Organization,
    Scheduler,
    Service,
    ServiceMaster,
    Template,
)


# Исправленная версия процедуры: NULL вместо отсутствующего p_service_id.
GENERATE_SLOTS_PROCEDURE = """
CREATE OR REPLACE PROCEDURE generate_5min_slots_for_master(
    p_master_id       INT,
    p_start_date      DATE,
    p_end_date        DATE DEFAULT NULL,
    p_organization_id INT  DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id     INT;
    v_step       INTERVAL := '5 minutes';
    v_slot_time  TIME;
    v_slot_dt    TIMESTAMP;
    v_day        DATE;
    v_rec        RECORD;
BEGIN
    IF p_organization_id IS NULL THEN
        SELECT organization_id INTO v_org_id
        FROM masters WHERE master_id = p_master_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Мастер с id % не найден', p_master_id;
        END IF;
    ELSE
        v_org_id := p_organization_id;
    END IF;

    IF p_end_date IS NULL THEN
        p_end_date := p_start_date;
    END IF;

    FOR v_day IN
        SELECT d::date FROM generate_series(p_start_date, p_end_date, '1 day'::interval) d
    LOOP
        FOR v_rec IN
            SELECT t.time_from, t.time_to
            FROM schedulers s
            JOIN templates  t ON t.template_id = s.template_id
            WHERE s.master_id = p_master_id
              AND t.week_day  = EXTRACT(DOW FROM v_day)::smallint
              AND t.organization_id = v_org_id
            ORDER BY t.time_from
        LOOP
            v_slot_time := v_rec.time_from;
            WHILE v_slot_time < v_rec.time_to LOOP
                v_slot_dt := v_day + v_slot_time;
                INSERT INTO booking (
                    client_id, service_id, master_id,
                    booking_dt, status, organization_id
                )
                VALUES (
                    NULL, NULL, p_master_id,
                    v_slot_dt, 'free', v_org_id
                )
                ON CONFLICT (booking_dt, master_id) DO NOTHING;
                v_slot_time := v_slot_time + v_step;
            END LOOP;
        END LOOP;
    END LOOP;
END;
$$;
"""

TABLES_TO_TRUNCATE = (
    "booking",
    "service_masters",
    "services",
    "schedulers",
    "templates",
    "masters",
    "clients",
    "managers",
    "accounts",
    "organizations",
)

# ─────────────────────────────────────────────────────────
# session-scoped: контейнер + схема
# ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def postgres_url():
    """Поднимает контейнер postgres:17, готовит схему, отдаёт async DSN."""
    container = PostgresContainer("postgres:17-alpine")
    container.start()
    try:
        sync_url = container.get_connection_url()  # postgresql+psycopg2://...
        async_url = sync_url.replace("psycopg2", "asyncpg")

        async def setup():
            engine = create_async_engine(async_url)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # client_id / service_id у бронирований должны быть NULLABLE
                # (status='free' слоты не привязаны к клиенту/услуге)
                await conn.execute(text(
                    "ALTER TABLE booking ALTER COLUMN client_id DROP NOT NULL"
                ))
                await conn.execute(text(
                    "ALTER TABLE booking ALTER COLUMN service_id DROP NOT NULL"
                ))
                await conn.execute(text(
                    "ALTER TABLE booking "
                    "ADD CONSTRAINT uq_booking_dt_master "
                    "UNIQUE (booking_dt, master_id)"
                ))
                await conn.execute(text(GENERATE_SLOTS_PROCEDURE))
            await engine.dispose()

        asyncio.run(setup())
        yield async_url
    finally:
        container.stop()

# ─────────────────────────────────────────────────────────
# function-scoped: engine, session, очистка
# ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def engine(postgres_url):
    eng = create_async_engine(postgres_url, future=True)
    yield eng
    await eng.dispose()

@pytest_asyncio.fixture
async def session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as s:
        yield s

    # очистка всех таблиц после теста
    async with engine.begin() as conn:
        await conn.execute(text(
            f"TRUNCATE {', '.join(TABLES_TO_TRUNCATE)} "
            "RESTART IDENTITY CASCADE"
        ))

# ─────────────────────────────────────────────────────────
# Фикстуры сервисов
# ─────────────────────────────────────────────────────────

@pytest.fixture
def booking_service(session):
    from services.booking.service import BookingService
    return BookingService(session)

# ─────────────────────────────────────────────────────────
# Фабрики тестовых данных
# ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def organization(session) -> Organization:
    org = Organization(name="Test org", is_enable=True)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org

async def _make_account(session, login: str) -> Account:
    acc = Account(login=login, is_enable=True)
    session.add(acc)
    await session.commit()
    await session.refresh(acc)
    return acc

@pytest_asyncio.fixture
async def master(session, organization) -> Master:
    acc = await _make_account(session, "master_login")
    m = Master(
        account_id=acc.account_id,
        organization_id=organization.organization_id,
    )
    session.add(m)
    await session.commit()
    await session.refresh(m)
    return m

@pytest_asyncio.fixture
async def client(session, organization) -> Client:
    acc = await _make_account(session, "client_login")
    c = Client(
        account_id=acc.account_id,
        organization_id=organization.organization_id,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c

@pytest_asyncio.fixture
async def service_master(session, organization, master) -> ServiceMaster:
    svc = Service(
        organization_id=organization.organization_id,
        name="Стрижка",
    )
    session.add(svc)
    await session.commit()
    await session.refresh(svc)

    sm = ServiceMaster(
        service_id=svc.service_pk,
        master_id=master.master_id,
        organization_id=organization.organization_id,
        duration=15,
        is_enable=True,
    )
    session.add(sm)
    await session.commit()
    await session.refresh(sm)
    return sm

# ─────────────────────────────────────────────────────────
# Хелперы
# ─────────────────────────────────────────────────────────

async def insert_free_slots(
        session: AsyncSession,
        master_id: int,
        organization_id: int,
        start: datetime,
        count: int,
        step_minutes: int = 5,
) -> list[Booking]:
    """Создаёт count свободных слотов с шагом 5 минут."""
    slots = [
        Booking(
            master_id=master_id,
            organization_id=organization_id,
            booking_dt=start + timedelta(minutes=step_minutes * i),
            status="free",
            client_id=None,
            service_id=None,
        )
        for i in range(count)
    ]
    session.add_all(slots)
    await session.commit()
    for s in slots:
        await session.refresh(s)
    return slots

async def insert_booked_slots(
        session: AsyncSession,
        master_id: int,
        organization_id: int,
        client_id: int,
        service_id: int,
        start: datetime,
        count: int,
        step_minutes: int = 5,
) -> list[Booking]:
    """Создаёт count забронированных слотов с шагом 5 минут."""
    slots = [
        Booking(
            master_id=master_id,
            organization_id=organization_id,
            booking_dt=start + timedelta(minutes=step_minutes * i),
            status="booked",
            client_id=client_id,
            service_id=service_id,
        )
        for i in range(count)
    ]
    session.add_all(slots)
    await session.commit()
    for s in slots:
        await session.refresh(s)
    return slots

async def insert_skipped_slots(
        session: AsyncSession,
        master_id: int,
        organization_id: int,
        start: datetime,
        count: int,
        step_minutes: int = 5,
) -> list[Booking]:
    slots = [
        Booking(
            master_id=master_id,
            organization_id=organization_id,
            booking_dt=start + timedelta(minutes=step_minutes * i),
            status="skipped",
            client_id=None,
            service_id=None,
        )
        for i in range(count)
    ]
    session.add_all(slots)
    await session.commit()
    return slots

async def setup_master_schedule(
        session: AsyncSession,
        master_id: int,
        organization_id: int,
        week_day: int,
        time_from,
        time_to,
) -> Scheduler:
    """Создаёт template + scheduler чтобы процедура нашла расписание мастера."""
    tpl = Template(
        organization_id=organization_id,
        week_day=week_day,
        time_from=time_from,
        time_to=time_to,
        template_name="test",
    )
    session.add(tpl)
    await session.commit()
    await session.refresh(tpl)

    sch = Scheduler(master_id=master_id, template_id=tpl.template_id)
    session.add(sch)
    await session.commit()
    await session.refresh(sch)
    return sch
