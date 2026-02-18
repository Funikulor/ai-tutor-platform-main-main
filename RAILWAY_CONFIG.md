# 🚀 Railway Config-as-Code

## ✅ Что это?

Railway поддерживает конфигурацию через файлы `railway.json` в каждой папке сервиса. Это проще, чем настраивать через интерфейс!

## 📁 Структура файлов

Созданы конфигурационные файлы:

1. **`AdaptEd/backend/railway.json`** - для backend (FastAPI)
2. **`AdaptEd/frontend/railway.json`** - для frontend (React/Vite)

## 📋 Как использовать:

### Вариант 1: Два отдельных сервиса (Рекомендуется)

#### Backend сервис:

1. **Railway Dashboard** → New Project → Deploy from GitHub
2. **Выберите репозиторий**
3. **Railway автоматически найдет** `AdaptEd/backend/railway.json`
4. **Root Directory автоматически установится** в `AdaptEd/backend`
5. **Добавьте переменные окружения**:
   ```
   DATABASE_URL=postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
   OPENAI_API_KEY=ваш_ключ_openai
   ASSISTANT_PROVIDER=openai
   OPENAI_MODEL=gpt-4o-mini
   PYTHON_VERSION=3.11
   ```

#### Frontend сервис:

1. **В том же проекте** → + New → GitHub Repo
2. **Выберите тот же репозиторий**
3. **Railway автоматически найдет** `AdaptEd/frontend/railway.json`
4. **Root Directory автоматически установится** в `AdaptEd/frontend`
5. **Добавьте переменные окружения**:
   ```
   VITE_API_URL=https://ваш-backend-url.up.railway.app
   NODE_VERSION=20
   ```

### Вариант 2: Через Railway CLI

```bash
# Установите Railway CLI
npm i -g @railway/cli

# Войдите
railway login

# Backend
cd AdaptEd/backend
railway init
railway up

# Frontend (в другом терминале)
cd AdaptEd/frontend
railway init
railway up
```

## 📝 Что в конфигурации:

### Backend (`AdaptEd/backend/railway.json`):

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn app:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Frontend (`AdaptEd/frontend/railway.json`):

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm install && npm run build"
  },
  "deploy": {
    "staticAssetsPath": "build",
    "staticServeCommand": "npx serve -s build -l $PORT"
  }
}
```

## ✅ Преимущества Config-as-Code:

1. **Автоматическое определение Root Directory** - Railway сам найдет правильную папку
2. **Версионирование конфигурации** - все настройки в Git
3. **Проще управлять** - не нужно настраивать через интерфейс
4. **Автоматический деплой** - при `git push` Railway использует конфигурацию из файла

## 🔍 Как Railway определяет Root Directory:

Railway ищет `railway.json` в следующих местах:
1. В корне репозитория
2. В подпапках проекта

Если находит `railway.json` в `AdaptEd/backend/`, то автоматически устанавливает Root Directory = `AdaptEd/backend`

## 🆘 Если Root Directory не установился автоматически:

1. **В Railway Dashboard** → Ваш сервис → Settings
2. **Найдите "Root Directory"** или "Source" раздел
3. **Вручную укажите**: `AdaptEd/backend` или `AdaptEd/frontend`

Но с `railway.json` это должно работать автоматически!

## 📚 Дополнительные настройки:

Если нужно больше настроек, можно добавить в `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "...",
    "watchPatterns": ["**/*.py"]
  },
  "deploy": {
    "startCommand": "...",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

