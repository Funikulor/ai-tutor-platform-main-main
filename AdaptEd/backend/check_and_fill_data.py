"""
Скрипт для проверки данных в SQLite и заполнения Railway PostgreSQL
"""
import sqlite3
import psycopg2
import os
import sys

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

# Локальная SQLite база
SQLITE_DB = "adapted.db"

def check_sqlite_data():
    """Проверяет данные в SQLite"""
    print("=" * 60)
    print("ПРОВЕРКА ДАННЫХ В SQLITE")
    print("=" * 60)
    
    if not os.path.exists(SQLITE_DB):
        print(f"Файл {SQLITE_DB} не найден!")
        return False
    
    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    
    # Получаем список таблиц
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    
    print(f"\nНайдено таблиц: {len(tables)}")
    
    total_rows = 0
    for table in tables:
        if table == 'sqlite_sequence':
            continue
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count} записей")
        total_rows += count
    
    conn.close()
    
    print(f"\nВсего записей: {total_rows}")
    return total_rows > 0

def create_sample_data_in_railway():
    """Создает тестовые данные в Railway PostgreSQL"""
    print("\n" + "=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ В RAILWAY")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(RAILWAY_DB_URL)
        cur = conn.cursor()
        
        # Проверяем, есть ли уже пользователи
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        
        if user_count > 0:
            print(f"В базе уже есть {user_count} пользователей")
            conn.close()
            return
        
        # Создаем тестового пользователя
        print("Создание тестового пользователя...")
        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, role, created_at)
            VALUES ('admin@example.com', 'hashed_password_here', 'Admin User', 'admin', NOW())
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """)
        
        result = cur.fetchone()
        if result:
            user_id = result[0]
            print(f"Создан пользователь с ID: {user_id}")
        else:
            # Получаем существующего пользователя
            cur.execute("SELECT id FROM users LIMIT 1")
            result = cur.fetchone()
            if result:
                user_id = result[0]
                print(f"Используем существующего пользователя с ID: {user_id}")
            else:
                print("Не удалось создать или найти пользователя")
                conn.close()
                return
        
        conn.commit()
        print("Тестовые данные созданы успешно!")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при создании данных: {e}")
        import traceback
        traceback.print_exc()

def migrate_all_data():
    """Мигрирует все данные из SQLite в Railway"""
    print("\n" + "=" * 60)
    print("МИГРАЦИЯ ВСЕХ ДАННЫХ")
    print("=" * 60)
    
    # Запускаем скрипт миграции
    try:
        import migrate_to_railway
        migrate_to_railway.main()
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 60)
    print("ПРОВЕРКА И ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ RAILWAY")
    print("=" * 60)
    
    # Проверяем данные в SQLite
    has_data = check_sqlite_data()
    
    if has_data:
        print("\nНайдены данные в SQLite. Запускаем миграцию...")
        migrate_all_data()
    else:
        print("\nВ SQLite нет данных. Создаем тестовые данные в Railway...")
        create_sample_data_in_railway()
    
    print("\n" + "=" * 60)
    print("ГОТОВО!")
    print("=" * 60)

if __name__ == "__main__":
    # Проверяем, что скрипт запущен из правильной директории
    if not os.path.exists(SQLITE_DB):
        print(f"Ошибка: файл {SQLITE_DB} не найден")
        print("Запустите скрипт из папки AdaptEd/backend")
        sys.exit(1)
    
    main()

