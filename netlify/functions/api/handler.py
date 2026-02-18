"""
Простой handler для тестирования Netlify Function
"""
import json

def handler(event, context):
    """Обработчик Netlify Function"""
    try:
        # Пробуем импортировать FastAPI app
        import sys
        import os
        
        # Определяем пути
        function_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(function_dir, '..', '..', '..'))
        backend_path = os.path.join(repo_root, 'AdaptEd', 'backend')
        
        # Добавляем путь к backend
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Меняем рабочую директорию
        original_cwd = os.getcwd()
        os.chdir(backend_path)
        
        try:
            from app import app
            from mangum import Mangum
            
            # Создаем адаптер
            adapter = Mangum(app, lifespan="off")
            
            # Обрабатываем запрос
            response = adapter(event, context)
            
            os.chdir(original_cwd)
            return response
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            os.chdir(original_cwd)
            
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Backend error",
                    "message": str(e),
                    "traceback": error_details,
                    "backend_path": backend_path
                })
            }
            
    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Function initialization error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })
        }

