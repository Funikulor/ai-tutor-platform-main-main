# Рекомендация по выбору базы данных для AdaptEd

## 🎯 Рекомендация: **PostgreSQL** (основная) + **Redis** (кэш, опционально)

## Анализ требований проекта

### Типы данных в проекте:

1. **Структурированные реляционные данные:**
   - Пользователи (users) с ролями
   - Тесты (tests) → Вопросы (test_questions) → Ответы (test_submissions)
   - Домашние задания (homeworks) → Сдачи (homework_submissions)
   - Документы (documents)

2. **JSON/документные данные:**
   - Когнитивные профили (CognitiveProfile) - сложные вложенные структуры
   - Аналитика учеников (StudentAnalyticsData) - JSON структуры
   - История диалогов
   - Опции вопросов (JSON поля в SQLAlchemy)

3. **Требования:**
   - ✅ ACID транзакции для критичных данных
   - ✅ JSON поддержка для гибких структур
   - ✅ Сложные запросы и аналитика
   - ✅ Масштабируемость
   - ✅ Быстрый доступ к данным пользователя

## Сравнение баз данных

| Критерий | PostgreSQL | MySQL | MongoDB | Redis |
|----------|-----------|-------|---------|-------|
| **Реляционные данные** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| **JSON поддержка** | ⭐⭐⭐⭐⭐ (JSONB) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **ACID транзакции** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Аналитика/запросы** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Масштабируемость** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Интеграция SQLAlchemy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| **Сложность настройки** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Почему PostgreSQL?

### 1. **Идеальное сочетание реляционных и JSON данных**

```python
# Пример: хранение когнитивного профиля в JSONB
class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"
    
    user_id = Column(String, primary_key=True)
    profile_data = Column(JSONB)  # Полный CognitiveProfile как JSON
    
    # Можно делать запросы по JSON полям!
    # SELECT * FROM cognitive_profiles 
    # WHERE profile_data->>'learning_style' = 'visual'
```

### 2. **Мощные аналитические запросы**

```sql
-- Анализ прогресса учеников по темам
SELECT 
    user_id,
    jsonb_array_elements(profile_data->'weak_topics') as weak_topic,
    COUNT(*) as error_count
FROM cognitive_profiles
WHERE profile_data->>'accuracy_rate' < '50'
GROUP BY user_id, weak_topic;
```

### 3. **Уже интегрирован в проект**

Ваш код уже использует SQLAlchemy, который отлично работает с PostgreSQL:

```python
# backend/utils/db.py уже поддерживает PostgreSQL
DATABASE_URL = "postgresql://user:password@localhost/adapted"
```

### 4. **JSONB - лучшая поддержка JSON**

- Индексация JSON полей
- Быстрый поиск по вложенным структурам
- Обновление частей JSON без перезаписи всего документа
- JSON запросы с операторами `->`, `->>`, `@>`

## Архитектура: PostgreSQL + Redis (опционально)

```
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│ PostgreSQL  │  │   Redis     │
│ (основная)  │  │  (кэш)      │
│             │  │             │
│ - Users     │  │ - Сессии    │
│ - Tests     │  │ - Кэш      │
│ - Profiles  │  │ - Rate      │
│ - Analytics │  │   limiting  │
└─────────────┘  └─────────────┘
```

### Когда использовать Redis:

- ✅ Кэширование часто запрашиваемых данных (профили учеников)
- ✅ Сессии пользователей
- ✅ Rate limiting для API
- ✅ Временные данные (токены, очереди)

## Миграция с SQLite на PostgreSQL

### Шаг 1: Установка PostgreSQL

**Windows:**
```powershell
# Скачать с https://www.postgresql.org/download/windows/
# Или через Chocolatey:
choco install postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
```

### Шаг 2: Создание базы данных

```sql
CREATE DATABASE adapted;
CREATE USER adapted_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE adapted TO adapted_user;
```

### Шаг 3: Обновление .env

```env
# backend/.env
DATABASE_URL=postgresql://adapted_user:your_password@localhost:5432/adapted
```

### Шаг 4: Установка драйвера

```bash
pip install psycopg2-binary
# Уже есть в requirements.txt!
```

### Шаг 5: Миграция данных (если нужно)

```python
# Скрипт миграции из SQLite в PostgreSQL
from sqlalchemy import create_engine
import pandas as pd

# SQLite источник
sqlite_engine = create_engine('sqlite:///adapted.db')

# PostgreSQL назначение
pg_engine = create_engine('postgresql://user:pass@localhost/adapted')

# Миграция таблиц
tables = ['users', 'tests', 'test_questions', 'test_submissions', 
          'homeworks', 'homework_submissions', 'documents']

for table in tables:
    df = pd.read_sql_table(table, sqlite_engine)
    df.to_sql(table, pg_engine, if_exists='append', index=False)
```

## Примеры использования JSONB в вашем проекте

### 1. Хранение CognitiveProfile

```python
from sqlalchemy import Column, String, JSONB
from utils.db import Base

class CognitiveProfileDB(Base):
    __tablename__ = "cognitive_profiles"
    
    user_id = Column(String(64), primary_key=True)
    profile_data = Column(JSONB)  # Весь CognitiveProfile как JSON
    
    # Индекс для быстрого поиска
    __table_args__ = (
        Index('ix_profile_learning_style', 
              'profile_data', postgresql_using='gin'),
    )
```

### 2. Запросы по JSON полям

```python
from sqlalchemy import func

# Найти всех визуалов
visual_learners = session.query(CognitiveProfileDB).filter(
    CognitiveProfileDB.profile_data['learning_style'].astext == 'visual'
).all()

# Найти учеников с низкой точностью
low_accuracy = session.query(CognitiveProfileDB).filter(
    func.cast(
        CognitiveProfileDB.profile_data['accuracy_rate'].astext, 
        Float
    ) < 50.0
).all()
```

### 3. Обновление JSON полей

```python
# Обновить только accuracy_rate без перезаписи всего профиля
session.execute(
    update(CognitiveProfileDB)
    .where(CognitiveProfileDB.user_id == user_id)
    .values(
        profile_data=func.jsonb_set(
            CognitiveProfileDB.profile_data,
            '{accuracy_rate}',
            '75.5'
        )
    )
)
```

## Производительность

### PostgreSQL оптимизации:

1. **Индексы на JSONB:**
```sql
CREATE INDEX idx_profile_learning_style 
ON cognitive_profiles USING gin (profile_data jsonb_path_ops);
```

2. **Партиционирование больших таблиц:**
```sql
-- Партиционирование по дате для test_submissions
CREATE TABLE test_submissions_2024 PARTITION OF test_submissions
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

3. **Материализованные представления для аналитики:**
```sql
CREATE MATERIALIZED VIEW student_progress_summary AS
SELECT 
    user_id,
    COUNT(*) as total_tests,
    AVG(score) as avg_score
FROM test_submissions
GROUP BY user_id;
```

## Альтернативные варианты

### Если нужна максимальная простота:
- **SQLite** (текущий вариант) - для разработки и небольших проектов
- ✅ Уже работает
- ❌ Не масштабируется
- ❌ Нет JSONB

### Если нужна максимальная производительность для JSON:
- **MongoDB** - только если убрать все реляционные данные
- ❌ Потеря ACID
- ❌ Сложная миграция
- ❌ Нет интеграции с SQLAlchemy

### Если нужен кэш:
- **Redis** - как дополнение к PostgreSQL
- ✅ Быстрый кэш
- ✅ Сессии
- ✅ Rate limiting

## Итоговая рекомендация

**Для вашего проекта: PostgreSQL**

✅ Идеально подходит для смешанных данных (реляционные + JSON)  
✅ Уже интегрирован через SQLAlchemy  
✅ Мощная аналитика для образовательной платформы  
✅ Масштабируется для роста  
✅ JSONB для гибких структур (профили, аналитика)  

**Дополнительно: Redis** (опционально)
- Для кэширования профилей
- Сессий пользователей
- Rate limiting

## Быстрый старт

```bash
# 1. Установить PostgreSQL
# 2. Создать БД
createdb adapted

# 3. Обновить .env
DATABASE_URL=postgresql://user:pass@localhost/adapted

# 4. Запустить приложение
# SQLAlchemy автоматически создаст таблицы при первом запуске
python -m uvicorn app:app --reload
```

## Полезные ссылки

- [PostgreSQL JSONB документация](https://www.postgresql.org/docs/current/datatype-json.html)
- [SQLAlchemy + PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [PostgreSQL индексы для JSONB](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING)







