"""
Скрипт для миграции данных из локальной SQLite базы в Railway PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from sqlalchemy import create_engine
from utils.db import Base, init_db

# Локальная SQLite база
SQLITE_DB = "adapted.db"

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

# Список таблиц для миграции (в порядке зависимостей)
TABLES = [
    'users',
    'documents',
    'tests',
    'test_questions',
    'test_submissions',
    'homeworks',
    'homework_submissions'
]

def create_tables_in_railway():
    """Создает таблицы в Railway PostgreSQL используя init_db()"""
    print("Создание таблиц в Railway PostgreSQL...")
    try:
        # Временно меняем DATABASE_URL для init_db()
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = RAILWAY_DB_URL
        
        # Создаем engine и инициализируем БД
        engine = create_engine(RAILWAY_DB_URL)
        Base.metadata.create_all(engine)
        
        print("Таблицы созданы успешно!")
        
        # Восстанавливаем оригинальный DATABASE_URL
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            del os.environ['DATABASE_URL']
            
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        raise

def migrate_table(sqlite_conn, pg_conn, table_name):
    """Мигрирует данные из SQLite в PostgreSQL"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    try:
        # Проверяем, существует ли таблица в SQLite
        sqlite_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not sqlite_cur.fetchone():
            print(f"Таблица {table_name} не найдена в SQLite, пропускаем")
            return 0
        
        # Получаем данные из SQLite
        sqlite_cur.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cur.fetchall()
        
        if not rows:
            print(f"Таблица {table_name} пустая, пропускаем")
            return 0
        
        # Получаем названия колонок
        columns = [description[0] for description in sqlite_cur.description]
        
        # Вставляем данные в PostgreSQL
        # Используем ON CONFLICT DO NOTHING для избежания дубликатов
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        count = 0
        for row in rows:
            # Конвертируем None в NULL для PostgreSQL
            values = [None if v is None else v for v in row]
            
            query = f"""
                INSERT INTO {table_name} ({columns_str}) 
                VALUES ({placeholders}) 
                ON CONFLICT DO NOTHING
            """
            try:
                pg_cur.execute(query, values)
                count += 1
            except Exception as e:
                print(f"Ошибка при вставке записи в {table_name}: {e}")
                continue
        
        pg_conn.commit()
        print(f"Мигрировано {count} записей из {table_name}")
        return count
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Ошибка при миграции {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    print("=" * 60)
    print("МИГРАЦИЯ ДАННЫХ ИЗ SQLITE В RAILWAY POSTGRESQL")
    print("=" * 60)
    
    # Проверяем наличие SQLite базы
    if not os.path.exists(SQLITE_DB):
        print(f"Ошибка: файл {SQLITE_DB} не найден!")
        print(f"Убедитесь, что вы запускаете скрипт из папки AdaptEd/backend")
        sys.exit(1)
    
    # Подключение к SQLite
    print(f"\nПодключение к SQLite: {SQLITE_DB}")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        print("Подключено к SQLite")
    except Exception as e:
        print(f"Ошибка подключения к SQLite: {e}")
        sys.exit(1)
    
    # Подключение к Railway
    print(f"\nПодключение к Railway PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(RAILWAY_DB_URL)
        print("Подключено к Railway")
    except Exception as e:
        print(f"Ошибка подключения к Railway: {e}")
        sqlite_conn.close()
        sys.exit(1)
    
    # Создаем таблицы в Railway
    print("\n" + "=" * 60)
    print("СОЗДАНИЕ ТАБЛИЦ В RAILWAY")
    print("=" * 60)
    try:
        create_tables_in_railway()
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        sqlite_conn.close()
        pg_conn.close()
        sys.exit(1)
    
    # Проверяем, какие таблицы есть в SQLite
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in sqlite_cur.fetchall()]
    
    print(f"\nНайдено таблиц в SQLite: {len(existing_tables)}")
    print(f"Таблицы: {', '.join(existing_tables)}")
    
    # Миграция данных
    print("\n" + "=" * 60)
    print("НАЧАЛО МИГРАЦИИ ДАННЫХ")
    print("=" * 60)
    
    total_migrated = 0
    for table in TABLES:
        if table in existing_tables:
            count = migrate_table(sqlite_conn, pg_conn, table)
            total_migrated += count
        else:
            print(f"Таблица {table} не найдена в SQLite, пропускаем")
    
    # Закрываем соединения
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print(f"МИГРАЦИЯ ЗАВЕРШЕНА!")
    print(f"Всего мигрировано записей: {total_migrated}")
    print("=" * 60)
    
    print("\nСледующие шаги:")
    print("1. Обновите DATABASE_URL в Railway:")
    print("   Service settings -> Variables -> DATABASE_URL")
    print("2. Установите значение:")
    print(f"   {RAILWAY_DB_URL}")
    print("3. Перезапустите сервис в Railway")

if __name__ == "__main__":
    main()

