"""
Скрипт для создания тестовых данных в Railway PostgreSQL
"""
import psycopg2
import time
from datetime import datetime, timedelta

# Railway PostgreSQL база
RAILWAY_DB_URL = "postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway"

def create_sample_data():
    """Создает тестовые данные во всех таблицах"""
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ В RAILWAY")
    print("=" * 60)
    
    for attempt in range(3):
        try:
            conn = psycopg2.connect(RAILWAY_DB_URL)
            cur = conn.cursor()
            print("[OK] Подключено к Railway")
            break
        except Exception as e:
            if attempt < 2:
                print(f"[WARN] Ошибка подключения (попытка {attempt + 1}/3): {e}")
                time.sleep(3)
            else:
                print(f"[ERROR] Не удалось подключиться: {e}")
                return
    
    try:
        # Проверяем, какие значения enum есть в базе
        print("\nПроверка enum значений для роли...")
        cur.execute("""
            SELECT unnest(enum_range(NULL::userroleenum))
        """)
        enum_values = [row[0] for row in cur.fetchall()]
        print(f"   Доступные роли: {enum_values}")
        
        # Используем первое доступное значение или 'student'
        role_value = enum_values[0] if enum_values else 'student'
        
        # 1. Создаем тестового пользователя
        print("\n1. Создание тестового пользователя...")
        import uuid
        user_id = str(uuid.uuid4())
        # Используем ADMIN роль
        admin_role = 'ADMIN' if 'ADMIN' in enum_values else role_value
        cur.execute("""
            INSERT INTO users (user_id, email, password_hash, full_name, role, is_active, created_at, updated_at)
            VALUES (%s, 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqB5J5K5K6', 'Admin User', %s::userroleenum, TRUE, NOW(), NOW())
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (user_id, admin_role))
        result = cur.fetchone()
        if result:
            admin_id = result[0]
            print(f"   [OK] Создан пользователь с ID: {admin_id}")
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
        
        # 2. Создаем тестовый документ (пропускаем, если структура неизвестна)
        print("\n2. Пропуск создания документа (структура может отличаться)")
        
        # 3. Создаем тестовый тест
        print("\n3. Создание тестового теста...")
        cur.execute("""
            INSERT INTO tests (title, description, created_by, created_at)
            VALUES ('Тестовый тест', 'Описание тестового теста', %s, NOW())
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (admin_id,))
        result = cur.fetchone()
        if result:
            test_id = result[0]
            print(f"   [OK] Создан тест с ID: {test_id}")
            
            # Создаем вопросы для теста
            print("\n4. Создание вопросов для теста...")
            questions = [
                ('Вопрос 1', 'Вариант A', 'Вариант B', 'Вариант C', 'Вариант D', 'A'),
                ('Вопрос 2', 'Вариант A', 'Вариант B', 'Вариант C', 'Вариант D', 'B'),
            ]
            for q_text, opt_a, opt_b, opt_c, opt_d, correct in questions:
                cur.execute("""
                    INSERT INTO test_questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_answer, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                """, (test_id, q_text, opt_a, opt_b, opt_c, opt_d, correct))
            print(f"   [OK] Создано {len(questions)} вопросов")
        else:
            print("   [OK] Тест уже существует или не создан")
        
        # 5. Проверяем homeworks
        print("\n5. Проверка домашних заданий...")
        cur.execute("SELECT COUNT(*) FROM homeworks")
        hw_count = cur.fetchone()[0]
        print(f"   [OK] Домашних заданий: {hw_count}")
        
        if hw_count == 0:
            print("   Создание тестового домашнего задания...")
            cur.execute("""
                INSERT INTO homeworks (title, description, subject, due_date, status, created_by, created_at)
                VALUES ('Тестовое задание', 'Описание тестового задания', 'Математика', NOW() + INTERVAL '7 days', 'active', %s, NOW())
                ON CONFLICT DO NOTHING
            """, (admin_id,))
            print("   [OK] Создано тестовое домашнее задание")
        
        # Коммитим после каждого важного шага
        conn.commit()
        print("   [OK] Изменения сохранены")
        
        # Финальная проверка
        print("\n" + "=" * 60)
        print("ФИНАЛЬНАЯ ПРОВЕРКА ДАННЫХ")
        print("=" * 60)
        
        tables = ['users', 'documents', 'tests', 'test_questions', 'homeworks']
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count} записей")
            except Exception as e:
                print(f"  {table}: ошибка - {e}")
        
        print("\n[OK] Тестовые данные созданы успешно!")
        
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка при создании данных: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()

if __name__ == "__main__":
    create_sample_data()

