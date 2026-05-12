from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SlotGenerateRequest(BaseModel):
    """Запрос на генерацию слотов для мастера"""
    master_id: int = Field(..., description="ID мастера", gt=0)
    start_date: date = Field(..., description="Дата начала")
    end_date: Optional[date] = Field(None, description="Дата окончания (если не указана, то только start_date)")


class SlotGenerateResponse(BaseModel):
    """Ответ после генерации слотов"""
    master_id: int
    organization_id: int
    start_date: date
    end_date: date
    slots_created: int
    message: str


class SlotResponse(BaseModel):
    """Модель слота для ответа"""
    booking_id: int
    master_id: int
    booking_dt: datetime
    status: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SlotFreeRequest(BaseModel):
    start_date: date
    end_date: Optional[date] = None


class SlotInterval(BaseModel):
    from_: datetime
    to: datetime

    class Config:
        populate_by_name = True


class SlotFreeResponse(BaseModel):
    """Ответ со списком свободных слотов"""
    master_id: int
    organization_id: Optional[int]
    start_date: date
    end_date: Optional[date]
    slots: List[SlotResponse]
    total: int


class GenerateSlotsForAllRequest(BaseModel):
    """Запрос на генерацию слотов для всех мастеров организации"""
    start_date: date = Field(..., description="Дата начала")
    end_date: Optional[date] = Field(None,
                                     description="Дата окончания (если не указана, то только start_date)")


class GenerateSlotsForAllResponse(BaseModel):
    """Ответ после генерации слотов для всех мастеров"""
    organization_id: int
    start_date: date
    end_date: date
    total_masters: int
    slots_created: int
    errors: Optional[List[str]] = None
    message: str


class MasterSlotError(BaseModel):
    """Ошибка при генерации слотов для конкретного мастера"""
    master_id: int
    error: str

class GenerateSlotsForMastersRequest(BaseModel):
    """Запрос на генерацию слотов для нескольких мастеров"""
    master_ids: List[int] = Field(..., description="Список ID мастеров")
    start_date: date = Field(..., description="Дата начала")
    end_date: Optional[date] = Field(None, description="Дата окончания")


class BookingCreateRequest(BaseModel):
    """Запрос на создание бронирования"""
    service_master_id: int
    client_id: int
    booking_dt: datetime
    duration_minutes: int


class BookedSlotInfo(BaseModel):
    booking_id: int
    booking_dt: datetime


class BookingResponse(BaseModel):
    booking_id: int
    client_id: int
    service_master_id: int
    master_id: int
    booking_dt: datetime
    duration_minutes: int
    status: str
    organization_id: int
    booked_slots: List[BookedSlotInfo] = []

    class Config:
        from_attributes = True


class BookedSlotInterval(BaseModel):
    """Интервал забронированных слотов"""
    from_: datetime = Field(..., alias="from")
    to: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookedSlotsIntervalsResponse(BaseModel):
    """Ответ с интервалами забронированных слотов"""
    master_id: int
    organization_id: Optional[int]
    start_date: date
    end_date: date
    intervals: List[BookedSlotInterval]
    total_intervals: int
    total_minutes: int = Field(..., description="Общая длительность всех забронированных интервалов в минутах")

class BookingCancelRequest(BaseModel):
    client_id: int
    booking_dt: datetime


class BookingCancelResponse(BaseModel):
    master_id: int
    client_id: int
    booking_dt: datetime
    released_slots: int
    status: str