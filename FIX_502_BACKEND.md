# 🔧 Исправление 502 Bad Gateway на Railway Backend

## ❌ Проблема:

```
502 Bad Gateway
CORS: No 'Access-Control-Allow-Origin' header
```

**Это означает:** Backend не запущен или падает при старте.

## ✅ Решение:

### Шаг 1: Проверьте логи Backend на Railway

1. **Railway Dashboard** → Backend Service → **Deployments**
2. Нажмите на последний деплой → **View Logs**
3. Найдите ошибки (обычно красным цветом)

**Частые ошибки:**
- `Error loading ASGI app` → неправильный Root Directory
- `Connection refused` → проблема с DATABASE_URL
- `ModuleNotFoundError` → отсутствуют зависимости

### Шаг 2: Проверьте Root Directory

1. **Railway Dashboard** → Backend Service → **Settings**
2. Найдите **Root Directory**
3. Должно быть: `AdaptEd/backend`
4. Если пусто или неправильно → установите `AdaptEd/backend`
5. **Сохраните** и **Redeploy**

### Шаг 3: Проверьте переменные окружения

**Railway Dashboard** → Backend Service → **Variables**

**Обязательные переменные:**
- ✅ `DATABASE_URL` - должен быть установлен
- ✅ `OPENAI_API_KEY` - если используете OpenAI
- ✅ `ASSISTANT_PROVIDER` - обычно `openai`
- ✅ `OPENAI_MODEL` - например `gpt-4o-mini`

**Проверьте:**
- Все переменные установлены?
- `DATABASE_URL` правильный? (должен начинаться с `postgresql://`)

### Шаг 4: Проверьте, что backend запускается

В логах должно быть:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

Если этого нет → backend не запустился.

### Шаг 5: Проверьте Procfile и railway.json

**Файл:** `AdaptEd/backend/Procfile`
```
web: python -m uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Файл:** `AdaptEd/backend/railway.json`
```json
{
  "deploy": {
    "startCommand": "python -m uvicorn app:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Шаг 6: Пересоберите Backend

1. **Railway Dashboard** → Backend Service → **Deployments**
2. Нажмите **Redeploy**
3. Дождитесь завершения
4. Проверьте логи - должны быть сообщения об успешном запуске

### Шаг 7: Проверьте доступность Backend

1. **Railway Dashboard** → Backend Service → **Settings** → **Networking**
2. Скопируйте **Public Domain**
3. Откройте в браузере
4. Должно появиться:
   ```json
   {"message": "Welcome to the AdaptEd API!"}
   ```

Если не появляется → backend все еще не работает, проверьте логи снова.

## 🔍 Диагностика через терминал (опционально)

Если у вас установлен Railway CLI:

```bash
railway logs --service backend
```

## ✅ После исправления:

1. Backend должен быть **Active** на Railway
2. В логах должно быть "Uvicorn running"
3. URL backend должен открываться в браузере
4. CORS ошибка исчезнет (backend будет отвечать)
5. Frontend сможет подключиться к backend

## ⚠️ Важно:

**НЕ убирайте `https://` из `VITE_API_URL`!** Это правильно. Проблема в том, что backend не запущен (502), а не в URL.

После того как backend запустится, CORS ошибка исчезнет автоматически, так как CORS уже настроен в `app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

