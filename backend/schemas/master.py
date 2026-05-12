from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, time

from schemas.account import AccountCreate
from schemas.user import UserOut

class MasterCreateData(BaseModel):
    """Данные для создания мастера"""
    specialization: Optional[str] = None
    grade: Optional[str] = None

class MasterCreate(BaseModel):
    """Создание мастера"""
    account_id: int = Field(..., gt=0, description="ID существующего аккаунта")
    specialization: Optional[str] = None
    grade: Optional[str] = None


class MasterCreateWithAccount(BaseModel):
    """Создание мастера с новым аккаунтом"""
    account: AccountCreate
    master: MasterCreateData


class AssignServiceMaster(BaseModel):
    master_id: int
    service_id: int
    price: int | None = None
    price_grp: int | None = None
    day_start: date | None  = None
    day_finish: date | None = None
    #is_enable: bool | True
    duration: int | None = None

class MasterOut(BaseModel):
    master_id: int
    organization_id: int 
    account_id: int       
    specialization: Optional[str] = None
    grade: Optional[str] = None

    # account: Optional[UserOut] = None
    
    class Config:
        from_attributes = True

class ServiceMasterOut(BaseModel):
    service_master_id: int
    service_id: int 
    master_id: int
    price: Optional[int] = None
    price_grp: Optional[int] = None
    day_start: Optional[date] = None
    day_finish: Optional[date] = None
    is_enable: Optional[bool] = True
    duration: Optional[int] = None
    organization_id: int

    class Config:
        from_attributes = True


class WorkTimeSlot(BaseModel):
    time_from: time
    time_to: time

class MasterWorkDayOut(BaseModel):
    master_id: int
    date: date
    slots: List[WorkTimeSlot]   # список рабочих интервалов на день
    is_working_day: bool = True

class SlotClient(BaseModel):
    id: int
    name: str


class SlotService(BaseModel):
    id: int
    name: Optional[str] = None


class WorkSlotDetailed(BaseModel):
    time_from: time
    time_to: time

    status: str  # free | booked

    client: Optional[SlotClient] = None
    service: Optional[SlotService] = None


class MasterWorkDayDetailedOut(BaseModel):
    master_id: int
    date: date
    slots: List[WorkSlotDetailed]
    is_working_day: bool