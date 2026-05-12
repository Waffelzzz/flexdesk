import os
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.security import hash_password
from db.models import Account, Client, Master, Manager, Organization


async def create_default_user(
    session: AsyncSession,
    login: str,
    password: str,
    role: str,                    # "client" | "master" | "manager"
    organization_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> bool:
    """
    Возвращает True, если пользователь создан, False — если уже существовал.
    """
    result = await session.execute(
        select(Account).where(Account.login == login)
    )
    if result.scalar_one_or_none():
        print(f"Аккаунт {login} ({role}) уже существует → пропуск")
        return False

    try:
        account = Account(
            login=login,
            password=hash_password(password),
            first_name=first_name or role.capitalize(),
            last_name=last_name,
            is_enable=True,
        )
        session.add(account)
        await session.flush()

        if role == "client":
            entity = Client(
                account_id=account.account_id,
                organization_id=organization_id,
            )
        elif role == "master":
            entity = Master(
                account_id=account.account_id,
                organization_id=organization_id,
            )
        elif role == "manager":
            entity = Manager(
                account_id=account.account_id,
                organization_id=organization_id,
            )
        else:
            raise ValueError(f"Неизвестная роль: {role}")

        session.add(entity)
        await session.commit()

        print(f"УСПЕШНО создан {role}: {login} (organization_id={organization_id})")
        return True

    except IntegrityError as e:
        await session.rollback()
        print(f"!!! INTEGRITY ERROR при создании {role} {login} !!!")
        print(f"Сообщение: {e.orig}")
        raise

    except Exception as e:
        await session.rollback()
        print(f"!!! НЕОЖИДАННАЯ ОШИБКА при создании {role} {login} !!!")
        print(f"Тип: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def ensure_default_accounts(session: AsyncSession) -> None:
    """
    Создаёт дефолтную организацию (если её нет) и трёх стандартных пользователей.
    """
    # 1. Проверяем / создаём организацию
    result = await session.execute(
        select(Organization).limit(1)
    )
    org = result.scalar_one_or_none()

    if not org:
        print("Создаём дефолтную организацию...")
        org = Organization(
            name="Default Organization",
            description="Автоматически создана при первом запуске",
            # можно добавить address, contact_info и т.д. при необходимости
        )
        session.add(org)
        await session.flush()  # получаем organization_id
        org_id = org.organization_id
        print(f"Создана организация → id = {org_id}")
    else:
        org_id = org.organization_id
        print(f"Используем существующую организацию → id = {org_id}")

    created_count = 0

    # ────────────── Client ──────────────
    cl_login = os.getenv("CLIENT_LOGIN")
    cl_pass = os.getenv("CLIENT_PASSWORD")
    if cl_login and cl_pass:
        if await create_default_user(
            session=session,
            login=cl_login,
            password=cl_pass,
            role="client",
            organization_id=org_id,
            first_name="Клиент",
            last_name="Тестовый",
        ):
            created_count += 1

    # ────────────── Master ──────────────
    m_login = os.getenv("MASTER_LOGIN")
    m_pass = os.getenv("MASTER_PASSWORD")
    if m_login and m_pass:
        if await create_default_user(
            session=session,
            login=m_login,
            password=m_pass,
            role="master",
            organization_id=org_id,
            first_name="Мастер",
            last_name="Главный",
        ):
            created_count += 1

    # ────────────── Manager ──────────────
    mgr_login = os.getenv("MANAGER_LOGIN")
    mgr_pass = os.getenv("MANAGER_PASSWORD")
    if mgr_login and mgr_pass:
        if await create_default_user(
            session=session,
            login=mgr_login,
            password=mgr_pass,
            role="manager",
            organization_id=org_id,
            first_name="Менеджер",
            last_name="Тест",
        ):
            created_count += 1

    if created_count == 0:
        print("Все дефолтные пользователи уже существуют")
    else:
        print(f"Создано новых пользователей: {created_count}")