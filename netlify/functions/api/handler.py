"""
Netlify Function для FastAPI backend
"""
import json
import sys
import os

# Определяем пути
function_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(function_dir, '..', '..', '..'))
backend_path = os.path.join(repo_root, 'AdaptEd', 'backend')

# Добавляем пути в sys.path
paths_to_add = [
    backend_path,
    repo_root,
    os.path.join(backend_path, 'routes'),
    os.path.join(backend_path, 'models'),
    os.path.join(backend_path, 'services'),
    os.path.join(backend_path, 'utils'),
    os.path.join(backend_path, 'agents'),
]

for path in paths_to_add:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

# Инициализируем handler при загрузке модуля
handler_instance = None
init_error = None

try:
    # Меняем рабочую директорию на backend
    original_cwd = os.getcwd()
    os.chdir(backend_path)
    
    try:
        from app import app
        from mangum import Mangum
        
        # Создаем адаптер
        handler_instance = Mangum(app, lifespan="off")
        
    except Exception as e:
        import traceback
        init_error = {
            "error": "Backend initialization failed",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "backend_path": backend_path,
            "cwd": os.getcwd()
        }
    finally:
        os.chdir(original_cwd)
        
except Exception as e:
    import traceback
    init_error = {
        "error": "Function setup failed",
        "message": str(e),
        "traceback": traceback.format_exc()
    }

def handler(event, context):
    """Обработчик Netlify Function"""
    # Если была ошибка инициализации, возвращаем её
    if init_error:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(init_error)
        }
    
    # Если handler не создан, возвращаем ошибку
    if handler_instance is None:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Handler not initialized"})
        }
    
    try:
        # Обрабатываем запрос через Mangum
        response = handler_instance(event, context)
        return response
    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "error": "Request processing failed",
                "message": str(e),
                "traceback": traceback.format_exc()
            })
        }

