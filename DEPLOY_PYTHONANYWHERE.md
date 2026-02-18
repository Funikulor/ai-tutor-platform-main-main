# 🚀 Деплой Backend на PythonAnywhere (БЕСПЛАТНО)

## ✅ Почему PythonAnywhere?

- **Полностью бесплатный**: для начинающих проектов
- **Специализирован на Python**: отлично подходит для FastAPI
- **Простой деплой**: через веб-интерфейс
- **Не засыпает**: сервисы работают постоянно

## 📋 Шаг 1: Регистрация

1. Перейдите на https://www.pythonanywhere.com
2. Зарегистрируйтесь (можно через GitHub)
3. Выберите **Beginner** план (бесплатный)

## 📋 Шаг 2: Подготовка кода

1. **Откройте Bash консоль** в PythonAnywhere Dashboard

2. **Клонируйте репозиторий**:
   ```bash
   cd ~
   git clone https://github.com/ваш-username/ваш-репозиторий.git
   cd ваш-репозиторий/AdaptEd/backend
   ```

3. **Установите зависимости**:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

## 📋 Шаг 3: Настройка переменных окружения

Создайте файл `.env`:
```bash
nano ~/ваш-репозиторий/AdaptEd/backend/.env
```

Добавьте:
```
DATABASE_URL=postgresql://neondb_owner:npg_X5QkZKm2DYGx@ep-damp-hill-aexgnowu-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require
OPENAI_API_KEY=ваш_ключ_openai
ASSISTANT_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
```

## 📋 Шаг 4: Настройка Web App

1. **В Dashboard** → **Web** → **Add a new web app**

2. **Выберите**:
   - Python version: **Python 3.10**
   - Framework: **Manual configuration**

3. **Настройте WSGI файл**:
   - Откройте `/var/www/ваш-username_pythonanywhere_com_wsgi.py`
   - Замените содержимое на:
   ```python
   import sys
   import os
   
   # Добавляем путь к проекту
   path = '/home/ваш-username/ваш-репозиторий/AdaptEd/backend'
   if path not in sys.path:
       sys.path.insert(0, path)
   
   os.chdir(path)
   
   # Импортируем приложение
   from app import app
   
   application = app
   ```

4. **Настройте Static files** (если нужно):
   - URL: `/static/`
   - Directory: `/home/ваш-username/ваш-репозиторий/AdaptEd/backend/static`

## 📋 Шаг 5: Запуск

1. **В Dashboard** → **Web** → нажмите **Reload**

2. **Проверьте URL**: `https://ваш-username.pythonanywhere.com/`

## ⚠️ Ограничения бесплатного плана

- **1 веб-приложение**
- **512MB дискового пространства**
- **Ограниченный CPU** (может быть медленнее при нагрузке)
- **Только HTTP** (не HTTPS на бесплатном плане)

## 🔧 Альтернатива: Использование uvicorn через Tasks

Если Web App не работает, можно использовать Tasks:

1. **Dashboard** → **Tasks** → **Create a new task**

2. **Команда**:
   ```bash
   cd ~/ваш-репозиторий/AdaptEd/backend && uvicorn app:app --host 0.0.0.0 --port 8080
   ```

3. **Но это не даст вам публичный URL** - только для тестирования

## 🆘 Решение проблем

### Ошибка импорта:
- Убедитесь, что все зависимости установлены: `pip3.10 install --user -r requirements.txt`
- Проверьте пути в WSGI файле

### База данных не подключается:
- Проверьте, что `DATABASE_URL` правильный
- Убедитесь, что Neon разрешает подключения с IP PythonAnywhere

### CORS ошибки:
Убедитесь, что в `AdaptEd/backend/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

