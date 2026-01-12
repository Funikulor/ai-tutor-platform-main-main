# Таблица users в базе данных

## Описание

Таблица `users` хранит информацию о всех пользователях системы: студентах, учителях, родителях и администраторах.

## Структура таблицы

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer (PK) | Автоинкрементный ID |
| `user_id` | String(64) | Уникальный ID пользователя (например, "student_001") |
| `email` | String(255) | Email (уникальный, индексирован) |
| `password_hash` | String(255) | Хеш пароля (SHA-256) |
| `full_name` | String(255) | Полное имя пользователя |
| `role` | Enum | Роль: `student`, `teacher`, `parent`, `admin` |
| `class_id` | String(50) | ID класса (для учеников, опционально) |
| `phone` | String(20) | Телефон (опционально) |
| `is_active` | Boolean | Активен ли пользователь (по умолчанию `true`) |
| `created_at` | DateTime | Дата создания записи |
| `updated_at` | DateTime | Дата последнего обновления |

## Роли пользователей

- **student** - Ученик
- **teacher** - Учитель
- **parent** - Родитель
- **admin** - Администратор

## Индексы

- `user_id` - уникальный индекс
- `email` - уникальный индекс
- `role` - индекс для быстрого поиска по ролям

## Использование

### Создание таблицы

Таблица создается автоматически при первом запуске приложения или вручную:

```bash
python create_users_table.py
```

### Проверка существования

```bash
python check_postgres_connection.py
```

Должна быть видна таблица `users` в списке.

### Примеры SQL запросов

**Получить всех пользователей:**
```sql
SELECT user_id, email, full_name, role, is_active 
FROM users;
```

**Получить всех студентов:**
```sql
SELECT user_id, email, full_name, class_id 
FROM users 
WHERE role = 'student' AND is_active = true;
```

**Получить всех учителей:**
```sql
SELECT user_id, email, full_name 
FROM users 
WHERE role = 'teacher' AND is_active = true;
```

**Получить всех администраторов:**
```sql
SELECT user_id, email, full_name 
FROM users 
WHERE role = 'admin' AND is_active = true;
```

**Найти пользователя по email:**
```sql
SELECT * FROM users WHERE email = 'student@example.com';
```

**Найти пользователя по user_id:**
```sql
SELECT * FROM users WHERE user_id = 'student_001';
```

## Интеграция с существующим кодом

Таблица `users` интегрирована с:

1. **Моделью auth.py** - Pydantic модели для API
2. **AuthService** - сервис авторизации (можно расширить для работы с БД)
3. **Routes auth.py** - API endpoints для регистрации и входа

## Миграция данных

Если у вас уже есть пользователи в `persistent_storage` (JSON), можно создать скрипт миграции:

```python
from utils.db import get_db
from models.user_db import User
from utils.persistent_storage import persistent_storage

def migrate_users():
    db = get_db()
    if not db:
        return
    
    users = persistent_storage.get("users", {})
    for user_id, user_data in users.items():
        # Проверяем, не существует ли уже
        existing = db.query(User).filter(User.user_id == user_id).first()
        if not existing:
            user = User(
                user_id=user_id,
                email=user_data.get("email"),
                password_hash=user_data.get("password"),
                full_name=user_data.get("full_name"),
                role=user_data.get("role"),
                class_id=user_data.get("class_id"),
                phone=user_data.get("phone"),
                is_active=user_data.get("is_active", True),
                created_at=user_data.get("created_at")
            )
            db.add(user)
    
    db.commit()
    print(f"Мигрировано {len(users)} пользователей")
```

## Безопасность

- ✅ Пароли хранятся в виде хешей (SHA-256)
- ✅ Email уникален (нельзя создать двух пользователей с одним email)
- ✅ `user_id` уникален
- ✅ Индексы для быстрого поиска
- ✅ Поле `is_active` для деактивации пользователей без удаления

## Расширение

В будущем можно добавить:

- Связи с другими таблицами (foreign keys)
- Дополнительные поля (avatar, bio, etc.)
- Таблицу для сессий пользователей
- Таблицу для прав доступа (permissions)




