# Dockerfile для Fly.io или других платформ
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose порт
EXPOSE 8080

# Команда запуска
CMD uvicorn app:app --host 0.0.0.0 --port $PORT

