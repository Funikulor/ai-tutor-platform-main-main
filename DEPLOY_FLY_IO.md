# 🚀 Деплой Backend на Fly.io (БЕСПЛАТНО)

## ✅ Почему Fly.io?

- **Бесплатный tier**: 3 shared-cpu-1x VM бесплатно
- **Не засыпает**: в отличие от Render, сервисы не "засыпают"
- **Быстрый старт**: деплой за 2-3 минуты
- **Хорошая документация**: отличная поддержка Python/FastAPI

## 📋 Шаг 1: Установка Fly CLI

### Windows:
```powershell
# Скачайте и установите с https://fly.io/docs/getting-started/installing-flyctl/
# Или через PowerShell:
iwr https://fly.io/install.ps1 -useb | iex
```

### Проверка установки:
```bash
flyctl version
```

## 📋 Шаг 2: Регистрация и вход

```bash
flyctl auth signup
# Или если уже есть аккаунт:
flyctl auth login
```

## 📋 Шаг 3: Деплой

1. **Перейдите в папку backend**:
   ```bash
   cd AdaptEd/backend
   ```

2. **Инициализируйте приложение**:
   ```bash
   flyctl launch
   ```
   
   Ответьте на вопросы:
   - App name: `adapted-backend` (или любое другое)
   - Region: выберите ближайший (например, `fra` для Frankfurt)
   - PostgreSQL: No (используем Neon)
   - Redis: No

3. **Настройте переменные окружения**:
   ```bash
   flyctl secrets set DATABASE_URL="postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"
   flyctl secrets set OPENAI_API_KEY="ваш_ключ_openai"
   flyctl secrets set ASSISTANT_PROVIDER="openai"
   flyctl secrets set OPENAI_MODEL="gpt-4o-mini"
   ```

4. **Деплой**:
   ```bash
   flyctl deploy
   ```

## 📋 Шаг 4: Проверка

После деплоя вы получите URL вида: `https://adapted-backend.fly.dev`

Проверьте:
```bash
curl https://adapted-backend.fly.dev/
# Должно вернуть: {"message": "Welcome to the AdaptEd API!"}
```

## 📋 Шаг 5: Обновите Frontend

В Netlify Dashboard → Environment variables:
```
VITE_API_URL=https://adapted-backend.fly.dev
```

## 🔧 Управление

### Просмотр логов:
```bash
flyctl logs
```

### Просмотр статуса:
```bash
flyctl status
```

### Перезапуск:
```bash
flyctl restart
```

### Просмотр переменных окружения:
```bash
flyctl secrets list
```

## 💰 Лимиты бесплатного плана

- **3 shared-cpu-1x VM** бесплатно
- **160GB outbound data transfer** в месяц
- **3GB persistent volume storage** бесплатно

Этого достаточно для небольшого проекта!

## 🆘 Решение проблем

### Ошибка при деплое:
```bash
# Проверьте логи
flyctl logs

# Проверьте статус
flyctl status
```

### Backend не запускается:
1. Проверьте, что все переменные окружения установлены: `flyctl secrets list`
2. Проверьте логи: `flyctl logs`
3. Убедитесь, что `DATABASE_URL` правильный

### CORS ошибки:
Убедитесь, что в `AdaptEd/backend/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретный URL frontend
    ...
)
```

