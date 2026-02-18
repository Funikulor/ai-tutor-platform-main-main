# 🚀 Деплой Backend на Render

## Проблема с Netlify

Netlify приостановил сайт из-за превышения лимитов бесплатного плана. Это произошло из-за Netlify Functions (backend), которые потребляют много ресурсов.

## ✅ Решение: Backend на Render, Frontend на Netlify

### Шаг 1: Деплой Backend на Render

1. **Создайте аккаунт** на https://render.com (можно через GitHub)

2. **Подключите репозиторий**:
   - Dashboard → New → Blueprint
   - Выберите ваш GitHub репозиторий
   - Render автоматически найдет `render.yaml`

3. **Настройте переменные окружения** в Render Dashboard:
   - Откройте созданный сервис `adapted-backend`
   - Environment → Add Environment Variable
   - Добавьте:
     ```
     DATABASE_URL=postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
     OPENAI_API_KEY=ваш_ключ_openai
     ```

4. **Дождитесь деплоя** (обычно 5-10 минут)

5. **Проверьте работу**:
   - Откройте `https://adapted-backend.onrender.com/`
   - Должно вернуться: `{"message": "Welcome to the AdaptEd API!"}`

### Шаг 2: Обновите Frontend на Netlify

1. **В Netlify Dashboard**:
   - Site settings → Environment variables
   - Добавьте/обновите:
     ```
     VITE_API_URL=https://adapted-backend.onrender.com
     ```

2. **Удалите Netlify Functions** (они больше не нужны):
   - Можно оставить файлы, но они не будут использоваться
   - Netlify больше не будет их обрабатывать

3. **Перезапустите деплой**:
   - Deploys → Trigger deploy → Deploy site

### Шаг 3: Проверка работы

1. **Frontend**: `https://web-tutor-ai.netlify.app`
2. **Backend**: `https://adapted-backend.onrender.com/`

## ⚠️ Важные замечания

### Render Free Plan:
- Сервисы "засыпают" после 15 минут неактивности
- Первый запрос после "сна" может занять 30-60 секунд
- Это нормально для бесплатного плана

### Если нужно избежать "сна":
- Используйте сервисы типа UptimeRobot для периодических запросов
- Или обновитесь на платный план Render ($7/месяц)

## 🔄 Обновление кода

После изменений в коде:
- **Backend**: Render автоматически перезапустит при `git push`
- **Frontend**: Netlify автоматически пересоберет при `git push`

## 🆘 Решение проблем

### Backend не запускается:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что `DATABASE_URL` и `OPENAI_API_KEY` установлены
3. Проверьте, что все зависимости в `requirements.txt`

### Frontend не подключается к Backend:
1. Проверьте `VITE_API_URL` в Netlify
2. Убедитесь, что backend работает: `https://adapted-backend.onrender.com/`
3. Проверьте CORS настройки в `AdaptEd/backend/app.py`

### CORS ошибки:
Убедитесь, что в `AdaptEd/backend/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретный URL frontend
    ...
)
```

