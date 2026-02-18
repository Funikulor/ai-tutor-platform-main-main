# 🚨 Быстрое исправление 502 Bad Gateway

## Проблема: Backend не запущен (502 Bad Gateway)

**НЕ убирайте `https://`!** Это правильно. Проблема в том, что backend не запускается на Railway.

## ✅ Что сделать СЕЙЧАС:

### 1. Проверьте логи Backend

**Railway Dashboard** → Backend Service → **Deployments** → последний деплой → **View Logs**

**Что искать:**
- ❌ `Error loading ASGI app` → неправильный Root Directory
- ❌ `Connection refused` → проблема с DATABASE_URL
- ❌ `ModuleNotFoundError` → отсутствуют зависимости
- ✅ `Uvicorn running on http://0.0.0.0:XXXX` → backend запущен

### 2. Проверьте Root Directory

**Railway Dashboard** → Backend Service → **Settings** → **Root Directory**

**Должно быть:** `AdaptEd/backend`

Если пусто или неправильно:
1. Установите `AdaptEd/backend`
2. **Сохраните**
3. **Redeploy** backend

### 3. Проверьте переменные

**Railway Dashboard** → Backend Service → **Variables**

**Обязательно должны быть:**
- `DATABASE_URL` (должен начинаться с `postgresql://`)
- `OPENAI_API_KEY` (если используете)
- `ASSISTANT_PROVIDER` (обычно `openai`)

### 4. Пересоберите Backend

**Railway Dashboard** → Backend Service → **Deployments** → **Redeploy**

Дождитесь завершения и проверьте логи.

### 5. Проверьте доступность

**Railway Dashboard** → Backend Service → **Settings** → **Networking** → **Public Domain**

Откройте этот URL в браузере.

**Должно появиться:**
```json
{"message": "Welcome to the AdaptEd API!"}
```

## ✅ После исправления:

- Backend будет **Active**
- URL backend откроется в браузере
- CORS ошибка исчезнет
- Frontend подключится к backend

## ⚠️ Важно:

**`https://` в `VITE_API_URL` правильный!** Не убирайте его. Проблема в том, что backend не запущен, а не в URL.

