"""
Скрипт для явного создания таблиц в базе данных
"""
import os
from dotenv import load_dotenv

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

print("[INFO] Загрузка .env...")
print(f"[INFO] DATABASE_URL: {'установлен' if os.getenv('DATABASE_URL') else 'не установлен'}")

# Инициализируем БД
from utils.db import init_db

print("[INFO] Инициализация базы данных...")
init_db()
print("[INFO] Готово!")












