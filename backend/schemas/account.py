from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class AccountBase(BaseModel):
    """Базовые поля аккаунта"""
    first_name: Optional[str] = Field(None, max_length=120)
    last_name: Optional[str] = Field(None, max_length=120)
    middle_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=25)
    login: str = Field(..., min_length=3, max_length=64)
    comments: Optional[str] = None


class AccountCreate(BaseModel):
    """Создание аккаунта (регистрация)"""
    first_name: Optional[str] = Field(None, max_length=120)
    last_name: Optional[str] = Field(None, max_length=120)
    middle_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=25)
    login: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    comments: Optional[str] = None

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Логин может содержать только буквы, цифры и знак подчеркивания")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v


class AccountUpdate(BaseModel):
    """Обновление данных аккаунта"""
    first_name: Optional[str] = Field(None, max_length=120)
    last_name: Optional[str] = Field(None, max_length=120)
    middle_name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=25)
    comments: Optional[str] = None


class AccountPasswordChange(BaseModel):
    """Смена пароля"""
    old_password: str
    new_password: str = Field(..., min_length=6)


class AccountOut(BaseModel):
    """Ответ с данными аккаунта (без пароля)"""
    account_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    phone: Optional[str]
    login: str
    is_enable: bool
    comments: Optional[str]

    class Config:
        from_attributes = True


class AccountWithRelationsOut(AccountOut):
    """Аккаунт с ролями в организациях"""
    manager_orgs: list[int] = []
    master_orgs: list[int] = []
    client_orgs: list[int] = []