# 🔍 Диагностика Backend на Railway

## Проблема: "Бэкенд не доступен"

Если вы видите сообщение "Бэкенд не доступен", выполните следующие шаги:

## ✅ Шаг 1: Проверьте, что Backend запущен на Railway

1. **Railway Dashboard** → Backend Service
2. Проверьте статус:
   - ✅ **Active** - backend запущен
   - ❌ **Inactive** или **Error** - backend не запущен

3. Если backend не запущен:
   - Проверьте логи (Railway Dashboard → Backend Service → Deployments → View Logs)
   - Убедитесь, что `DATABASE_URL` установлен
   - Убедитесь, что `Root Directory` = `AdaptEd/backend`

## ✅ Шаг 2: Проверьте URL Backend

1. **Railway Dashboard** → Backend Service → Settings → Networking
2. Найдите **Public Domain** (например: `https://xxx.up.railway.app`)
3. Откройте этот URL в браузере
4. Должно появиться:
   ```json
   {"message": "Welcome to the AdaptEd API!"}
   ```

Если не появляется - backend не работает.

## ✅ Шаг 3: Проверьте VITE_API_URL в Frontend

1. **Railway Dashboard** → Frontend Service → Variables
2. Найдите `VITE_API_URL`
3. Убедитесь, что значение:
   - ✅ Начинается с `https://`
   - ✅ Без `/api` в конце
   - ✅ Без `/` в конце
   - ✅ Совпадает с Public Domain из шага 2

**Пример правильного значения:**
```
https://ai-tutor-platform-main-main-production.up.railway.app
```

## ✅ Шаг 4: Проверьте в консоли браузера

1. Откройте сайт
2. **F12** → **Console**
3. Найдите логи:
   ```
   Backend check failed: {
     error: "...",
     code: "...",
     baseURL: "...",
     fullURL: "..."
   }
   ```

4. Проверьте `fullURL` - он должен быть:
   ```
   https://ваш-backend-url.up.railway.app/
   ```

## ✅ Шаг 5: Пересоберите Frontend

После изменения `VITE_API_URL`:

1. **Railway Dashboard** → Frontend Service → Deployments
2. Нажмите **Redeploy**
3. Дождитесь завершения деплоя
4. Обновите страницу (Ctrl+F5)

## 🔧 Частые проблемы:

### Проблема 1: Backend не запускается

**Причина:** Неправильный `Root Directory` или отсутствует `DATABASE_URL`

**Решение:**
1. Railway Dashboard → Backend Service → Settings
2. Установите **Root Directory** = `AdaptEd/backend`
3. Проверьте, что `DATABASE_URL` установлен в Variables
4. Пересоберите backend (Redeploy)

### Проблема 2: CORS ошибка

**Причина:** Backend не разрешает запросы с frontend домена

**Решение:**
- Проверьте `app.py` - должен быть настроен CORS для всех источников:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # В production лучше указать конкретные домены
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### Проблема 3: Timeout

**Причина:** Backend слишком долго отвечает (холодный старт Railway или Neon)

**Решение:**
- Подождите 10-15 секунд и попробуйте снова
- Backend автоматически попробует еще раз через 3 секунды

## 📝 Проверка через curl (опционально)

Если у вас установлен curl, можете проверить backend напрямую:

```bash
curl https://ваш-backend-url.up.railway.app/
```

Должен вернуться:
```json
{"message": "Welcome to the AdaptEd API!"}
```

## ✅ После исправления:

1. Backend должен быть **Active** на Railway
2. URL backend должен открываться в браузере
3. `VITE_API_URL` должен быть правильным
4. Frontend должен быть пересобран
5. В консоли браузера должен быть правильный `fullURL`

После этого сообщение "Бэкенд не доступен" должно исчезнуть, и появится "Бэкенд доступен и готов к работе".

