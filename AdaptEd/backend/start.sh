#!/bin/bash
# Скрипт запуска для Railway
# Читает PORT из переменной окружения или использует 8080 по умолчанию

PORT=${PORT:-8080}
python -m uvicorn app:app --host 0.0.0.0 --port $PORT

