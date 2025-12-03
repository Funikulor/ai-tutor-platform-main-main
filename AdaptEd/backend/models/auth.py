"""
Модели для авторизации и регистрации
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """Роли пользователей"""
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


class UserRegistration(BaseModel):
    """Модель регистрации пользователя"""
    email: str
    password: str
    full_name: str
    role: UserRole
    class_id: Optional[str] = None  # Для учеников
    phone: Optional[str] = None


class UserLogin(BaseModel):
    """Модель входа пользователя"""
    email: str
    password: str


class User(BaseModel):
    """Модель пользователя"""
    user_id: str
    email: str
    full_name: str
    role: UserRole
    class_id: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    
    class Config:
        use_enum_values = True


class Token(BaseModel):
    """Токен доступа"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str

