# 🔄 Миграция базы данных с Railway на Neon

## 📋 Подготовка

### Что нужно:
- Доступ к старой базе Railway (пока она еще работает)
- Установленный PostgreSQL клиент (`psql`) или `pg_dump`
- Или используйте онлайн инструменты

---

## 🎯 Вариант 1: Через pg_dump (Рекомендуется)

### Шаг 1: Экспорт данных из Railway

```bash
# Установите PostgreSQL клиент (если еще не установлен)
# Windows: скачайте с https://www.postgresql.org/download/windows/
# Или используйте WSL

# Экспортируйте данные
pg_dump "postgresql://postgres:aiESxgjbPbpNrAuZuuCAbfjeAhGXPMsj@shortline.proxy.rlwy.net:19185/railway" \
  --format=custom \
  --file=railway_backup.dump

# Или в простом SQL формате
pg_dump "postgresql://postgres:aiESxgjbPbpNrAuZuuCAbfjeAhGXPMsj@shortline.proxy.rlwy.net:19185/railway" \
  --file=railway_backup.sql
```

### Шаг 2: Создайте базу на Neon

1. Зайдите на https://neon.tech
2. Создайте проект
3. Скопируйте Connection String

### Шаг 3: Импорт данных в Neon

```bash
# Импорт из custom формата
pg_restore -d "postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require" \
  --clean \
  --if-exists \
  railway_backup.dump

# Или из SQL файла
psql "postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require" \
  < railway_backup.sql
```

---

## 🎯 Вариант 2: Через Python скрипт

Создайте файл `migrate_db.py`:

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Старая база Railway
OLD_DB_URL = "postgresql://postgres:aiESxgjbPbpNrAuZuuCAbfjeAhGXPMsj@shortline.proxy.rlwy.net:19185/railway"

# Новая база Neon (замените на ваш URL)
NEW_DB_URL = "postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"

def migrate_table(old_conn, new_conn, table_name):
    """Мигрирует данные из одной таблицы в другую"""
    with old_conn.cursor(cursor_factory=RealDictCursor) as old_cur:
        with new_conn.cursor() as new_cur:
            # Получаем данные
            old_cur.execute(f"SELECT * FROM {table_name}")
            rows = old_cur.fetchall()
            
            if not rows:
                print(f"Таблица {table_name} пустая, пропускаем")
                return
            
            # Получаем колонки
            columns = list(rows[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            # Вставляем данные
            for row in rows:
                values = [row[col] for col in columns]
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                new_cur.execute(query, values)
            
            new_conn.commit()
            print(f"Мигрировано {len(rows)} записей из {table_name}")

# Подключения
old_conn = psycopg2.connect(OLD_DB_URL)
new_conn = psycopg2.connect(NEW_DB_URL)

try:
    # Список таблиц для миграции
    tables = [
        'users',
        'documents',
        'tests',
        'test_questions',
        'test_submissions',
        'homeworks',
        'homework_submissions'
    ]
    
    for table in tables:
        try:
            migrate_table(old_conn, new_conn, table)
        except Exception as e:
            print(f"Ошибка при миграции {table}: {e}")
    
    print("Миграция завершена!")
    
finally:
    old_conn.close()
    new_conn.close()
```

Запуск:
```bash
cd AdaptEd/backend
pip install psycopg2-binary
python migrate_db.py
```

---

## 🎯 Вариант 3: Через Neon Dashboard (Самый простой)

### Если данных немного или база новая:

1. **Создайте проект на Neon**
2. **Обновите DATABASE_URL в Netlify**
3. **Таблицы создадутся автоматически** при первом запуске через `init_db()`
4. **Данные можно добавить вручную** через интерфейс или API

---

## 🎯 Вариант 4: Экспорт через SQL запросы

Если у вас есть доступ к Railway через веб-интерфейс или psql:

```sql
-- Экспорт таблицы users
COPY (SELECT * FROM users) TO STDOUT WITH CSV HEADER;

-- Или через SELECT
SELECT * FROM users;
```

Затем импортируйте в Neon через SQL Editor или psql.

---

## 📋 Пошаговая инструкция (Рекомендуемый способ)

### 1. Создайте базу на Neon

- Зайдите на https://neon.tech
- Создайте проект
- Скопируйте Connection String

### 2. Экспортируйте схему (структуру таблиц)

```bash
# Только схема без данных
pg_dump "postgresql://postgres:aiESxgjbPbpNrAuZuuCAbfjeAhGXPMsj@shortline.proxy.rlwy.net:19185/railway" \
  --schema-only \
  --file=schema.sql
```

### 3. Импортируйте схему в Neon

```bash
psql "postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require" \
  < schema.sql
```

### 4. Экспортируйте данные

```bash
# Только данные
pg_dump "postgresql://postgres:aiESxgjbPbpNrAuZuuCAbfjeAhGXPMsj@shortline.proxy.rlwy.net:19185/railway" \
  --data-only \
  --file=data.sql
```

### 5. Импортируйте данные в Neon

```bash
psql "postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require" \
  < data.sql
```

### 6. Обновите DATABASE_URL в Netlify

- Site settings → Environment variables
- Замените `DATABASE_URL` на новый Neon URL
- Сохраните

### 7. Перезапустите деплой

Netlify автоматически перезапустит функцию с новым DATABASE_URL.

---

## ✅ Проверка после миграции

1. **Проверьте подключение**:
   ```bash
   psql "postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require" \
     -c "SELECT COUNT(*) FROM users;"
   ```

2. **Проверьте работу API**:
   - Откройте: `https://web-tutor-ai.netlify.app/api/`
   - Попробуйте залогиниться

3. **Проверьте логи Netlify**:
   - Functions → api → View logs
   - Не должно быть ошибок подключения к БД

---

## 🆘 Решение проблем

### Ошибка "connection refused"

- Проверьте, что Railway база еще доступна
- Убедитесь, что URL правильный

### Ошибка при импорте в Neon

- Убедитесь, что `sslmode=require` есть в URL
- Проверьте, что таблицы не существуют (или используйте `--clean`)

### Данные не переносятся

- Проверьте, что таблицы созданы в Neon
- Убедитесь, что порядок импорта правильный (сначала схема, потом данные)

---

## 💡 Совет

Если база данных небольшая или вы только начинаете проект:
- **Проще всего**: Создать новую базу на Neon и начать с чистого листа
- Таблицы создадутся автоматически при первом запуске
- Пользователей можно зарегистрировать заново через интерфейс

---

## 🎉 Готово!

После миграции обновите `DATABASE_URL` в Netlify, и всё будет работать на Neon!

