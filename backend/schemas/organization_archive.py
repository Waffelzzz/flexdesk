from pydantic import BaseModel
from typing import Optional
from datetime import date
from pydantic import Field

class OrganizationArchiveIn(BaseModel):
    revenue: float | None = 0
    booking_count: int | None = 0
    work_period:date | None = Field(default_factory=date.today)

class OrganizationArchiveUpdate(BaseModel):
    revenue: float | None = None
    booking_count: int | None = None
    organization_id: int
    work_period:date | None = Field(default_factory=date.today)

class OrganizationArchiveDate(BaseModel):
    work_period:date | None = Field(default_factory=date.today)

class OrganizationArchiveSelectOut(BaseModel):
    organization_archive_id: int
    revenue: float | None = None
    booking_count: int | None = None
    organization_id: int
    work_period:date | None = None

    class Config:
        from_attributes = True
