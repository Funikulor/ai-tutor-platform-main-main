from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import lessons, users, agents, auth
from routes import assistant, homework

try:
	from dotenv import load_dotenv  # type: ignore
	import os
	# Загружаем .env из папки backend
	env_path = os.path.join(os.path.dirname(__file__), '.env')
	load_dotenv(env_path)
	print(f"[App] Загружен .env из: {env_path}")
	print(f"[App] ASSISTANT_PROVIDER={os.getenv('ASSISTANT_PROVIDER', 'не установлен')}")
	print(f"[App] OLLAMA_URL={os.getenv('OLLAMA_URL', 'не установлен')}")
	print(f"[App] OLLAMA_MODEL={os.getenv('OLLAMA_MODEL', 'не установлен')}")
	
	# Инициализируем assistant_service после загрузки .env
	from services.assistant import get_assistant_service
	get_assistant_service()  # Создаем экземпляр с правильными настройками
	print(f"[App] AssistantService инициализирован")
except Exception as e:
	def load_dotenv():
		return None
	print(f"[App] Ошибка загрузки .env: {e}")

from utils.db import init_db

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes - без префикса для обратной совместимости
app.include_router(auth.router, tags=["Auth"])
app.include_router(lessons.router, tags=["Lessons"])
app.include_router(users.router, tags=["Users"])
app.include_router(agents.router, tags=["Agents"])
app.include_router(assistant.router, tags=["Assistant"])
app.include_router(homework.router, tags=["Homework"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AdaptEd API!"}

@app.get("/debug")
def debug_storage():
    """Отладочный endpoint для проверки хранилища"""
    from utils.persistent_storage import persistent_storage
    import os
    return {
        "users_count": len(persistent_storage.get("users", {})),
        "users": persistent_storage.get("users", {}),
        "data_file_exists": os.path.exists("data.json")
    }