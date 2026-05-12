from pydantic import BaseModel
from datetime import date
from typing import Optional


class MasterArchiveUpsertRequest(BaseModel):
    work_day: date
    organization_id: int
    released_hours: Optional[float] = 0
    released_amount: Optional[float] = 0
    cheats_hours: Optional[float] = 0
    booking_count: Optional[int] = 0


class MasterArchiveResponse(BaseModel):
    master_id: int
    work_day: date
    organization_id: int
    released_hours: float
    released_amount: float
    cheats_hours: float
    booking_count: int