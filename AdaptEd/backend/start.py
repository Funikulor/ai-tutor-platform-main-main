#!/usr/bin/env python3
"""
Скрипт запуска для Railway
Читает PORT из переменной окружения или использует 8080 по умолчанию
"""
import os
import sys
import subprocess

# Получаем PORT из переменной окружения
port = os.getenv('PORT', '8080')

# Запускаем uvicorn
cmd = [
    sys.executable, '-m', 'uvicorn',
    'app:app',
    '--host', '0.0.0.0',
    '--port', str(port)
]

print(f"Starting server on port {port}...")
sys.exit(subprocess.call(cmd))


