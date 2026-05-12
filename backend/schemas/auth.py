from typing import List, Optional

from pydantic import BaseModel

from schemas.base import CamelModel


class UserLogin(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    login: str

class UserRoleResponse(BaseModel):
    account_id: int
    login: str
    role: str                          # основная роль: "account" | "client" | "master" | "manager"
    additional_roles: Optional[List[str]] = None  # если у пользователя несколько ролей
