# 🔧 Переменные окружения для Railway

## 📋 Разделение переменных:

### 🔴 BACKEND Service (Railway Dashboard → Backend Service → Variables):

Эти переменные используются **только в backend** для работы AI и базы данных:

```
ASSISTANT_PROVIDER=proxyapi
PROXYAPI_KEY=ваш-api-ключ
PROXYAPI_URL=https://api.proxyapi.ru/openai/v1/chat/completions
PROXYAPI_MODEL=gpt-4o-mini

DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-... (если используете OpenAI как fallback)
OPENAI_MODEL=gpt-4o-mini (если используете OpenAI)
```

**Почему здесь:**
- `ASSISTANT_PROVIDER`, `PROXYAPI_KEY`, `PROXYAPI_URL`, `PROXYAPI_MODEL` - используются в `AdaptEd/backend/services/assistant.py` для генерации ответов
- `DATABASE_URL` - используется в `AdaptEd/backend/utils/db.py` для подключения к базе данных
- `OPENAI_API_KEY`, `OPENAI_MODEL` - используются как fallback, если PROXYAPI недоступен

### 🟢 FRONTEND Service (Railway Dashboard → Frontend Service → Variables):

Эти переменные используются **только во frontend** для подключения к backend:

```
VITE_API_URL=https://ваш-backend-url.up.railway.app
```

**Почему здесь:**
- `VITE_API_URL` - используется в `AdaptEd/frontend/src/services/api.ts` для отправки запросов к backend
- Префикс `VITE_` обязателен - Vite встраивает эти переменные в код при сборке
- Frontend должен знать URL backend, чтобы отправлять запросы

## ✅ Полная инструкция:

### 1. Backend Variables:

**Railway Dashboard** → **Backend Service** → **Variables** → **New Variable**

Добавьте все эти переменные:

| Переменная | Значение | Обязательно |
|-----------|----------|-------------|
| `ASSISTANT_PROVIDER` | `proxyapi` | ✅ Да |
| `PROXYAPI_KEY` | Ваш ключ PROXYAPI | ✅ Да |
| `PROXYAPI_URL` | `https://api.proxyapi.ru/openai/v1/chat/completions` | ⚠️ Проверьте в документации PROXYAPI |
| `PROXYAPI_MODEL` | `gpt-4o-mini` | ⚠️ Зависит от вашего тарифа |
| `DATABASE_URL` | `postgresql://...` | ✅ Да (из Railway Database) |
| `OPENAI_API_KEY` | `sk-...` | ❌ Нет (только если нужен fallback) |
| `OPENAI_MODEL` | `gpt-4o-mini` | ❌ Нет (только если используете OpenAI) |

### 2. Frontend Variables:

**Railway Dashboard** → **Frontend Service** → **Variables** → **New Variable**

Добавьте:

| Переменная | Значение | Обязательно |
|-----------|----------|-------------|
| `VITE_API_URL` | `https://ваш-backend-url.up.railway.app` | ✅ Да |

**Как найти URL Backend:**
1. Railway Dashboard → Backend Service → **Settings** → **Networking**
2. Скопируйте **Public Domain** (например: `https://xxx.up.railway.app`)
3. Используйте его как значение `VITE_API_URL`

**Важно:**
- URL должен начинаться с `https://`
- Без `/api` в конце
- Без `/` в конце

## 🔍 Проверка:

### Backend:
После установки переменных и пересборки, в логах backend должно быть:
```
[AssistantService] Провайдер: proxyapi
[AssistantService] PROXYAPI ключ: установлен
[App] DATABASE_URL: установлен
```

### Frontend:
После установки `VITE_API_URL` и пересборки frontend:
1. Откройте сайт
2. **F12** → **Console**
3. Попробуйте войти
4. В консоли должно быть:
```
API Request: {
  baseURL: "https://ваш-backend-url.up.railway.app",
  ...
}
```

## ⚠️ Важные моменты:

1. **Переменные с `VITE_`** идут только в **Frontend**
2. **Все остальные переменные** идут в **Backend**
3. **После изменения переменных** нужно **пересобрать** сервис (Redeploy)
4. **Frontend нужно пересобрать** после изменения `VITE_API_URL`, чтобы переменная попала в код

## 📝 Пример .env файла (для локальной разработки):

**AdaptEd/backend/.env:**
```env
ASSISTANT_PROVIDER=proxyapi
PROXYAPI_KEY=ваш-ключ
PROXYAPI_URL=https://api.proxyapi.ru/openai/v1/chat/completions
PROXYAPI_MODEL=gpt-4o-mini
DATABASE_URL=postgresql://...
```

**AdaptEd/frontend/.env:**
```env
VITE_API_URL=http://localhost:8000
```

**Важно:** `.env` файлы используются только для локальной разработки. На Railway используйте Variables в интерфейсе.

