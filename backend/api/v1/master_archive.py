from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from db.session import get_db_session
from services.master_archive.service import MasterArchiveService
from schemas.master_archive import (
    MasterArchiveUpsertRequest,
    MasterArchiveResponse
)

router = APIRouter(prefix="/master-archive", tags=["Master Archive"])

@router.post("/masters/{master_id}")
async def upsert_master_archive(
    master_id: int,
    request: MasterArchiveUpsertRequest,
    session: AsyncSession = Depends(get_db_session)
):
    service = MasterArchiveService(session)

    try:
        await service.upsert(
            master_id=master_id,
            work_day=request.work_day,
            organization_id=request.organization_id,
            released_hours=request.released_hours,
            released_amount=request.released_amount,
            cheats_hours=request.cheats_hours,
            booking_count=request.booking_count,
        )

        return {"status": "ok"}

    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/masters/{master_id}", response_model=List[MasterArchiveResponse])
async def get_master_archive(
    master_id: int,
    start_date: date,
    end_date: date | None = None,
    organization_id: int | None = None,
    session: AsyncSession = Depends(get_db_session)
):
    service = MasterArchiveService(session)

    try:
        result = await service.get(
            master_id=master_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )

        return [
            MasterArchiveResponse(
                master_id=r.master_id,
                work_day=r.work_day,
                organization_id=r.organization_id,
                released_hours=float(r.released_hours or 0),
                released_amount=float(r.released_amount or 0),
                cheats_hours=float(r.cheats_hours or 0),
                booking_count=r.booking_count or 0
            )
            for r in result
        ]

    except Exception as e:
        raise HTTPException(500, str(e))