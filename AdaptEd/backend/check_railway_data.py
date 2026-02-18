"""
Скрипт для проверки данных в Railway PostgreSQL
"""
import psycopg2
import time

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

def check_data():
    """Проверяет данные в Railway"""
    print("=" * 60)
    print("ПРОВЕРКА ДАННЫХ В RAILWAY")
    print("=" * 60)
    
    for attempt in range(3):
        try:
            conn = psycopg2.connect(RAILWAY_DB_URL)
            cur = conn.cursor()
            
            # Проверяем все таблицы
            tables = ['users', 'documents', 'tests', 'test_questions', 'test_submissions', 'homeworks', 'homework_submissions']
            
            print("\nПроверка данных в таблицах:")
            print("-" * 60)
            
            total_rows = 0
            for table in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"  {table}: {count} записей")
                    total_rows += count
                    
                    # Если есть данные, показываем первые несколько записей
                    if count > 0 and count <= 5:
                        cur.execute(f"SELECT * FROM {table} LIMIT 3")
                        rows = cur.fetchall()
                        if rows:
                            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
                            columns = [row[0] for row in cur.fetchall()]
                            print(f"    Колонки: {', '.join(columns[:5])}...")
                            for i, row in enumerate(rows, 1):
                                print(f"    Запись {i}: {str(row)[:100]}...")
                    elif count > 5:
                        cur.execute(f"SELECT * FROM {table} LIMIT 1")
                        row = cur.fetchone()
                        if row:
                            print(f"    Пример записи: {str(row)[:100]}...")
                except Exception as e:
                    print(f"  {table}: Ошибка - {e}")
            
            print("-" * 60)
            print(f"Всего записей во всех таблицах: {total_rows}")
            
            conn.close()
            return True
            
        except Exception as e:
            if attempt < 2:
                print(f"[WARN] Ошибка подключения (попытка {attempt + 1}/3): {e}")
                print("  Повторная попытка через 3 секунды...")
                time.sleep(3)
            else:
                print(f"[ERROR] Не удалось подключиться к Railway: {e}")
                return False
    
    return False

if __name__ == "__main__":
    check_data()

