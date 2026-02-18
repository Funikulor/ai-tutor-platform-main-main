"""
Netlify Function для FastAPI backend
Использует Mangum для адаптации FastAPI к AWS Lambda/Netlify Functions
"""
import sys
import os

# Добавляем путь к backend
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'AdaptEd', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Устанавливаем переменные окружения из Netlify
# Netlify автоматически передает их в функции

# Импортируем FastAPI приложение
try:
    from app import app
    from mangum import Mangum
    
    # Создаем handler для Netlify Functions
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Если ошибка, возвращаем информативное сообщение
    def handler(event, context):
        import json
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Backend initialization failed",
                "message": str(e)
            })
        }

