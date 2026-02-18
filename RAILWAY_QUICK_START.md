# 🚀 Быстрый старт: Деплой на Railway

## ✅ Что нужно сделать:

### 1. Backend на Railway

1. **Войдите на Railway**: https://railway.app
2. **Создайте новый проект** → "Deploy from GitHub repo"
3. **Выберите ваш репозиторий**
4. **Railway автоматически определит Python проект**
5. **В настройках сервиса**:
   - **Root Directory**: `AdaptEd/backend`
   - Railway автоматически найдет `Procfile` и `requirements.txt`
6. **Добавьте переменные окружения**:
   ```
   DATABASE_URL=postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
   OPENAI_API_KEY=ваш_ключ_openai
   ASSISTANT_PROVIDER=openai
   OPENAI_MODEL=gpt-4o-mini
   PYTHON_VERSION=3.11
   ```
7. **Скопируйте URL backend** (будет вида `https://xxx.up.railway.app`)

### 2. Frontend на Railway

1. **В том же проекте Railway** → "+ New" → "GitHub Repo"
2. **Выберите тот же репозиторий**
3. **Railway автоматически определит Node.js проект**
4. **В настройках сервиса**:
   - **Root Directory**: `AdaptEd/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Output Directory**: `build`
5. **Добавьте переменные окружения**:
   ```
   VITE_API_URL=https://ваш-backend-url.up.railway.app
   NODE_VERSION=20
   ```
   **Важно**: Замените `https://ваш-backend-url.up.railway.app` на реальный URL backend из шага 1.7

### 3. Готово! 🎉

Railway автоматически:
- Задеплоит оба сервиса
- Создаст публичные URL для каждого
- Настроит автоматический деплой при `git push`

## 📝 Файлы уже готовы:

- ✅ `AdaptEd/backend/Procfile` - для запуска backend
- ✅ `AdaptEd/backend/requirements.txt` - зависимости backend
- ✅ `AdaptEd/frontend/package.json` - зависимости frontend
- ✅ `AdaptEd/frontend/vite.config.ts` - конфигурация сборки

## 🔍 Проверка:

1. **Backend**: Откройте URL backend → должно вернуться `{"message": "Welcome to the AdaptEd API!"}`
2. **Frontend**: Откройте URL frontend → должен загрузиться интерфейс

## 🆘 Если что-то не работает:

Смотрите подробную инструкцию в `DEPLOY_RAILWAY.md`

