#!/usr/bin/env python3
"""
Скрипт создания администратора в базе данных.
Запуск из корня backend: python -m scripts.create_admin

Берёт ADMIN_EMAIL и ADMIN_PASSWORD из .env (или переменных окружения).
Если не заданы — создаёт админа admin@adapted.local / Admin123!
"""
import hashlib
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        pass

from sqlalchemy import text
from utils.db import init_db, has_db, get_db
from models.user_db import User, UserRoleEnum

ADMIN_ID = "admin_001"


def _ensure_user_columns(db):
    """Добавляет колонки в users, если их нет (миграция для Railway/Postgres)."""
    for col, typ in [
        ("parent_fio", "VARCHAR(255)"),
        ("parent_phone", "VARCHAR(20)"),
        ("avatar_seed", "VARCHAR(64)"),
    ]:
        try:
            db.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}"))
            db.commit()
        except Exception:
            db.rollback()


def hash_password(password: str) -> str:
    """Тот же алгоритм, что и в auth_service."""
    return hashlib.sha256(password.encode()).hexdigest()


def main():
    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip() or "admin@adapted.local"
    admin_password = (os.getenv("ADMIN_PASSWORD") or "").strip() or "Admin123!"
    full_name = (os.getenv("ADMIN_FULL_NAME") or "").strip() or "Администратор"

    if not has_db():
        print("Ошибка: DATABASE_URL не задан или БД недоступна. Проверьте .env")
        sys.exit(1)

    init_db()
    hashed = hash_password(admin_password)

    db = get_db()
    if not db:
        print("Ошибка: не удалось подключиться к БД")
        sys.exit(1)

    try:
        _ensure_user_columns(db)
    except Exception as e:
        print(f"Предупреждение при миграции колонок: {e}")
        db.rollback()

    try:
        existing = db.query(User).filter(
            (User.user_id == ADMIN_ID) | (User.email == admin_email)
        ).first()

        if existing:
            existing.password_hash = hashed
            existing.email = admin_email
            existing.full_name = full_name
            existing.role = UserRoleEnum.ADMIN
            existing.is_active = True
            db.commit()
            print(f"[OK] Администратор обновлён в БД: {admin_email}")
        else:
            admin = User(
                user_id=ADMIN_ID,
                email=admin_email,
                password_hash=hashed,
                full_name=full_name,
                role=UserRoleEnum.ADMIN,
                class_id=None,
                phone=None,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"[OK] Администратор создан в БД: {admin_email}")

        print("")
        print("Вход в панель админа:")
        print(f"  Email:    {admin_email}")
        print(f"  Пароль:   {admin_password}")
        print("")
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
