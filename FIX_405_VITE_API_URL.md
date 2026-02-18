# 🔧 Исправление ошибки 405: VITE_API_URL не установлен

## ❌ Проблема:

Запрос идет на URL frontend (`/ai-tutor-platform-m…ay.app/auth/login`) вместо backend. Это означает, что `VITE_API_URL` не установлен или не используется.

## ✅ Решение:

### Шаг 1: Установите VITE_API_URL в Railway

1. **Railway Dashboard** → Frontend Service → Variables
2. **Добавьте переменную:**
   ```
   VITE_API_URL=https://ваш-backend-url.up.railway.app
   ```
3. **Важно:**
   - Замените `https://ваш-backend-url.up.railway.app` на реальный URL вашего backend
   - Без `/api` в конце
   - Без `/` в конце
   - С `https://` в начале

### Шаг 2: Найдите URL Backend

1. **Railway Dashboard** → Backend Service → Settings → Networking
2. **Скопируйте Public Domain** (URL вида `https://xxx.up.railway.app`)
3. **Используйте этот URL** в `VITE_API_URL`

### Шаг 3: Пересоберите Frontend

После установки `VITE_API_URL`:

1. **Railway Dashboard** → Frontend Service → Deployments
2. **Нажмите "Redeploy"** или подождите автоматического деплоя
3. **Важно:** Frontend нужно пересобрать, чтобы переменная `VITE_API_URL` попала в код!

### Шаг 4: Проверьте

После пересборки:

1. Откройте сайт
2. **F12** → **Console**
3. Попробуйте войти
4. В консоли должно быть:
   ```
   API Request: {
     method: "POST",
     url: "https://ваш-backend-url.up.railway.app/auth/login",
     baseURL: "https://ваш-backend-url.up.railway.app"
   }
   ```

Если URL правильный - запрос должен работать!

## ⚠️ Важно:

**VITE_API_URL должен быть установлен ДО сборки frontend!**

Если вы установили переменную после сборки:
1. Railway Dashboard → Frontend Service → Deployments → Redeploy
2. Или сделайте `git push` - Railway пересоберет автоматически

## 🔍 Проверка:

После установки `VITE_API_URL` и пересборки, проверьте в консоли браузера:
- Должен использоваться правильный backend URL
- Не должен использоваться URL frontend

