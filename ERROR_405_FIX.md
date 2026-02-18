# 🔧 Исправление ошибки 405 (Method Not Allowed)

## ❌ Проблема:

При попытке входа получаете ошибку **405 Method Not Allowed**.

## 🔍 Возможные причины:

1. **Неправильный URL backend** - `VITE_API_URL` указывает на неправильный адрес
2. **Лишний слэш в URL** - запрос идет на `/auth/login/` вместо `/auth/login`
3. **Проблема с CORS preflight** - OPTIONS запрос не обрабатывается правильно
4. **Backend не запущен** или не отвечает на POST запросы

## ✅ Решение:

### Шаг 1: Проверьте VITE_API_URL

1. **Railway Dashboard** → Frontend Service → Variables
2. **Проверьте `VITE_API_URL`**:
   ```
   VITE_API_URL=https://ваш-backend-url.up.railway.app
   ```
3. **Важно:**
   - URL должен быть **без `/api`** в конце
   - URL должен начинаться с **`https://`**
   - URL должен быть правильным (скопируйте из Backend Service → Settings → Networking)

### Шаг 2: Проверьте работу Backend

Откройте в браузере:
```
https://ваш-backend-url.up.railway.app/
```

Должно вернуться:
```json
{"message": "Welcome to the AdaptEd API!"}
```

### Шаг 3: Проверьте endpoint напрямую

Попробуйте отправить POST запрос через curl или Postman:
```bash
curl -X POST https://ваш-backend-url.up.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"test"}'
```

Если это работает - проблема в frontend. Если нет - проблема в backend.

### Шаг 4: Проверьте консоль браузера

1. Откройте сайт
2. **F12** → **Console**
3. Попробуйте войти
4. Посмотрите, какой URL используется для запроса
5. Должно быть: `https://ваш-backend-url.up.railway.app/auth/login`

### Шаг 5: Проверьте Network tab

1. **F12** → **Network**
2. Попробуйте войти
3. Найдите запрос к `/auth/login`
4. Проверьте:
   - **Method**: должен быть **POST**
   - **URL**: должен быть правильным
   - **Status**: если 405 - проверьте URL и метод

## 🆘 Если ничего не помогает:

1. **Проверьте логи backend** в Railway:
   - Railway Dashboard → Backend Service → Deployments → View Logs
   - Должны быть запросы к `/auth/login`

2. **Проверьте, что backend запущен**:
   - Backend Service должен быть в статусе "Running"

3. **Попробуйте перезапустить backend**:
   - Railway Dashboard → Backend Service → Deployments → Redeploy

4. **Проверьте переменные окружения backend**:
   - `DATABASE_URL` установлен?
   - `OPENAI_API_KEY` установлен?

## 📝 Что было добавлено:

1. ✅ Обработка ошибки 405 в `Auth.tsx`
2. ✅ Детальное логирование в `api.ts` для отладки
3. ✅ Инструкция по диагностике

## 🔍 Диагностика:

После обновления кода, откройте консоль браузера (F12 → Console) и попробуйте войти. В консоли будет показано:
- Какой метод используется (POST)
- Какой URL используется
- Какой baseURL установлен

Это поможет понять, в чем проблема.

