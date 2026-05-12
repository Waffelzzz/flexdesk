from pydantic import BaseModel, Field, validator
from typing import Optional, List

from schemas.base import CamelModel


class UserCreate(BaseModel):
    """
    Схема для регистрации нового пользователя (аккаунта).
    Обязательные поля: login, password.
    Остальные — желательны, но могут быть опциональными.
    """
    login: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Логин пользователя (уникальный)",
        examples=["dmitriy91", "master_alex"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль (будет захэширован)",
        examples=["StrongPass123!"]
    )

    first_name: Optional[str] = Field(
        None,
        max_length=120,
        description="Имя",
        examples=["Дмитрий"]
    )
    last_name: Optional[str] = Field(
        None,
        max_length=120,
        description="Фамилия",
        examples=["Иванов"]
    )
    middle_name: Optional[str] = Field(
        None,
        max_length=120,
        description="Отчество",
        examples=["Сергеевич"]
    )
    phone: Optional[str] = Field(
        None,
        max_length=25,
        description="Номер телефона",
        examples=["+79781234567", "79781234567"]
    )
    comments: Optional[str] = Field(
        None,
        description="Комментарии / заметки об аккаунте"
    )

    @validator("phone", pre=True, always=True)
    def normalize_phone(cls, v):
        if v:
            cleaned = ''.join(c for c in str(v) if c.isdigit() or c == '+')
            if cleaned.startswith('8'):
                cleaned = '+7' + cleaned[1:]
            return cleaned
        return v


class UserUpdate(BaseModel):
    """
    Схема для обновления профиля (PATCH /me или /users/{id}).
    Все поля опциональные.
    """
    first_name: Optional[str] = Field(None, max_length=120)
    last_name: Optional[str] = Field(None, max_length=120)
    middle_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=25)
    comments: Optional[str] = Field(None)

    class Config:
        extra = "forbid"


class UserOut(BaseModel):
    """
    Схема для вывода информации о пользователе.
    Обычно используется в ответах API.
    """
    account_id: int
    login: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    is_enable: bool
    comments: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


