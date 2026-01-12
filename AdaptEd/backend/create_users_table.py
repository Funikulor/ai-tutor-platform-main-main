"""
Скрипт для создания таблицы users в базе данных
"""
import os
from dotenv import load_dotenv

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

print("[INFO] Создание таблицы users...")

try:
    from utils.db import Base, _ensure_engine, SQLA_AVAILABLE
    from sqlalchemy import inspect
    
    _ensure_engine()
    
    if not SQLA_AVAILABLE:
        print("[ERROR] SQLAlchemy недоступен")
        exit(1)
    
    from utils.db import _engine
    if _engine is None:
        print("[ERROR] Подключение к базе данных не установлено")
        exit(1)
    
    # Импортируем модель User
    from models.user_db import User
    
    # Проверяем, существует ли таблица
    inspector = inspect(_engine)
    existing_tables = inspector.get_table_names()
    
    if 'users' in existing_tables:
        print("[INFO] Таблица users уже существует")
    else:
        print("[INFO] Создание таблицы users...")
        Base.metadata.create_all(bind=_engine, tables=[User.__table__])
        print("[SUCCESS] Таблица users создана успешно!")
    
    # Показываем структуру таблицы
    if 'users' in existing_tables or 'users' in inspector.get_table_names():
        print("\n[INFO] Структура таблицы users:")
        columns = inspector.get_columns('users')
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    
except Exception as e:
    print(f"[ERROR] Ошибка: {e}")
    import traceback
    traceback.print_exc()
    exit(1)




