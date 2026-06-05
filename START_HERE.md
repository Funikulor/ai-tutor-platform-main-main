# Как запустить AdaptEd

## 🚀 Быстрый запуск

### Запуск через командную строку

**Терминал 1 (Backend):**
```bash
cd AdaptEd\backend
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Терминал 2 (Frontend):**
```bash
cd AdaptEd\frontend
npm install
npm run dev
```

## 📋 После запуска

1. Backend будет доступен на: http://localhost:8000
2. Frontend откроется автоматически в браузере на: http://localhost:5173
3. API документация доступна на: http://localhost:8000/docs
4. Войдите в систему или зарегистрируйтесь для начала работы

## 🔧 Если что-то не работает

### Backend не запускается
- Убедитесь, что порт 8000 свободен
- Проверьте, что установлены все зависимости: `pip install -r AdaptEd/backend/requirements.txt`
- Проверьте наличие файла `.env` в папке `AdaptEd/backend/` с необходимыми переменными окружения

### Переменные окружения (важно)
| Переменная | Назначение |
|------------|------------|
| `DATABASE_URL` | PostgreSQL на Railway; если не задана — локально создаётся SQLite `adapted.db` |
| `AUTH_SECRET_KEY` или `SECRET_KEY` | Подпись JWT-подобных токенов (**обязательно смените в проде**) |
| `OPENAI_API_KEY` / `PROXYAPI_KEY` | Для AI-чата и генерации (см. `ASSISTANT_PROVIDER`) |
| `DEBUG` | Если `1` или `true` — доступны `/debug` и `/batcher-stats` (в проде обычно не задают) |
| `CORS_ORIGINS` | Дополнительные origin для CORS через запятую |
| `VITE_API_URL` | Только для **сборки фронта** на Railway: полный URL бэкенда, например `https://ваш-backend.up.railway.app` (**без** слэша в конце). Задаётся в **Variables сервиса frontend**; после изменения нужен **новый деплой** (пересборка `npm run build`). |

### Railway: «Backend API недоступен»
1. В **отдельном сервисе backend** в Railway должны быть `DATABASE_URL`, `AUTH_SECRET_KEY` (или `SECRET_KEY`), при необходимости ключи ИИ. Убедитесь, что сервис **Running** и в **Settings → Networking** есть публичный URL.
2. В **сервисе frontend** в Variables задайте **`VITE_API_URL`** = тот же публичный URL бэкенда с `https://`. Без этой переменной в production `baseURL` у axios пустой, запросы уходят не туда.
3. После добавления или смены `VITE_API_URL` сделайте **Redeploy** фронта (пересборка), иначе в бандле останется старое значение.
4. CORS: для доменов `*.up.railway.app` бэкенд разрешает origin по шаблону; для другого хоста добавьте его в `CORS_ORIGINS` на бэкенде.

### Сброс учеников/учителей и повторный сид (Postgres / Railway)
Из папки `AdaptEd/backend` при корректном `DATABASE_URL` в `.env`:
```bash
python -m scripts.seed_from_credentials --reset
```
Сначала удаляются все пользователи с ролями **student** и **teacher**, затем создаются заново из `seed_credentials.txt`. Администраторов не трогает.

### Миграции схемы БД
Сейчас таблицы создаются через `Base.metadata.create_all()` при старте. Для эволюции схемы в проде рекомендуется подключить **Alembic** (`pip install alembic`, `alembic init`) и хранить ревизии в репозитории — отдельный шаг после стабилизации моделей.

### Frontend не запускается
- Убедитесь, что Backend запущен на порту 8000
- Проверьте, что установлен Node.js (версия 16 или выше)
- Проверьте, что установлены все зависимости: `npm install`
- Убедитесь, что переменная `VITE_API_URL` в `.env` указывает на правильный адрес backend

## 📚 Дополнительная информация

- API документация: http://localhost:8000/docs
- Руководство по проекту: `AdaptEd/README.md`
- Диагностика и решение проблем: `TROUBLESHOOTING.md`
