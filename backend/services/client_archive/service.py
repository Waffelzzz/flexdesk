from sqlalchemy import select, exists, update, delete, union_all, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import union
from typing import Optional, List
from sqlalchemy.orm import selectinload

from db.models import ClientArchive, Account, Client
from schemas.client_archive import ClientArchiveInsert, ClientArchiveSelectOut,ClientArchiveUpdate
from services.master.exceptions import NoRelationToOrganizationError, NotManagerOfOrganizationError, ServiceMasterNotFoundError

class ClientArchiveService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def client_archive_insert(
        self,
        data: ClientArchiveInsert,
        client_id: int,
        current_user: Account,
     ) -> dict:
        
        serviceClientArchive = ClientArchive(
            client_id = client_id,
            service_master_id = data.service_master_id,
            visit_start_dt = data.visit_start_dt,
            visit_end_dt = data.visit_end_dt,
            organization_id = data.organization_id
        )

        self.session.add(serviceClientArchive)
        await self.session.commit()
        await self.session.refresh(serviceClientArchive)

        return {"message": f"Услуга добавлена в архив клиента"}
    
    async def client_archive_delete(
        self,
        id: int,
        current_user: Account,
     ) -> dict:
        
        stmt = (
            delete(ClientArchive)
            .where(ClientArchive.client_archive_id == id)
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Услуга удалена из архива клиента"}
    
    async def client_archive_update(
        self,
        id: int,
        data: ClientArchiveUpdate,
        current_user: Account,
     ) -> dict:
        
        stmt = (
            update(ClientArchive)
            .where(ClientArchive.client_archive_id == id)
            .values(
                client_id = data.client_id,
                service_master_id = data.service_master_id,
                visit_start_dt = data.visit_start_dt,
                visit_end_dt = data.visit_end_dt,
                organization_id = data.organization_id
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        return {"message": f"Архив клиента изменен"}
    
    async def client_archive_select(
        self,
        id: int,
        current_user: Account,
     ) -> ClientArchiveSelectOut:
        
        stmt = (
            select(ClientArchive)
            .where(ClientArchive.client_archive_id == id)
        )

        result = await self.session.execute(stmt)
        client_archive = result.unique().scalar_one_or_none()

        return ClientArchiveSelectOut.model_validate(client_archive)