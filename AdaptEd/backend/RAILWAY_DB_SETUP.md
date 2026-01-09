# Настройка подключения к PostgreSQL на Railway

## ✅ Что уже сделано

1. ✅ Создан файл `.env` с `DATABASE_URL` для Railway
2. ✅ Установлен драйвер `psycopg2-binary`
3. ✅ Подключение проверено и работает

## 📋 Текущие настройки

**База данных:** PostgreSQL 17.7 на Railway  
**URL:** `postgresql://postgres:...@shortline.proxy.rlwy.net:19185/railway`

## 🚀 Запуск приложения

При первом запуске приложения таблицы создадутся автоматически:

```bash
cd C:\Users\Admin\Desktop\ai-tutor-platform-main-main\AdaptEd\backend
npm run dev
```

Или через Python:

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## 🔍 Проверка подключения

Для проверки подключения к базе данных:

```bash
python check_postgres_connection.py
```

## 📊 Создаваемые таблицы

При первом запуске будут созданы следующие таблицы:

- `documents` - документы для обучения
- `tests` - тесты
- `test_questions` - вопросы тестов
- `test_submissions` - ответы на тесты
- `homeworks` - домашние задания
- `homework_submissions` - сдачи домашних заданий

## ⚠️ Важно

1. **Безопасность:** Файл `.env` уже добавлен в `.gitignore` и не будет загружен в репозиторий
2. **Подключение:** Убедитесь, что Railway база данных активна
3. **Драйвер:** `psycopg2-binary` должен быть установлен (уже в requirements.txt)

## 🔧 Решение проблем

### Ошибка подключения

1. Проверьте, что Railway база данных активна
2. Проверьте `DATABASE_URL` в `.env` файле
3. Убедитесь, что установлен `psycopg2-binary`:
   ```bash
   pip install psycopg2-binary
   ```

### Таблицы не создаются

1. Проверьте логи при запуске приложения
2. Убедитесь, что `init_db()` вызывается в `app.py`
3. Проверьте права доступа к базе данных

### Проверка существующих таблиц

Подключитесь к базе через Railway CLI или используйте скрипт:

```bash
python check_postgres_connection.py
```

## 📝 Пример использования

После запуска приложения все API endpoints будут работать с PostgreSQL на Railway:

- `/api/v1/auth/*` - авторизация
- `/assistant/*` - чат-ассистент
- `/tests/*` - тесты
- `/homework/*` - домашние задания

Все данные теперь хранятся в облачной базе данных Railway!



