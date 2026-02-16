# Как запустить AdaptEd

## 🚀 Быстрый запуск

### Вариант 1: Использование BAT файлов (самый простой способ)

1. **Запустите Backend:**
   - Дважды кликните на файл `start_backend.bat`
   - Подождите пока появится сообщение "Application startup complete"
   - Backend будет доступен на: http://localhost:8000

2. **Запустите Frontend (в отдельном окне):**
   - Дважды кликните на файл `start_frontend.bat`
   - Frontend откроется автоматически в браузере
   - Или откройте вручную: http://localhost:8501

### Вариант 2: Запуск через командную строку

**Терминал 1 (Backend):**
```bash
cd AdaptEd\backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Терминал 2 (Frontend):**
```bash
cd AdaptEd\frontend
streamlit run app.py
```

## 📋 После запуска

1. Откройте браузер и перейдите на http://localhost:8501
2. Нажмите кнопку "Fetch Math Tasks" для загрузки задач
3. Введите ответы и проверьте их
4. Используйте секцию "User Management" для работы с пользователями

## 🔧 Если что-то не работает

### Backend не запускается
- Убедитесь, что порт 8000 свободен
- Проверьте, что установлены все зависимости: `pip install -r AdaptEd/backend/requirements.txt`

### Frontend не запускается
- Убедитесь, что Backend запущен на порту 8000
- Проверьте, что установлены все зависимости: `pip install -r AdaptEd/frontend/requirements.txt`

### Ошибка "No module named 'streamlit'"
Выполните:
```bash
pip install streamlit requests --upgrade
```

## 📚 Дополнительная информация

- API документация: http://localhost:8000/docs
- Руководство по проекту: `AdaptEd/README.md`
- Диагностика и решение проблем: `TROUBLESHOOTING.md`
