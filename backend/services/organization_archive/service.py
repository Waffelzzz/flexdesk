from sqlalchemy import select, exists, update, delete, union_all, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import union
from typing import Optional, List
from sqlalchemy.orm import selectinload

from db.models import OrganizationArchive, Account
from schemas.organization_archive import OrganizationArchiveIn, OrganizationArchiveSelectOut, OrganizationArchiveDate, OrganizationArchiveUpdate
from services.master.exceptions import NoRelationToOrganizationError, NotManagerOfOrganizationError, ServiceMasterNotFoundError

class OrganizationArchiveService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def organization_archive_insert(
        self,
        data: OrganizationArchiveIn,
        org_id: int,
        current_user: Account,
     ) -> dict:

        stmt = (
            select(OrganizationArchive)
            .where(
                OrganizationArchive.organization_id == org_id, 
                OrganizationArchive.work_period == data.work_period
            )
        )

        result = await self.session.execute(stmt)
        existing_archive = result.scalar_one_or_none()
        
        if existing_archive:
            return {
                "message": f"Запись за период {data.work_period} уже существует",
                "status": "already_exists",
                "organization_archive_id": existing_archive.organization_archive_id
            }
        
        serviceOrgArchive = OrganizationArchive(
            revenue =data.revenue,
            booking_count = data.booking_count,
            organization_id = org_id,
            work_period = data.work_period
        )

        self.session.add(serviceOrgArchive)
        await self.session.commit()
        await self.session.refresh(serviceOrgArchive)

        return {"message": f"Услуга добавлена в архив организации"}
    
    async def organization_archive_delete(
        self,
        id: int,
        current_user: Account,
     ) -> dict:
        
        stmt = (
            delete(OrganizationArchive)
            .where(OrganizationArchive.organization_archive_id == id)
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Услуга удалена из архива организации"}
    
    async def organization_archive_update(
        self,
        id: int,
        data: OrganizationArchiveUpdate,
        current_user: Account,
     ) -> dict:
        
        check_stmt = select(OrganizationArchive).where(OrganizationArchive.organization_archive_id == id)
        result = await self.session.execute(check_stmt)
        existing_archive = result.scalar_one_or_none()
        
        if not existing_archive:
            return {"message": f"Запись с id {id} не найдена", "status": "not_found"}
        stmt = (
            update(OrganizationArchive)
            .where(OrganizationArchive.organization_archive_id == id)
            .values(
                revenue=OrganizationArchive.revenue + data.revenue if data.revenue is not None else OrganizationArchive.revenue,
                booking_count=OrganizationArchive.booking_count + data.booking_count if data.booking_count is not None else OrganizationArchive.booking_count,
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Архив организации изменен"}
    
    async def organization_archive_select(
        self,
        id: int,
        data: OrganizationArchiveDate,
        current_user: Account,
     ) -> OrganizationArchiveSelectOut:
        
        stmt = (
            select(OrganizationArchive)
            .where(
                OrganizationArchive.organization_archive_id == id,
                OrganizationArchive.work_period == data.work_period)
        )

        result = await self.session.execute(stmt)
        organization_archive = result.unique().scalar_one_or_none()

        return OrganizationArchiveSelectOut.model_validate(organization_archive)