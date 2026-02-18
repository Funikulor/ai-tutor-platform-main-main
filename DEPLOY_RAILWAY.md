# 🚀 Деплой Backend и Frontend на Railway

## ✅ Railway поддерживает оба сервиса!

Railway может задеплоить:
- **Backend** (FastAPI/Python) - как Web Service
- **Frontend** (React/Vite) - как Static Site или Web Service

## 📋 Шаг 1: Подготовка репозитория

### Backend (FastAPI)

1. **Procfile** уже создан в `AdaptEd/backend/Procfile`:
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

2. **requirements.txt** уже есть в `AdaptEd/backend/requirements.txt`

### Frontend (React/Vite)

1. **package.json** уже есть в `AdaptEd/frontend/package.json`
2. **build script** уже настроен: `npm run build`

## 📋 Шаг 2: Деплой на Railway

### Вариант 1: Через Railway Dashboard (Рекомендуется)

1. **Войдите на Railway**: https://railway.app

2. **Создайте новый проект**:
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите ваш репозиторий

3. **Добавьте Backend сервис**:
   - Нажмите "+ New" → "GitHub Repo"
   - Выберите ваш репозиторий
   - Railway автоматически определит Python проект
   - **Важно**: В настройках сервиса укажите:
     - **Root Directory**: `AdaptEd/backend`
     - Railway автоматически найдет `Procfile` и `requirements.txt`

4. **Добавьте Frontend сервис**:
   - Нажмите "+ New" → "GitHub Repo"
   - Выберите тот же репозиторий
   - Railway автоматически определит Node.js проект
   - **Важно**: В настройках сервиса укажите:
     - **Root Directory**: `AdaptEd/frontend`
     - **Build Command**: `npm install && npm run build`
     - **Start Command**: (оставьте пустым для static site)
     - Или используйте **Static Files**:
       - **Output Directory**: `build`

### Вариант 2: Через Railway CLI

```bash
# Установите Railway CLI
npm i -g @railway/cli

# Войдите
railway login

# Создайте проект
railway init

# Деплой backend
cd AdaptEd/backend
railway up

# Деплой frontend (в другом терминале)
cd AdaptEd/frontend
railway up
```

## 📋 Шаг 3: Настройка переменных окружения

### Для Backend:

В Railway Dashboard → Backend Service → Variables:

```
DATABASE_URL=postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
OPENAI_API_KEY=ваш_ключ_openai
ASSISTANT_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
PYTHON_VERSION=3.11
```

### Для Frontend:

В Railway Dashboard → Frontend Service → Variables:

```
VITE_API_URL=https://ваш-backend-url.railway.app
NODE_VERSION=20
```

**Важно**: Замените `https://ваш-backend-url.railway.app` на реальный URL backend после деплоя.

## 📋 Шаг 4: Настройка доменов

1. **Backend**: Railway автоматически создаст URL вида `https://ваш-проект-production.up.railway.app`
2. **Frontend**: Railway автоматически создаст URL вида `https://ваш-проект-production.up.railway.app`

3. **Настройте кастомные домены** (опционально):
   - В настройках каждого сервиса → Settings → Domains
   - Добавьте свой домен

## 📋 Шаг 5: Настройка Frontend как Static Site

Если Railway определил frontend как Web Service, но вы хотите Static Site:

1. В настройках Frontend сервиса:
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: (оставьте пустым)
   - **Output Directory**: `build`

Или используйте **Static Files** опцию:
- Railway → Frontend Service → Settings → Static Files
- **Output Directory**: `build`

## ✅ Проверка работы

1. **Backend**: Откройте URL backend
   - Должно вернуться: `{"message": "Welcome to the AdaptEd API!"}`

2. **Frontend**: Откройте URL frontend
   - Должен загрузиться интерфейс приложения

## 🔄 Автоматический деплой

Railway автоматически деплоит при каждом `git push` в основную ветку, если:
- Репозиторий подключен
- Автодеплой включен (по умолчанию включен)

## 🆘 Решение проблем

### Backend не запускается:

1. Проверьте логи: Railway Dashboard → Backend Service → Deployments → View Logs
2. Убедитесь, что `Root Directory` = `AdaptEd/backend`
3. Проверьте, что все переменные окружения установлены
4. Убедитесь, что `Procfile` существует в `AdaptEd/backend/`

### Frontend не собирается:

1. Проверьте логи: Railway Dashboard → Frontend Service → Deployments → View Logs
2. Убедитесь, что `Root Directory` = `AdaptEd/frontend`
3. Проверьте, что `NODE_VERSION=20` установлен
4. Убедитесь, что `VITE_API_URL` указывает на правильный backend URL

### CORS ошибки:

Убедитесь, что в `AdaptEd/backend/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретный URL frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend не подключается к Backend:

1. Проверьте `VITE_API_URL` в переменных окружения frontend
2. Убедитесь, что backend URL правильный (без `/api` в конце, если не нужно)
3. Проверьте, что backend работает: откройте URL backend в браузере

## 💡 Советы

1. **Используйте Railway Variables** для секретных данных (API ключи, пароли)
2. **Настройте Health Checks** для автоматического перезапуска при сбоях
3. **Используйте Railway Insights** для мониторинга использования ресурсов
4. **Настройте уведомления** о деплоях и ошибках

## 💰 Лимиты Railway

Railway предоставляет:
- **$5 бесплатного кредита** в месяц
- После исчерпания кредита сервисы останавливаются
- Можно добавить кредитную карту для продолжения работы

