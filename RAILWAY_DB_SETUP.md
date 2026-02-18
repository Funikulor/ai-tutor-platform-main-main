# 🗄️ Настройка базы данных на Railway

## ✅ Автоматическое создание таблиц

Railway база данных автоматически создаст все таблицы при первом запуске backend!

## 📋 Шаги:

### 1. Установите DATABASE_URL в Railway

1. **Railway Dashboard** → Ваш backend сервис → Variables
2. **Добавьте переменную**:
   ```
   DATABASE_URL=postgresql://postgres:MZwAJfqAVDejANZlhTVAmMKhBGnahHVG@switchyard.proxy.rlwy.net:49224/railway
   ```

### 2. Запустите backend на Railway

Backend автоматически:
- Подключится к базе данных
- Создаст все таблицы через `init_db()`
- Будет готов к работе

### 3. Проверьте создание таблиц

После запуска backend проверьте логи:
- Railway Dashboard → Ваш backend сервис → Deployments → View Logs
- Должно быть: `Таблицы созданы успешно` или подобное сообщение

### 4. Добавление данных

После создания таблиц данные можно добавить:

#### Вариант 1: Через сам backend (рекомендуется)

1. Запустите backend на Railway
2. Используйте API endpoints для создания данных:
   - `/auth/register` - регистрация пользователей
   - `/tests/` - создание тестов
   - `/homework/` - создание домашних заданий

#### Вариант 2: Через Railway CLI

```bash
# Установите Railway CLI
npm i -g @railway/cli

# Войдите
railway login

# Подключитесь к базе
railway connect

# Теперь вы в psql консоли, можете выполнять SQL команды
```

#### Вариант 3: Через Railway Dashboard

1. Railway Dashboard → Ваша база данных → Query
2. Выполните SQL команды для вставки данных

## 🔍 Проверка таблиц

После запуска backend, таблицы должны быть созданы:
- `users`
- `documents`
- `tests`
- `test_questions`
- `test_submissions`
- `homeworks`
- `homework_submissions`

## 📝 Пример SQL для добавления тестовых данных

После создания таблиц, можно выполнить в Railway Query:

```sql
-- Создание тестового пользователя
INSERT INTO users (email, password_hash, full_name, role, created_at)
VALUES ('admin@example.com', 'hashed_password', 'Admin User', 'admin', NOW())
ON CONFLICT (email) DO NOTHING;

-- Создание тестового теста
INSERT INTO tests (title, description, created_at)
VALUES ('Тестовый тест', 'Описание теста', NOW())
ON CONFLICT DO NOTHING;
```

## ⚠️ Важно

- Railway база данных может "засыпать" на бесплатном плане
- Первое подключение может занять несколько секунд
- Убедитесь, что `DATABASE_URL` правильно установлен в Variables

## 🆘 Если таблицы не создаются

1. Проверьте логи backend в Railway
2. Убедитесь, что `DATABASE_URL` установлен
3. Проверьте, что backend успешно запустился
4. Убедитесь, что `init_db()` вызывается в `app.py`

