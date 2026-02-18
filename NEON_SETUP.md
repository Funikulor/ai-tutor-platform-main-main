# 🗄️ Настройка базы данных на Neon

## 📋 Шаг 1: Создание аккаунта и проекта

1. **Перейдите на Neon**: https://neon.tech
2. **Зарегистрируйтесь** (можно через GitHub)
3. **Создайте новый проект**:
   - Нажмите "Create a project"
   - Выберите регион (ближайший к вам)
   - Название проекта: `adapted` (или любое другое)
   - Нажмите "Create project"

## 📋 Шаг 2: Получение DATABASE_URL

После создания проекта:

1. **Скопируйте Connection String**:
   - В Dashboard проекта найдите раздел "Connection Details"
   - Нажмите на кнопку "Connection string" или "Copy connection string"
   - Выберите формат: **Postgres** (не Pooler)

2. **URL будет выглядеть так**:
   ```
   postgresql://username:password@ep-xxxx-xxxx.region.aws.neon.tech/neondb?sslmode=require
   ```

3. **Или соберите вручную**:
   - Host: `ep-xxxx-xxxx.region.aws.neon.tech`
   - Database: `neondb` (по умолчанию)
   - User: ваш username
   - Password: ваш password
   - Port: `5432`
   - SSL: `require`

## 📋 Шаг 3: Обновление переменных окружения

### В Netlify:

1. Откройте **Site settings** → **Environment variables**
2. Найдите `DATABASE_URL`
3. Замените старое значение Railway на новое значение Neon:
   ```
   DATABASE_URL=postgresql://username:password@ep-xxxx-xxxx.region.aws.neon.tech/neondb?sslmode=require
   ```
4. Нажмите **Save**

### Локально (если нужно):

В файле `AdaptEd/backend/.env`:
```env
DATABASE_URL=postgresql://username:password@ep-xxxx-xxxx.region.aws.neon.tech/neondb?sslmode=require
```

## 📋 Шаг 4: Создание таблиц

Таблицы создадутся **автоматически** при первом запуске backend через `init_db()`.

Если нужно создать вручную:
```bash
cd AdaptEd/backend
python -c "from utils.db import init_db; init_db()"
```

## ✅ Проверка подключения

После обновления `DATABASE_URL` в Netlify:

1. **Перезапустите деплой** (или подождите автоматического перезапуска)
2. Проверьте логи Netlify Function:
   - Functions → api → View logs
   - Должны быть сообщения об успешном подключении к БД

3. **Проверьте работу API**:
   - Откройте: `https://web-tutor-ai.netlify.app/api/`
   - Должно работать без ошибок

## 🔧 Важные замечания

1. **SSL обязателен**: Neon требует `?sslmode=require` в connection string
2. **Бесплатный план**: 
   - 0.5 GB storage
   - Автоматическое приостановление после 5 минут неактивности
   - Автоматическое пробуждение при запросе (небольшая задержка)
3. **Миграция данных**: Если нужно перенести данные из Railway:
   - Экспортируйте данные из Railway (pg_dump)
   - Импортируйте в Neon (psql или через Dashboard)

## 🆘 Решение проблем

### Ошибка подключения

- Проверьте, что `sslmode=require` есть в URL
- Убедитесь, что пароль правильный
- Проверьте, что проект Neon активен

### Таблицы не создаются

- Проверьте логи backend
- Убедитесь, что `init_db()` вызывается
- Проверьте права доступа к базе данных

### Медленные запросы

- Neon на бесплатном плане может "засыпать" после неактивности
- Первый запрос после пробуждения может быть медленным (1-2 секунды)
- Это нормально для бесплатного плана

## 📝 Формат DATABASE_URL для Neon

```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

Пример:
```
postgresql://neondb_owner:your_password@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

---

## 🎉 Готово!

После настройки Neon и обновления `DATABASE_URL` в Netlify, база данных будет работать на бесплатном плане Neon.

