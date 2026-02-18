# 🔌 Настройка порта для Railway Backend

## ✅ Что указать в поле "Enter the port your app is listening on":

### Для FastAPI/uvicorn:

**Укажите:** `8000` или оставьте пустым (Railway автоматически определит)

Railway автоматически устанавливает переменную `$PORT`, и ваш backend должен использовать её.

## 📋 Проверка конфигурации:

### 1. Проверьте Procfile:

В `AdaptEd/backend/Procfile` должно быть:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

### 2. Проверьте railway.json:

В `AdaptEd/backend/railway.json` должно быть:
```json
{
  "deploy": {
    "startCommand": "uvicorn app:app --host 0.0.0.0 --port $PORT"
  }
}
```

## 🎯 Что делать:

1. **В поле "Enter the port"**:
   - Оставьте **пустым** (Railway автоматически определит)
   - Или укажите **`8000`** (стандартный порт для uvicorn)

2. **Нажмите "Generate Service Domain"**

3. **Railway создаст URL** вида:
   ```
   https://ваш-проект-production.up.railway.app
   ```

4. **Скопируйте этот URL**

5. **Используйте его в Frontend**:
   - Railway Dashboard → Frontend Service → Variables
   - Добавьте: `VITE_API_URL=https://ваш-backend-url.up.railway.app`

## ⚠️ Важно:

- Railway автоматически устанавливает переменную `$PORT`
- Ваш backend должен использовать `$PORT` в команде запуска
- Если указать конкретный порт (например, 8000), Railway может не работать правильно
- **Лучше оставить пустым** - Railway сам определит порт

## 🔍 Если порт не работает:

1. Проверьте логи backend в Railway
2. Убедитесь, что в команде запуска используется `$PORT`
3. Проверьте, что backend слушает на `0.0.0.0`, а не `127.0.0.1`

