"""
Скрипт для проверки и создания всех таблиц в Railway PostgreSQL
"""
import psycopg2
from sqlalchemy import create_engine, inspect
import os
import sys

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

def check_tables():
    """Проверяет, какие таблицы есть в Railway"""
    print("=" * 60)
    print("ПРОВЕРКА ТАБЛИЦ В RAILWAY")
    print("=" * 60)
    
    try:
        engine = create_engine(RAILWAY_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nНайдено таблиц: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        return tables, engine
        
    except Exception as e:
        print(f"Ошибка при проверке таблиц: {e}")
        import traceback
        traceback.print_exc()
        return [], None

def create_all_tables():
    """Создает все таблицы используя init_db()"""
    print("\n" + "=" * 60)
    print("СОЗДАНИЕ ВСЕХ ТАБЛИЦ")
    print("=" * 60)
    
    try:
        # Временно устанавливаем DATABASE_URL
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = RAILWAY_DB_URL
        
        # Импортируем и вызываем init_db
        from utils.db import init_db
        init_db()
        
        print("Таблицы созданы успешно!")
        
        # Восстанавливаем оригинальный DATABASE_URL
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            del os.environ['DATABASE_URL']
            
        return True
        
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_homeworks():
    """Мигрирует данные homeworks из SQLite в Railway"""
    print("\n" + "=" * 60)
    print("МИГРАЦИЯ ДАННЫХ HOMEWORKS")
    print("=" * 60)
    
    import sqlite3
    
    SQLITE_DB = "adapted.db"
    
    if not os.path.exists(SQLITE_DB):
        print(f"Файл {SQLITE_DB} не найден!")
        return
    
    # Подключение к SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    
    # Получаем данные из SQLite
    sqlite_cur.execute("SELECT * FROM homeworks")
    rows = sqlite_cur.fetchall()
    
    if not rows:
        print("Нет данных в таблице homeworks")
        sqlite_conn.close()
        return
    
    # Получаем названия колонок
    columns = [description[0] for description in sqlite_cur.description]
    
    # Подключение к Railway
    pg_conn = psycopg2.connect(RAILWAY_DB_URL)
    pg_cur = pg_conn.cursor()
    
    # Вставляем данные
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    
    count = 0
    for row in rows:
        values = [None if v is None else v for v in row]
        
        query = f"""
            INSERT INTO homeworks ({columns_str}) 
            VALUES ({placeholders}) 
            ON CONFLICT DO NOTHING
        """
        try:
            pg_cur.execute(query, values)
            count += 1
        except Exception as e:
            print(f"Ошибка при вставке: {e}")
            continue
    
    pg_conn.commit()
    print(f"Мигрировано {count} записей из homeworks")
    
    sqlite_conn.close()
    pg_conn.close()

def main():
    print("=" * 60)
    print("ПРОВЕРКА И СОЗДАНИЕ ТАБЛИЦ В RAILWAY")
    print("=" * 60)
    
    # Проверяем таблицы
    tables, engine = check_tables()
    
    # Создаем все таблицы
    if create_all_tables():
        # Проверяем снова
        tables, engine = check_tables()
    
    # Мигрируем данные homeworks
    if 'homeworks' in tables:
        migrate_homeworks()
    else:
        print("\nТаблица homeworks не найдена после создания. Проверьте логи.")
    
    print("\n" + "=" * 60)
    print("ГОТОВО!")
    print("=" * 60)

if __name__ == "__main__":
    main()

