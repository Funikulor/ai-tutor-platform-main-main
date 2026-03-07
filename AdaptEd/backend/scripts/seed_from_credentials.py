#!/usr/bin/env python3
"""
Заполнение БД пользователями из seed_credentials.txt.
Запуск из корня backend: python -m scripts.seed_from_credentials

Не трогает админа — админ создаётся отдельно (scripts/create_admin.py).
"""
import hashlib
import os
import re
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


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _ensure_user_columns(db):
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


def parse_credentials_file(path: str):
    """Парсит seed_credentials.txt, возвращает список dict."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r"\n(?=Ученик:|Учитель:)", content)
    result = []
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("AdaptEd") or block.startswith("="):
            continue
        role_match = re.match(r"(Ученик|Учитель):\s*(.+)", block)
        if not role_match:
            continue
        role_name, full_name = role_match.group(1), role_match.group(2).strip()
        role = "student" if role_name == "Ученик" else "teacher"
        email = re.search(r"Email:\s*(\S+)", block)
        password = re.search(r"Пароль:\s*(\S+)", block)
        class_line = re.search(r"Класс:\s*(.+)", block)
        parent_line = re.search(r"Родитель:\s*(.+)", block)
        if not email or not password:
            continue
        email = email.group(1).strip()
        password = password.group(1).strip()
        class_id = class_line.group(1).strip() if class_line else None
        if class_id == "-":
            class_id = None
        parent_fio, parent_phone = None, None
        if parent_line and parent_line.group(1).strip() != "-":
            parts = parent_line.group(1).strip().split(",", 1)
            parent_fio = parts[0].strip() if parts else None
            parent_phone = parts[1].strip() if len(parts) > 1 else None
        user_id = email.split("@")[0]  # student101, teacher51
        result.append({
            "user_id": user_id,
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
            "class_id": class_id,
            "parent_fio": parent_fio,
            "parent_phone": parent_phone,
        })
    return result


def main():
    if not has_db():
        print("Ошибка: DATABASE_URL не задан или БД недоступна. Проверьте .env")
        sys.exit(1)
    init_db()
    cred_path = os.path.join(backend_dir, "seed_credentials.txt")
    entries = parse_credentials_file(cred_path)
    if not entries:
        print(f"В файле {cred_path} не найдено записей Ученик/Учитель.")
        sys.exit(1)
    db = get_db()
    if not db:
        print("Ошибка: не удалось подключиться к БД")
        sys.exit(1)
    try:
        _ensure_user_columns(db)
    except Exception as e:
        print(f"Предупреждение при миграции колонок: {e}")
        db.rollback()
    created, updated = 0, 0
    for e in entries:
        try:
            existing = db.query(User).filter(
                (User.user_id == e["user_id"]) | (User.email == e["email"])
            ).first()
            hashed = hash_password(e["password"])
            if existing:
                existing.password_hash = hashed
                existing.full_name = e["full_name"]
                existing.role = UserRoleEnum.STUDENT if e["role"] == "student" else UserRoleEnum.TEACHER
                existing.class_id = e["class_id"]
                existing.parent_fio = e.get("parent_fio")
                existing.parent_phone = e.get("parent_phone")
                existing.is_active = True
                db.commit()
                updated += 1
                print(f"  Обновлён: {e['email']}")
            else:
                user = User(
                    user_id=e["user_id"],
                    email=e["email"],
                    password_hash=hashed,
                    full_name=e["full_name"],
                    role=UserRoleEnum.STUDENT if e["role"] == "student" else UserRoleEnum.TEACHER,
                    class_id=e["class_id"],
                    parent_fio=e.get("parent_fio"),
                    parent_phone=e.get("parent_phone"),
                    is_active=True,
                )
                db.add(user)
                db.commit()
                created += 1
                print(f"  Создан: {e['email']}")
        except Exception as err:
            print(f"  Ошибка для {e['email']}: {err}")
            db.rollback()
    db.close()
    print(f"\nГотово. Создано: {created}, обновлено: {updated}.")


if __name__ == "__main__":
    print("Заполнение БД из seed_credentials.txt...\n")
    main()
