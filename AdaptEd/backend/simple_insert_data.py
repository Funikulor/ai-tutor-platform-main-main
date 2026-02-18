"""
Простой скрипт для вставки данных в Railway - только пользователь и документ
"""
import psycopg2
import time
import uuid

RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

def insert_data():
    """Вставляет простые данные"""
    print("=" * 60)
    print("ВСТАВКА ДАННЫХ В RAILWAY")
    print("=" * 60)
    
    for attempt in range(3):
        try:
            conn = psycopg2.connect(RAILWAY_DB_URL)
            cur = conn.cursor()
            print("[OK] Подключено к Railway")
            break
        except Exception as e:
            if attempt < 2:
                print(f"[WARN] Ошибка (попытка {attempt + 1}/3): {e}")
                time.sleep(3)
            else:
                print(f"[ERROR] Не удалось подключиться: {e}")
                return
    
    try:
        # 1. Пользователь
        print("\n1. Создание пользователя...")
        user_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (user_id, email, password_hash, full_name, role, is_active, created_at, updated_at)
            VALUES (%s, 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqB5J5K5K6', 'Admin User', 'ADMIN'::userroleenum, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (user_id,))
        result = cur.fetchone()
        if result:
            admin_id = result[0]
            print(f"   [OK] Пользователь создан, ID: {admin_id}")
        else:
            cur.execute("SELECT id FROM users WHERE email = 'admin@example.com'")
            result = cur.fetchone()
            if result:
                admin_id = result[0]
                print(f"   [OK] Пользователь уже существует, ID: {admin_id}")
            else:
                print("   [ERROR] Не удалось создать/найти пользователя")
                conn.close()
                return
        
        conn.commit()
        print("   [OK] Изменения сохранены")
        
        # 2. Документ
        print("\n2. Создание документа...")
        cur.execute("""
            INSERT INTO documents (title, content, created_at)
            VALUES ('Тестовый документ', 'Содержимое тестового документа', NOW())
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        result = cur.fetchone()
        if result:
            print(f"   [OK] Документ создан, ID: {result[0]}")
        else:
            print("   [OK] Документ уже существует или не создан")
        
        conn.commit()
        print("   [OK] Изменения сохранены")
        
        # Проверка
        print("\n" + "=" * 60)
        print("ПРОВЕРКА ДАННЫХ")
        print("=" * 60)
        
        cur.execute("SELECT COUNT(*) FROM users")
        users_count = cur.fetchone()[0]
        print(f"  users: {users_count} записей")
        
        cur.execute("SELECT COUNT(*) FROM documents")
        docs_count = cur.fetchone()[0]
        print(f"  documents: {docs_count} записей")
        
        cur.execute("SELECT COUNT(*) FROM homeworks")
        hw_count = cur.fetchone()[0]
        print(f"  homeworks: {hw_count} записей")
        
        print(f"\nВсего записей: {users_count + docs_count + hw_count}")
        print("\n[OK] Данные успешно добавлены!")
        
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()

if __name__ == "__main__":
    insert_data()

