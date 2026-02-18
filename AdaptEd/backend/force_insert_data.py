"""
Скрипт для принудительной вставки данных в Railway PostgreSQL
"""
import sqlite3
import psycopg2
import os
import time

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

# Локальная SQLite база
SQLITE_DB = "adapted.db"

def force_insert_homeworks():
    """Принудительно вставляет данные из homeworks"""
    print("=" * 60)
    print("ПРИНУДИТЕЛЬНАЯ ВСТАВКА ДАННЫХ HOMEWORKS")
    print("=" * 60)
    
    if not os.path.exists(SQLITE_DB):
        print(f"Файл {SQLITE_DB} не найден!")
        return False
    
    # Подключение к SQLite
    print("\nЧтение данных из SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    
    sqlite_cur.execute("SELECT * FROM homeworks")
    rows = sqlite_cur.fetchall()
    
    if not rows:
        print("Нет данных в таблице homeworks в SQLite")
        sqlite_conn.close()
        return False
    
    columns = [description[0] for description in sqlite_cur.description]
    print(f"Найдено {len(rows)} записей")
    print(f"Колонки: {', '.join(columns)}")
    
    # Подключение к Railway
    print("\nПодключение к Railway...")
    for attempt in range(3):
        try:
            pg_conn = psycopg2.connect(RAILWAY_DB_URL)
            pg_cur = pg_conn.cursor()
            print("[OK] Подключено к Railway")
            break
        except Exception as e:
            if attempt < 2:
                print(f"[WARN] Ошибка подключения (попытка {attempt + 1}/3): {e}")
                time.sleep(3)
            else:
                print(f"[ERROR] Не удалось подключиться: {e}")
                sqlite_conn.close()
                return False
    
    # Проверяем структуру таблицы в Railway
    print("\nПроверка структуры таблицы homeworks в Railway...")
    pg_cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'homeworks'
        ORDER BY ordinal_position
    """)
    railway_columns = {row[0]: row[1] for row in pg_cur.fetchall()}
    
    if not railway_columns:
        print("[ERROR] Таблица homeworks не найдена в Railway!")
        pg_conn.close()
        sqlite_conn.close()
        return False
    
    print(f"Колонки в Railway: {', '.join(railway_columns.keys())}")
    
    # Вставляем данные
    print("\nВставка данных...")
    inserted = 0
    updated = 0
    errors = 0
    
    for row in rows:
        # Создаем словарь значений
        values_dict = dict(zip(columns, row))
        
        # Формируем список колонок и значений для вставки
        railway_cols = [col for col in columns if col in railway_columns]
        values = [values_dict.get(col) for col in railway_cols]
        
        placeholders = ', '.join(['%s'] * len(railway_cols))
        columns_str = ', '.join(railway_cols)
        
        # Пробуем вставить с ON CONFLICT
        query = f"""
            INSERT INTO homeworks ({columns_str}) 
            VALUES ({placeholders})
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                updated_at = NOW()
        """
        
        try:
            pg_cur.execute(query, values)
            if pg_cur.rowcount > 0:
                # Проверяем, была ли это вставка или обновление
                pg_cur.execute("SELECT COUNT(*) FROM homeworks WHERE id = %s", (values_dict.get('id'),))
                if pg_cur.fetchone()[0] > 0:
                    inserted += 1
                else:
                    updated += 1
        except Exception as e:
            errors += 1
            print(f"  [ERROR] Ошибка при вставке записи ID={values_dict.get('id')}: {e}")
            # Пробуем без ON CONFLICT
            try:
                query_simple = f"""
                    INSERT INTO homeworks ({columns_str}) 
                    VALUES ({placeholders})
                """
                pg_cur.execute(query_simple, values)
                inserted += 1
            except Exception as e2:
                print(f"    [ERROR] Повторная ошибка: {e2}")
    
    pg_conn.commit()
    
    print(f"\n[OK] Вставлено новых: {inserted}")
    print(f"[OK] Обновлено: {updated}")
    if errors > 0:
        print(f"[WARN] Ошибок: {errors}")
    
    # Проверяем результат
    pg_cur.execute("SELECT COUNT(*) FROM homeworks")
    final_count = pg_cur.fetchone()[0]
    print(f"\nВсего записей в homeworks: {final_count}")
    
    pg_conn.close()
    sqlite_conn.close()
    
    return True

if __name__ == "__main__":
    force_insert_homeworks()

