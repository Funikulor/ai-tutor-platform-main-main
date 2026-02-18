"""
Скрипт для заполнения данных в Railway PostgreSQL из локальной SQLite
"""
import sqlite3
import psycopg2
import os
import time

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

# Локальная SQLite база
SQLITE_DB = "adapted.db"

# Список таблиц для миграции
TABLES = [
    'users',
    'documents',
    'tests',
    'test_questions',
    'test_submissions',
    'homeworks',
    'homework_submissions'
]

def migrate_table(sqlite_conn, pg_conn, table_name, retry=3):
    """Мигрирует данные из SQLite в PostgreSQL с повторными попытками"""
    for attempt in range(retry):
        try:
            sqlite_cur = sqlite_conn.cursor()
            pg_cur = pg_conn.cursor()
            
            # Проверяем, существует ли таблица в SQLite
            sqlite_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not sqlite_cur.fetchone():
                print(f"  Таблица {table_name} не найдена в SQLite, пропускаем")
                return 0
            
            # Получаем данные из SQLite
            sqlite_cur.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cur.fetchall()
            
            if not rows:
                print(f"  Таблица {table_name} пустая, пропускаем")
                return 0
            
            # Получаем названия колонок
            columns = [description[0] for description in sqlite_cur.description]
            
            # Проверяем, существует ли таблица в PostgreSQL
            pg_cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (table_name,))
            
            if not pg_cur.fetchone()[0]:
                print(f"  Таблица {table_name} не существует в Railway, пропускаем")
                return 0
            
            # Вставляем данные
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            count = 0
            errors = 0
            
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
                    errors += 1
                    if errors <= 3:  # Показываем только первые 3 ошибки
                        print(f"    Ошибка при вставке записи: {e}")
                    continue
            
            pg_conn.commit()
            
            if count > 0:
                print(f"  [OK] Мигрировано {count} записей из {table_name}")
            if errors > 0:
                print(f"    [WARN] Пропущено {errors} записей из-за ошибок")
            
            return count
            
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            if attempt < retry - 1:
                print(f"  [WARN] Ошибка подключения (попытка {attempt + 1}/{retry}): {e}")
                print(f"    Переподключаемся через 2 секунды...")
                time.sleep(2)
                try:
                    pg_conn.close()
                except:
                    pass
                pg_conn = psycopg2.connect(RAILWAY_DB_URL)
                continue
            else:
                print(f"  [ERROR] Не удалось мигрировать {table_name} после {retry} попыток")
                raise
        except Exception as e:
            print(f"  [ERROR] Ошибка при миграции {table_name}: {e}")
            return 0
    
    return 0

def main():
    print("=" * 60)
    print("ЗАПОЛНЕНИЕ ДАННЫХ В RAILWAY POSTGRESQL")
    print("=" * 60)
    
    # Проверяем наличие SQLite базы
    if not os.path.exists(SQLITE_DB):
        print(f"Ошибка: файл {SQLITE_DB} не найден!")
        print(f"Убедитесь, что вы запускаете скрипт из папки AdaptEd/backend")
        return
    
    # Подключение к SQLite
    print(f"\nПодключение к SQLite: {SQLITE_DB}")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        print("[OK] Подключено к SQLite")
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к SQLite: {e}")
        return
    
    # Подключение к Railway
    print(f"\nПодключение к Railway PostgreSQL...")
    pg_conn = None
    for attempt in range(3):
        try:
            pg_conn = psycopg2.connect(RAILWAY_DB_URL)
            print("[OK] Подключено к Railway")
            break
        except Exception as e:
            if attempt < 2:
                print(f"[WARN] Ошибка подключения (попытка {attempt + 1}/3): {e}")
                print("  Повторная попытка через 3 секунды...")
                time.sleep(3)
            else:
                print(f"[ERROR] Не удалось подключиться к Railway: {e}")
                sqlite_conn.close()
                return
    
    if not pg_conn:
        return
    
    # Проверяем, какие таблицы есть в SQLite
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in sqlite_cur.fetchall()]
    
    print(f"\nНайдено таблиц в SQLite: {len(existing_tables)}")
    print(f"Таблицы: {', '.join(existing_tables)}")
    
    # Проверяем, какие таблицы есть в Railway
    pg_cur = pg_conn.cursor()
    pg_cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    railway_tables = [row[0] for row in pg_cur.fetchall()]
    
    print(f"\nНайдено таблиц в Railway: {len(railway_tables)}")
    print(f"Таблицы: {', '.join(railway_tables)}")
    
    # Миграция данных
    print("\n" + "=" * 60)
    print("НАЧАЛО МИГРАЦИИ ДАННЫХ")
    print("=" * 60)
    
    total_migrated = 0
    for table in TABLES:
        if table in existing_tables and table in railway_tables:
            try:
                count = migrate_table(sqlite_conn, pg_conn, table)
                total_migrated += count
            except Exception as e:
                print(f"  [ERROR] Критическая ошибка при миграции {table}: {e}")
                # Пробуем переподключиться
                try:
                    pg_conn.close()
                except:
                    pass
                try:
                    time.sleep(2)
                    pg_conn = psycopg2.connect(RAILWAY_DB_URL)
                    print("  [OK] Переподключено к Railway")
                except:
                    print("  [ERROR] Не удалось переподключиться")
                    break
        elif table not in existing_tables:
            print(f"  [WARN] Таблица {table} не найдена в SQLite, пропускаем")
        elif table not in railway_tables:
            print(f"  [WARN] Таблица {table} не найдена в Railway, пропускаем")
    
    # Закрываем соединения
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print(f"МИГРАЦИЯ ЗАВЕРШЕНА!")
    print(f"Всего мигрировано записей: {total_migrated}")
    print("=" * 60)

if __name__ == "__main__":
    main()

