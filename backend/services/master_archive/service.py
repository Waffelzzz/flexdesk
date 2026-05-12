from datetime import date
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import MasterArchive


class MasterArchiveService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        master_id: int,
        work_day: date,
        organization_id: int,
        released_hours: float = 0,
        released_amount: float = 0,
        cheats_hours: float = 0,
        booking_count: int = 0
    ):
        released_hours = round(float(released_hours), 6)
        released_amount = round(float(released_amount), 2)
        cheats_hours = round(float(cheats_hours), 6)

        stmt = insert(MasterArchive).values(
            master_id=master_id,
            work_day=work_day,
            organization_id=organization_id,
            released_hours=released_hours,
            released_amount=released_amount,
            cheats_hours=cheats_hours,
            booking_count=booking_count
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["master_id", "work_day", "organization_id"],
            set_={
                "released_hours": MasterArchive.released_hours + released_hours,
                "released_amount": MasterArchive.released_amount + released_amount,
                "cheats_hours": MasterArchive.cheats_hours + cheats_hours,
                "booking_count": MasterArchive.booking_count + booking_count,
            }
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def get(
        self,
        master_id: int,
        start_date: date,
        end_date: Optional[date] = None,
        organization_id: Optional[int] = None
    ) -> List[MasterArchive]:

        end_date = end_date or start_date

        query = select(MasterArchive).where(
            and_(
                MasterArchive.master_id == master_id,
                MasterArchive.work_day >= start_date,
                MasterArchive.work_day <= end_date
            )
        )

        if organization_id:
            query = query.where(MasterArchive.organization_id == organization_id)

        query = query.order_by(MasterArchive.work_day)

        result = await self.session.execute(query)
        return result.scalars().all()