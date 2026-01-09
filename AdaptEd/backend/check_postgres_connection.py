"""
Скрипт для проверки подключения к PostgreSQL на Railway
"""
import os
from dotenv import load_dotenv

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL не найден в .env файле")
    exit(1)

print("[INFO] Подключение к базе данных...")
db_host = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'скрыт'
print(f"   URL: {db_host}")

try:
    from sqlalchemy import create_engine, text
    
    # Создаем подключение
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Проверяем подключение
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("[SUCCESS] Подключение успешно!")
        print(f"   PostgreSQL версия: {version.split(',')[0]}")
        
        # Проверяем текущую базу данных
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.fetchone()[0]
        print(f"   Текущая БД: {db_name}")
        
        # Проверяем существующие таблицы
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"   Найдено таблиц: {len(tables)}")
            print(f"   Таблицы: {', '.join(tables)}")
            
            # Проверяем наличие таблицы users
            if 'users' in tables:
                # Показываем количество пользователей
                result = conn.execute(text("SELECT COUNT(*) FROM users;"))
                user_count = result.fetchone()[0]
                print(f"\n   [INFO] Таблица users: {user_count} пользователей")
                
                # Показываем распределение по ролям
                result = conn.execute(text("""
                    SELECT role, COUNT(*) as count 
                    FROM users 
                    GROUP BY role 
                    ORDER BY count DESC;
                """))
                roles = result.fetchall()
                if roles:
                    print(f"   Распределение по ролям:")
                    for role, count in roles:
                        print(f"     - {role}: {count}")
            else:
                print(f"   [WARNING] Таблица users не найдена!")
        else:
            print(f"   [WARNING] Таблиц не найдено. Запустите приложение для создания схемы.")
    
    print("\n[SUCCESS] База данных готова к использованию!")
    
except ImportError as e:
    print(f"[ERROR] Ошибка импорта: {e}")
    print("   Установите зависимости: pip install -r requirements.txt")
except Exception as e:
    print(f"[ERROR] Ошибка подключения: {e}")
    print("\nВозможные причины:")
    print("1. Неверный DATABASE_URL в .env")
    print("2. База данных недоступна (проверьте Railway)")
    print("3. Не установлен psycopg2-binary: pip install psycopg2-binary")
    exit(1)

