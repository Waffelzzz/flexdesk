from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import time
from pydantic import BaseModel, field_validator

from schemas.base import CamelModel


class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None
    contact_info: str | None = None
    address: str | None = None
    time_gap: int | None = Field(None, ge=0, description="интервал в минутах")
    granular_step: int | None = Field(None, ge=1, description="шаг в минутах")


class OrganizationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    contact_info: str | None = None
    address: str | None = None
    time_gap: int | None = Field(None, ge=0)
    granular_step: int | None = Field(None, ge=1)

class OrganizationOut(CamelModel):
    organization_id: int
    name: str
    description: Optional[str] = None
    contact_info: Optional[str] = None
    address: Optional[str] = None
    time_gap: Optional[int] = None
    granular_step: Optional[int] = None

    class Config:
        from_attributes = True