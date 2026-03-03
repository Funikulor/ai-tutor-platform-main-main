"""
SQLAlchemy модель для таблицы users в базе данных
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from utils.db import Base
import enum


class UserRoleEnum(str, enum.Enum):
    """Роли пользователей"""
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


class User(Base):  # type: ignore
    """Модель пользователя в базе данных"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False, index=True)  # Уникальный ID пользователя
    email = Column(String(255), unique=True, nullable=False, index=True)  # Email (уникальный)
    password_hash = Column(String(255), nullable=False)  # Хеш пароля
    full_name = Column(String(255), nullable=False)  # Полное имя
    role = Column(SQLEnum(UserRoleEnum), nullable=False, index=True)  # Роль: student, teacher, parent, admin
    class_id = Column(String(50), nullable=True)  # ID класса (для учеников)
    phone = Column(String(20), nullable=True)  # Телефон (опционально)
    parent_fio = Column(String(255), nullable=True)  # ФИО родителя (для учеников)
    parent_phone = Column(String(20), nullable=True)  # Телефон родителя (для учеников)
    avatar_seed = Column(String(64), nullable=True)  # Строка для генерации аватара (DiceBear)
    is_active = Column(Boolean, default=True, nullable=False)  # Активен ли пользователь
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Дата создания
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # Дата обновления
    
    # Связи с другими таблицами (опционально, для будущего расширения)
    # homeworks = relationship("Homework", back_populates="created_by_user")
    # test_submissions = relationship("TestSubmission", back_populates="user")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}', role='{self.role}')>"



















