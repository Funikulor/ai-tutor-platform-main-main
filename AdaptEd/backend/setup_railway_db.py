"""
Простой скрипт для создания таблиц и заполнения данных в Railway PostgreSQL
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sqlite3
import os

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

# Локальная SQLite база
SQLITE_DB = "adapted.db"

def setup_railway_database():
    """Создает таблицы и заполняет данные в Railway"""
    print("=" * 60)
    print("НАСТРОЙКА БАЗЫ ДАННЫХ RAILWAY")
    print("=" * 60)
    
    try:
        # Подключение к Railway
        print("\nПодключение к Railway PostgreSQL...")
        conn = psycopg2.connect(RAILWAY_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        print("Подключено успешно!")
        
        # Проверяем существующие таблицы
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cur.fetchall()]
        print(f"\nСуществующие таблицы: {existing_tables}")
        
        # Если таблиц нет, создадим их через backend при первом запуске
        # Сейчас просто мигрируем данные, если таблицы есть
        
        if 'users' in existing_tables:
            print("\nТаблицы уже существуют. Мигрируем данные...")
            
            # Мигрируем данные из SQLite
            if os.path.exists(SQLITE_DB):
                sqlite_conn = sqlite3.connect(SQLITE_DB)
                sqlite_cur = sqlite_conn.cursor()
                
                # Мигрируем homeworks
                if 'homeworks' in existing_tables:
                    sqlite_cur.execute("SELECT * FROM homeworks")
                    rows = sqlite_cur.fetchall()
                    
                    if rows:
                        columns = [desc[0] for desc in sqlite_cur.description]
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
                                cur.execute(query, values)
                                count += 1
                            except Exception as e:
                                print(f"Ошибка при вставке: {e}")
                        
                        print(f"Мигрировано {count} записей из homeworks")
                
                sqlite_conn.close()
        else:
            print("\nТаблицы не найдены.")
            print("Таблицы будут созданы автоматически при первом запуске backend на Railway.")
            print("После запуска backend, запустите этот скрипт снова для миграции данных.")
        
        conn.close()
        print("\n" + "=" * 60)
        print("ГОТОВО!")
        print("=" * 60)
        print("\nСледующие шаги:")
        print("1. Убедитесь, что DATABASE_URL установлен в Railway:")
        print("   Service settings -> Variables -> DATABASE_URL")
        print(f"   Значение: {RAILWAY_DB_URL}")
        print("2. Запустите backend на Railway - таблицы создадутся автоматически")
        print("3. После создания таблиц запустите этот скрипт снова для миграции данных")
        
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_railway_database()

