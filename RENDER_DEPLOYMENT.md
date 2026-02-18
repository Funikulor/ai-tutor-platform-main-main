# 🚀 Деплой на Render.com

## 📋 Что такое render.yaml?

`render.yaml` - это Blueprint файл для автоматической настройки сервисов на Render. Он позволяет настроить весь проект одной командой.

---

## 🎯 Быстрый старт

### Шаг 1: Подготовка файла

Файл `render.yaml` уже создан в корне проекта. Он настроен для:
- **Backend** (FastAPI) - автоматический деплой
- **Frontend** (React) - опционально

### Шаг 2: Подключение к Render

1. **Создайте аккаунт** на https://render.com
2. **Подключите GitHub репозиторий**:
   - Dashboard → New → Blueprint
   - Выберите ваш репозиторий
   - Render автоматически найдет `render.yaml`

### Шаг 3: Настройка переменных окружения

После создания сервисов, в панели Render установите:

**Для Backend:**
- `DATABASE_URL` - URL вашей базы данных (PostgreSQL)
- `OPENAI_API_KEY` - ваш ключ OpenAI

**Для Frontend (если деплоите):**
- `VITE_API_URL` - URL вашего backend (например: `https://adapted-backend.onrender.com/api`)

### Шаг 4: Деплой

Render автоматически:
1. Найдет `render.yaml`
2. Создаст сервисы согласно конфигурации
3. Задеплоит проект

---

## 📝 Структура render.yaml

### Backend сервис

```yaml
services:
  - type: web
    name: adapted-backend
    env: python
    buildCommand: pip install -r AdaptEd/backend/requirements.txt
    startCommand: cd AdaptEd/backend && uvicorn app:app --host 0.0.0.0 --port $PORT
    rootDir: AdaptEd/backend
```

**Важно:**
- `rootDir` указывает на папку с backend
- `startCommand` запускает uvicorn на порту `$PORT` (Render автоматически устанавливает)

### Frontend сервис (опционально)

```yaml
  - type: web
    name: adapted-frontend
    env: static
    buildCommand: cd AdaptEd/frontend && npm install && npm run build
    staticPublishPath: AdaptEd/frontend/build
```

---

## 🔧 Настройка переменных окружения

### В render.yaml (автоматически):

```yaml
envVars:
  - key: OPENAI_MODEL
    value: gpt-4o-mini
```

### В панели Render (вручную):

Переменные с `sync: false` нужно установить вручную:
- `DATABASE_URL`
- `OPENAI_API_KEY`

**Как установить:**
1. Откройте ваш сервис в Render Dashboard
2. Перейдите в раздел "Environment"
3. Добавьте переменные

---

## 🗄️ База данных (опционально)

Если хотите использовать PostgreSQL на Render, раскомментируйте в `render.yaml`:

```yaml
databases:
  - name: adapted-db
    databaseName: adapted_db
    user: adapted_user
    plan: free
```

После создания базы, Render автоматически создаст переменную `DATABASE_URL`.

---

## 📍 Регионы

В `render.yaml` указан регион `frankfurt`. Вы можете изменить на:
- `oregon` - США (Запад)
- `ohio` - США (Восток)
- `frankfurt` - Европа
- `singapore` - Азия

---

## ✅ Проверка работы

После деплоя:

1. **Backend**: Откройте `https://adapted-backend.onrender.com/`
   - Должно вернуться: `{"message": "Welcome to the AdaptEd API!"}`

2. **Frontend** (если деплоите): Откройте `https://adapted-frontend.onrender.com`
   - Должен загрузиться интерфейс

---

## 🔄 Обновление

Render автоматически обновляет сервисы при пуше в репозиторий, если:
- Репозиторий подключен
- Автодеплой включен (по умолчанию включен)

---

## 🆘 Решение проблем

### Backend не запускается

1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что `requirements.txt` содержит все зависимости

### Frontend не собирается

1. Проверьте, что `package.json` существует
2. Убедитесь, что Node.js версия совместима
3. Проверьте логи сборки

### CORS ошибки

Убедитесь, что в `AdaptEd/backend/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретный URL frontend
    ...
)
```

---

## 📝 Важные замечания

1. **Бесплатный план**: Сервисы "засыпают" после 15 минут неактивности
2. **Переменные окружения**: Секретные ключи храните только в Environment Variables
3. **База данных**: На бесплатном плане есть ограничения по размеру

---

## 🎯 Рекомендация

Для production лучше использовать:
- **Backend** → Render (или Railway)
- **Frontend** → Netlify или Beget (быстрее и проще для статики)

Но если хотите все на Render - это тоже работает!

---

## 📞 Дополнительная информация

- **Документация Render**: https://render.com/docs
- **Blueprint Reference**: https://render.com/docs/blueprint-spec

