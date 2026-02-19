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

### Frontend не запускается
- Убедитесь, что Backend запущен на порту 8000
- Проверьте, что установлен Node.js (версия 16 или выше)
- Проверьте, что установлены все зависимости: `npm install`
- Убедитесь, что переменная `VITE_API_URL` в `.env` указывает на правильный адрес backend

## 📚 Дополнительная информация

- API документация: http://localhost:8000/docs
- Руководство по проекту: `AdaptEd/README.md`
- Диагностика и решение проблем: `TROUBLESHOOTING.md`
