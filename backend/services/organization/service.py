from typing import Optional, List

from sqlalchemy import select, exists, update, delete, union_all, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import union

from db.models import Organization, Manager, Master, Client, Account
from schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationOut
from services.organization.exceptions import (
    OrganizationNotFoundError,
    NotManagerOfOrganizationError,
    NoRelationToOrganizationError,
    OrganizationDisabledError,
)


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_active_organization_or_raise(self, org_id: int) -> Organization:
        stmt = select(Organization).where(
            Organization.organization_id == org_id,
            Organization.is_enable.is_(True)
        )

        result = await self.session.execute(stmt)
        org = result.scalar_one_or_none()

        if org is None:
            exists_stmt = select(1).where(Organization.organization_id == org_id)
            exists_result = await self.session.execute(exists_stmt)
            exists = exists_result.scalar() is not None

            if exists:
                raise OrganizationDisabledError(org_id)
            else:
                raise OrganizationNotFoundError(org_id)

        return org

    async def _get_organization_even_disabled(self, org_id: int) -> Organization:
        stmt = select(Organization).where(Organization.organization_id == org_id)
        result = await self.session.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise OrganizationNotFoundError(org_id)
        return org

    async def _require_manager_for_org(self, current_user: Account, org_id: int):
        stmt = select(exists().where(
            Manager.account_id == current_user.account_id,
            Manager.organization_id == org_id
        ))
        result = await self.session.execute(stmt)
        if not result.scalar_one():
            raise NotManagerOfOrganizationError(current_user.account_id, org_id)

    async def _require_relation_to_org(self, current_user: Account, org_id: int):
        stmt = union_all(
            select(exists().where(
                Manager.account_id == current_user.account_id,
                Manager.organization_id == org_id,
                Organization.organization_id == org_id,
                Organization.is_enable.is_(True)
            )),
            select(exists().where(
                Master.account_id == current_user.account_id,
                Master.organization_id == org_id,
                Organization.organization_id == org_id,
                Organization.is_enable.is_(True)
            )),
            select(exists().where(
                Client.account_id == current_user.account_id,
                Client.organization_id == org_id,
                Organization.organization_id == org_id,
                Organization.is_enable.is_(True)
            )),
        ).limit(1)

        result = await self.session.scalar(stmt)

        if not result:
            raise NoRelationToOrganizationError(current_user.account_id, org_id)

    # ─── Только менеджер ─────────────────────────────────────────────────────

    async def create_organization(
        self,
        data: OrganizationCreate,
        current_user: Account,
    ) -> OrganizationOut:
        org = Organization(
            name=data.name,
            description=data.description,
            contact_info=data.contact_info,
            address=data.address,
            time_gap=data.time_gap,
            granular_step=data.granular_step,
            admin_id=current_user.account_id,
            is_enable=True,           # явно
        )
        self.session.add(org)
        await self.session.flush()

        manager = Manager(
            account_id=current_user.account_id,
            organization_id=org.organization_id,
        )
        self.session.add(manager)

        await self.session.commit()
        await self.session.refresh(org)

        return OrganizationOut.model_validate(org)

    async def update_organization(
        self,
        org_id: int,
        data: OrganizationUpdate,
        current_user: Account,
    ) -> OrganizationOut:
        org = await self._get_organization_even_disabled(org_id)
        await self._require_manager_for_org(current_user, org_id)

        update_data = data.model_dump(exclude_unset=True)
        # Запрещаем менять is_enable через обычное обновление
        update_data.pop("is_enable", None)

        if update_data:
            stmt = (
                update(Organization)
                .where(Organization.organization_id == org_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            await self.session.refresh(org)

        return OrganizationOut.model_validate(org)

    async def deactivate_organization(
        self,
        org_id: int,
        current_user: Account,
    ) -> dict:
        org = await self._get_organization_even_disabled(org_id)
        await self._require_manager_for_org(current_user, org_id)

        if not org.is_enable:
            return {"message": f"Организация {org_id} уже деактивирована"}

        stmt = (
            update(Organization)
            .where(Organization.organization_id == org_id)
            .values(is_enable=False)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Организация {org_id} деактивирована (мягкое удаление)"}

    async def activate_organization(
        self,
        org_id: int,
        current_user: Account,
    ) -> OrganizationOut:
        org = await self._get_organization_even_disabled(org_id)
        await self._require_manager_for_org(current_user, org_id)

        if org.is_enable:
            return OrganizationOut.model_validate(org)

        stmt = (
            update(Organization)
            .where(Organization.organization_id == org_id)
            .values(is_enable=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        await self.session.refresh(org)

        return OrganizationOut.model_validate(org)

    # ─── Доступно связанным пользователям ───────────────────────────────────

    async def get_organization(
        self,
        org_id: int,
        current_user: Account,
    ) -> OrganizationOut:
        org = await self._get_active_organization_or_raise(org_id)
        await self._require_relation_to_org(current_user, org_id)
        return OrganizationOut.model_validate(org)

    async def get_my_organizations(
            self,
            current_user: Account,
    ) -> List[OrganizationOut]:
        sub_stmt = union_all(
            select(Organization.organization_id.label("id")),
            select(Organization.organization_id.label("id")),
            select(Organization.organization_id.label("id")),
        ).subquery()

        stmt = (
            select(Organization)
            .where(Organization.organization_id.in_(select(sub_stmt.c.id).distinct()))
        )

        result = await self.session.execute(stmt)
        orgs = result.scalars().all()

        return [OrganizationOut.model_validate(o) for o in orgs]
