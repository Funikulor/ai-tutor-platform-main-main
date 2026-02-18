# 🔧 Исправление ошибки "Could not import module 'main'"

## Проблема

Railway не может найти модуль `app`, потому что:
1. Root Directory не установлен правильно
2. Railway использует Procfile вместо railway.json
3. Команда запуска выполняется не из правильной директории

## ✅ Решение

### Вариант 1: Убедитесь, что Root Directory установлен

1. **Railway Dashboard** → Ваш сервис → Settings
2. **Найдите "Source"** или "Root Directory"
3. **Установите**: `AdaptEd/backend`
4. **Сохраните** и перезапустите деплой

### Вариант 2: Обновите Procfile

Railway может использовать Procfile вместо railway.json. Обновите `AdaptEd/backend/Procfile`:

```
web: cd AdaptEd/backend && uvicorn app:app --host 0.0.0.0 --port $PORT
```

Или если Root Directory уже установлен в `AdaptEd/backend`:

```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Вариант 3: Используйте python -m

Обновите `railway.json`:

```json
{
  "deploy": {
    "startCommand": "python -m uvicorn app:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Вариант 4: Явно укажите PYTHONPATH

В Railway Dashboard → Variables добавьте:

```
PYTHONPATH=/app/AdaptEd/backend
```

Или в railway.json:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "PYTHONPATH=/app/AdaptEd/backend uvicorn app:app --host 0.0.0.0 --port $PORT"
  }
}
```

## 🎯 Рекомендуемое решение

1. **Установите Root Directory** в Railway Dashboard:
   - Settings → Source → Root Directory: `AdaptEd/backend`

2. **Убедитесь, что Procfile правильный**:
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

3. **Перезапустите деплой**

## 🔍 Проверка

После исправления проверьте логи:
- Railway Dashboard → Ваш сервис → Deployments → View Logs
- Должно быть: `Application startup complete` вместо ошибок импорта

