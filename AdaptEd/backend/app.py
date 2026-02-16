from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import lessons, users, agents, auth
from routes import assistant, homework, tests

try:
	from dotenv import load_dotenv  # type: ignore
	import os
	env_path = os.path.join(os.path.dirname(__file__), '.env')
	load_dotenv(env_path)
except Exception:
	def load_dotenv():
		return None

# Инициализируем БД ПОСЛЕ загрузки .env
from utils.db import init_db
init_db()  # Создает таблицы только если их нет

# Инициализируем assistant_service после инициализации БД
try:
	from services.assistant import get_assistant_service
	get_assistant_service()
except Exception:
	pass

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
app.include_router(tests.router, tags=["Tests"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AdaptEd API!"}

@app.on_event("shutdown")
async def shutdown_event():
    try:
        try:
            from agents.orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator()
            orchestrator.profiler.flush_all_profiles()
        except Exception:
            pass
        
        try:
            from services.student_analytics import get_analytics_service
            analytics_service = get_analytics_service()
            analytics_service.adaptive_educator.flush_all_data()
        except Exception:
            pass
        
        try:
            from services.assistant import get_assistant_service
            assistant_service = get_assistant_service()
            assistant_service.flush_all_profiles()
        except Exception:
            pass
    except Exception:
        pass

@app.get("/batcher-stats")
def get_batcher_stats():
    """Endpoint для получения статистики батчеров"""
    try:
        from utils.batched_saver import (
            get_profiler_batcher,
            get_analytics_batcher,
            get_personality_batcher
        )
        
        return {
            "profiler": get_profiler_batcher().get_stats(),
            "analytics": get_analytics_batcher().get_stats(),
            "personality": get_personality_batcher().get_stats()
        }
    except Exception as e:
        return {"error": str(e)}