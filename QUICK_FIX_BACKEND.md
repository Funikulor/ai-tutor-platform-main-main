# 🚀 Быстрое исправление: "Бэкенд не доступен"

## ✅ Что нужно проверить:

### 1. Backend запущен на Railway?

**Railway Dashboard** → Backend Service → проверьте статус:
- ✅ **Active** = работает
- ❌ **Inactive/Error** = не работает

**Если не работает:**
- Проверьте логи (View Logs)
- Убедитесь, что `Root Directory` = `AdaptEd/backend`
- Убедитесь, что `DATABASE_URL` установлен

### 2. Backend доступен по URL?

**Railway Dashboard** → Backend Service → Settings → Networking → **Public Domain**

Откройте этот URL в браузере (например: `https://xxx.up.railway.app`)

**Должно появиться:**
```json
{"message": "Welcome to the AdaptEd API!"}
```

**Если не появляется** → backend не работает, проверьте логи.

### 3. VITE_API_URL правильный?

**Railway Dashboard** → Frontend Service → Variables → `VITE_API_URL`

**Должно быть:**
```
https://ваш-backend-url.up.railway.app
```

**Важно:**
- ✅ Начинается с `https://`
- ✅ Без `/api` в конце
- ✅ Без `/` в конце
- ✅ Совпадает с Public Domain из шага 2

### 4. Frontend пересобран?

После изменения `VITE_API_URL`:

**Railway Dashboard** → Frontend Service → Deployments → **Redeploy**

Дождитесь завершения и обновите страницу (Ctrl+F5).

### 5. Проверьте консоль браузера

**F12** → **Console** → найдите логи:

```
Checking backend at: https://...
✅ Backend is online: {...}
```

или

```
❌ Backend check failed: {
  fullURL: "https://...",
  error: "..."
}
```

## 🔧 Если все правильно, но не работает:

1. **Проверьте CORS** - должен быть настроен в `app.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       ...
   )
   ```

2. **Проверьте логи backend** на Railway - могут быть ошибки подключения к БД

3. **Подождите 10-15 секунд** - Railway может быть в режиме холодного старта

## ✅ После исправления:

Должно появиться: **"Бэкенд доступен и готов к работе"** ✅

