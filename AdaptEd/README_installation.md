# AdaptEd - Инструкция по установке и запуску

## Требования

- Python 3.8 или выше
- pip (менеджер пакетов Python)

## Быстрая установка

### 1. Установка зависимостей

#### Backend (FastAPI)
```bash
cd AdaptEd/backend
pip install -r requirements.txt
```

#### Frontend (Streamlit)
```bash
cd AdaptEd/frontend
pip install -r requirements.txt
```

## Запуск приложения

### Вариант 1: Использование скриптов запуска

#### 1. Запуск Backend
Откройте первый терминал:
```bash
cd AdaptEd
python run_backend.py
```
Backend будет доступен на: http://localhost:8000

#### 2. Запуск Frontend
Откройте второй терминал:
```bash
cd AdaptEd
python run_frontend.py
```
Frontend будет доступен на: http://localhost:8501

### Вариант 2: Ручной запуск

#### Backend:
```bash
cd AdaptEd/backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend:
```bash
cd AdaptEd/frontend
streamlit run app.py
```

## Использование

1. Откройте браузер и перейдите на http://localhost:8501
2. Нажмите кнопку "Fetch Math Tasks" для загрузки задач
3. Введите ответы в поля ввода
4. Нажмите "Check Answer" для проверки ответа
5. Используйте секцию "User Management" для работы с пользователями

## API Endpoints

- `GET /tasks` - Получить список задач
- `POST /tasks/check?task_id={id}&user_answer={answer}` - Проверить ответ
- `GET /users/{user_id}` - Получить данные пользователя
- `POST /users/submit_answers` - Отправить ответы пользователя

Полная документация API доступна по адресу: http://localhost:8000/docs

## Устранение проблем

### Backend не запускается
- Убедитесь, что установлены все зависимости
- Проверьте, что порт 8000 не занят другим приложением

### Frontend не может подключиться к Backend
- Убедитесь, что Backend запущен на порту 8000
- Проверьте настройки CORS в backend/app.py

### Ошибки импорта
- Убедитесь, что вы находитесь в правильной директории
- Проверьте, что все файлы на месте
