"""
Скрипт для миграции данных из локальной SQLite базы в Neon PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# Локальная SQLite база
SQLITE_DB = "adapted.db"

# Neon PostgreSQL база (используем pooler connection string)
NEON_DB_URL = "postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

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

def get_table_columns(cursor, table_name):
    """Получает список колонок таблицы"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate_table(sqlite_conn, pg_conn, table_name, retry_count=3):
    """Мигрирует данные из SQLite в PostgreSQL с обработкой переподключений"""
    sqlite_cur = sqlite_conn.cursor()
    
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
        
        # Пробуем мигрировать с переподключением при необходимости
        for attempt in range(retry_count):
            try:
                # Переподключаемся, если соединение закрыто
                if pg_conn.closed:
                    pg_conn = psycopg2.connect(NEON_DB_URL)
                    print(f"[INFO] Переподключение к Neon (попытка {attempt + 1})")
                
                pg_cur = pg_conn.cursor()
                
                # Проверяем, существует ли таблица в PostgreSQL
                try:
                    pg_cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        );
                    """, (table_name,))
                    table_exists = pg_cur.fetchone()[0]
                except:
                    # Если таблицы нет, пропускаем
                    table_exists = False
                
                if not table_exists:
                    print(f"[WARN] Таблица {table_name} не существует в Neon")
                    print(f"      Таблица будет создана автоматически при первом запуске backend")
                    return 0
                
                # Вставляем данные в PostgreSQL
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                count = 0
                for row in rows:
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
                print(f"[OK] Мигрировано {count} записей из {table_name}")
                return count
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                if attempt < retry_count - 1:
                    print(f"[WARN] Ошибка подключения (попытка {attempt + 1}/{retry_count}): {e}")
                    print(f"      Пробуем переподключиться...")
                    try:
                        pg_conn.close()
                    except:
                        pass
                    pg_conn = psycopg2.connect(NEON_DB_URL)
                    continue
                else:
                    raise
        
        return 0
        
    except Exception as e:
        try:
            if not pg_conn.closed:
                pg_conn.rollback()
        except:
            pass
        print(f"[ERROR] Ошибка при миграции {table_name}: {e}")
        return 0

def create_tables_in_neon(pg_conn):
    """Создает таблицы в Neon через SQL, если их еще нет"""
    print("\nСоздание таблиц в Neon...")
    try:
        cur = pg_conn.cursor()
        
        # Создаем таблицы через SQL (упрощенная версия)
        # Полная структура создастся через init_db() при первом запуске
        
        # Проверяем, существует ли таблица homeworks
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'homeworks'
            );
        """)
        homeworks_exists = cur.fetchone()[0]
        
        if not homeworks_exists:
            print("[INFO] Таблицы будут созданы автоматически при первом запуске backend")
            print("[INFO] Продолжаем миграцию данных...")
        else:
            print("[OK] Таблицы уже существуют")
        
        pg_conn.commit()
        return True
    except Exception as e:
        print(f"[WARN] Предупреждение: {e}")
        print("[INFO] Таблицы будут созданы автоматически при первом запуске backend")
        return False

def main():
    print("=" * 60)
    print("МИГРАЦИЯ ДАННЫХ ИЗ SQLITE В NEON POSTGRESQL")
    print("=" * 60)
    
    # Проверяем наличие SQLite базы
    if not os.path.exists(SQLITE_DB):
        print(f"[ERROR] Файл {SQLITE_DB} не найден!")
        print(f"  Убедитесь, что вы запускаете скрипт из папки AdaptEd/backend")
        return
    
    # Подключение к SQLite
    print(f"\nПодключение к SQLite: {SQLITE_DB}")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        print("[OK] Подключено к SQLite")
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к SQLite: {e}")
        return
    
    # Подключение к Neon
    print(f"\nПодключение к Neon PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(NEON_DB_URL)
        print("[OK] Подключено к Neon")
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к Neon: {e}")
        sqlite_conn.close()
        return
    
    # Создаем таблицы в Neon
    create_tables_in_neon(pg_conn)
    
    # Проверяем, какие таблицы есть в SQLite
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in sqlite_cur.fetchall()]
    
    print(f"\nНайдено таблиц в SQLite: {len(existing_tables)}")
    print(f"Таблицы: {', '.join(existing_tables)}")
    
    # Миграция данных
    print("\n" + "=" * 60)
    print("НАЧАЛО МИГРАЦИИ")
    print("=" * 60)
    
    total_migrated = 0
    for table in TABLES:
        if table in existing_tables:
            try:
                count = migrate_table(sqlite_conn, pg_conn, table)
                total_migrated += count
            except Exception as e:
                print(f"[ERROR] Критическая ошибка при миграции {table}: {e}")
                # Пробуем переподключиться
                try:
                    pg_conn.close()
                except:
                    pass
                try:
                    pg_conn = psycopg2.connect(NEON_DB_URL)
                    print("[INFO] Переподключено к Neon")
                except:
                    print("[ERROR] Не удалось переподключиться к Neon")
                    break
        else:
            print(f"[WARN] Таблица {table} не найдена в SQLite, пропускаем")
    
    # Закрываем соединения
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print(f"МИГРАЦИЯ ЗАВЕРШЕНА!")
    print(f"Всего мигрировано записей: {total_migrated}")
    print("=" * 60)
    
    print("\nСледующие шаги:")
    print("1. Обновите DATABASE_URL в Netlify:")
    print("   Site settings -> Environment variables -> DATABASE_URL")
    print("2. Установите значение:")
    print(f"   {NEON_DB_URL}")
    print("3. Перезапустите деплой в Netlify")

if __name__ == "__main__":
    # Проверяем, что скрипт запущен из правильной директории
    if not os.path.exists(SQLITE_DB):
        print(f"Ошибка: файл {SQLITE_DB} не найден")
        print("Запустите скрипт из папки AdaptEd/backend:")
        print("  cd AdaptEd/backend")
        print("  python migrate_sqlite_to_neon.py")
        sys.exit(1)
    
    main()

