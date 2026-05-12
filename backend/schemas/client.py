from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from schemas.account import AccountCreate


class ClientCreate(BaseModel):
    """Создание клиента из существующего аккаунта"""
    account_id: int = Field(..., gt=0, description="ID существующего аккаунта")


class ClientCreateWithAccount(BaseModel):
    """Создание клиента с новым аккаунтом"""
    account: AccountCreate


class ClientOut(BaseModel):
    """Ответ с данными клиента"""
    client_id: int
    account_id: int
    organization_id: int
    # account: Optional[AccountOut] = None

    class Config:
        from_attributes = True


class BookingInfoOut(BaseModel):
    """Информация о записи (только для чтения)"""
    booking_id: int
    service_name: Optional[str] = None
    master_name: Optional[str] = None
    booking_dt: datetime
    status: Optional[str] = None
    price: Optional[int] = None

    class Config:
        from_attributes = True


class ClientWithBookingsOut(ClientOut):
    """Клиент с его записями (только для чтения)"""
    bookings: List[BookingInfoOut] = []