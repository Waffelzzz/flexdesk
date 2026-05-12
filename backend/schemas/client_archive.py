from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.user import UserOut

class ClientArchiveInsert(BaseModel):
    service_master_id: int
    visit_start_dt: datetime | None = None
    visit_end_dt: datetime | None = None
    organization_id: int

class ClientArchiveUpdate(BaseModel):
    client_id: int
    service_master_id: int
    visit_start_dt: datetime | None = None
    visit_end_dt: datetime | None = None
    organization_id: int

class ClientArchiveSelectOut(BaseModel):
    client_archive_id: int
    client_id: int
    service_master_id: int
    visit_start_dt: datetime | None = None
    visit_end_dt: datetime | None = None
    organization_id: int

    class Config:
        from_attributes = True
