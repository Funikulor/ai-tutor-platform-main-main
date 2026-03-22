import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routes import lessons, users, agents, auth
from routes import assistant, homework, tests, materials

try:
	from dotenv import load_dotenv  # type: ignore
	env_path = os.path.join(os.path.dirname(__file__), '.env')
	load_dotenv(env_path)
	print(f"[App] Загружен .env из: {env_path}")
	print(f"[App] ASSISTANT_PROVIDER={os.getenv('ASSISTANT_PROVIDER', 'не установлен')}")
	print(f"[App] OPENAI_MODEL={os.getenv('OPENAI_MODEL', 'не установлен')}")
	print(f"[App] OPENAI_API_KEY={'установлен' if os.getenv('OPENAI_API_KEY') else 'не установлен'}")
	provider = os.getenv('ASSISTANT_PROVIDER', 'openai')
	openai_set = bool(os.getenv('OPENAI_API_KEY'))
	proxy_set = bool(os.getenv('PROXYAPI_KEY'))
	if provider == 'openai' and not openai_set:
		print("[App] ВНИМАНИЕ: ASSISTANT_PROVIDER=openai, но OPENAI_API_KEY не задан. Добавьте ключ в .env (локально) или в Railway → Variables.")
	if provider == 'proxyapi' and not proxy_set:
		print("[App] ВНИМАНИЕ: ASSISTANT_PROVIDER=proxyapi, но PROXYAPI_KEY не задан. Добавьте ключ в .env (локально) или в Railway → Variables.")
	if provider in ('openai', 'proxyapi') and not openai_set and not proxy_set:
		print("[App] ВНИМАНИЕ: Ни OPENAI_API_KEY, ни PROXYAPI_KEY не заданы. Генерация заданий и чат будут возвращать ошибку. Задайте переменные в .env (локально) или в Railway → Variables.")
except Exception as e:
	print(f"[App] Ошибка загрузки .env: {e}")
	def load_dotenv():
		return None

from utils.db import init_db

init_db()

# Инициализируем assistant_service после инициализации БД
try:
	from services.assistant import get_assistant_service
	get_assistant_service()
except Exception:
	pass


def _flush_on_shutdown() -> None:
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


@asynccontextmanager
async def _app_lifespan(_app: FastAPI):
    yield
    _flush_on_shutdown()


app = FastAPI(redirect_slashes=False, lifespan=_app_lifespan)


def _get_allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    env_origins = [item.strip() for item in raw.split(",") if item.strip()]
    defaults = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://loving-flow-production-6ddf.up.railway.app",
        "https://ai-tutor-platform-main-main-production.up.railway.app",
    ]
    unique: list[str] = []
    for origin in [*defaults, *env_origins]:
        if origin not in unique:
            unique.append(origin)
    return unique

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
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
app.include_router(materials.router, tags=["Materials"])

# Serve built frontend from backend domain if available.
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = BACKEND_DIR.parent / "frontend" / "build"
FRONTEND_INDEX_FILE = FRONTEND_BUILD_DIR / "index.html"

if FRONTEND_BUILD_DIR.exists():
    assets_dir = FRONTEND_BUILD_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

@app.get("/")
def read_root():
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(str(FRONTEND_INDEX_FILE))
    return {"message": "Welcome to the AdaptEd API!"}

@app.get("/debug")
def debug_storage():
    """Отладочный endpoint для проверки хранилища"""
    from utils.persistent_storage import persistent_storage

    data_file = Path(persistent_storage.data_file)
    return {
        "users_count": len(persistent_storage.get("users", {})),
        "users": persistent_storage.get("users", {}),
        "data_file_exists": data_file.is_file(),
    }

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


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if not FRONTEND_INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Not Found")

    api_prefixes = (
        "auth/",
        "users/",
        "agents/",
        "assistant/",
        "homework/",
        "tests/",
        "tasks/",
        "materials",
        "materials/",
        "debug",
        "batcher-stats",
        "docs",
        "redoc",
        "openapi.json",
    )
    if full_path in api_prefixes or any(full_path.startswith(prefix) for prefix in api_prefixes):
        raise HTTPException(status_code=404, detail="Not Found")

    return FileResponse(str(FRONTEND_INDEX_FILE))
