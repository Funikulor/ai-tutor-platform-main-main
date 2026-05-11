import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routes import lessons, users, agents, auth
from routes import assistant, homework, tests, materials, monitoring

try:
	from dotenv import load_dotenv  # type: ignore
	env_path = os.path.join(os.path.dirname(__file__), '.env')
	load_dotenv(env_path)
	print(f"[App] Загружен .env из: {env_path}")
	openai_set = bool(os.getenv("OPENAI_API_KEY"))
	proxy_set = bool(os.getenv("PROXYAPI_KEY"))
	exp_raw = (os.getenv("ASSISTANT_PROVIDER") or "").strip()
	exp = exp_raw.lower()
	if exp == "neuroapi":
		exp = "proxyapi"
	if exp in ("openai", "proxyapi", "hf_api", "local"):
		effective = exp
	elif openai_set:
		effective = "openai"
	elif proxy_set:
		effective = "proxyapi"
	else:
		effective = "openai"
	if exp_raw:
		print(f"[App] ASSISTANT_PROVIDER={exp_raw!r} → канал {effective!r}")
	else:
		print(
			f"[App] ASSISTANT_PROVIDER не задан → канал {effective!r} "
			f"(ключи: OPENAI_API_KEY={'да' if openai_set else 'нет'}, PROXYAPI_KEY={'да' if proxy_set else 'нет'})"
		)
	print(f"[App] OPENAI_API_KEY={'установлен' if openai_set else 'не установлен'}")
	if not openai_set and not proxy_set:
		print(
			"[App] ВНИМАНИЕ: ни OPENAI_API_KEY, ни PROXYAPI_KEY не заданы. "
			"Чат и генерация через LLM недоступны. Задайте переменные в Railway Variables (сервис backend)."
		)
	elif exp == "openai" and not openai_set:
		print(
			"[App] ВНИМАНИЕ: указан ASSISTANT_PROVIDER=openai, но OPENAI_API_KEY пуст. "
			"Укажите ключ или уберите переменную (будет автовыбор по PROXYAPI_KEY)."
		)
	elif exp == "proxyapi" and not proxy_set:
		print(
			"[App] ВНИМАНИЕ: указан ASSISTANT_PROVIDER=proxyapi, но PROXYAPI_KEY пуст. "
			"Укажите ключ или уберите переменную для автовыбора по OPENAI_API_KEY."
		)
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
            from utils.orchestrator_singleton import get_orchestrator

            get_orchestrator().profiler.flush_all_profiles()
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
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://loving-flow-production-6ddf.up.railway.app",
        "https://ai-tutor-platform-main-main-production.up.railway.app",
    ]
    unique: list[str] = []
    for origin in [*defaults, *env_origins]:
        if origin not in unique:
            unique.append(origin)
    return unique


def _railway_cors_regex() -> Optional[str]:
    """Любой публичный URL вида https://<service>.up.railway.app (деплой фронта)."""
    if os.getenv("CORS_DISABLE_RAILWAY_REGEX", "").lower() in ("1", "true", "yes"):
        return None
    return r"^https://[\w.-]+\.up\.railway\.app$"


def _is_allowed_origin(origin: Optional[str]) -> bool:
    if not origin:
        return False
    if origin in _get_allowed_origins():
        return True
    pattern = _railway_cors_regex()
    if pattern and re.match(pattern, origin):
        return True
    return False


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_origin_regex=_railway_cors_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _force_cors_headers(request, call_next):
    """
    Дополнительный защитный слой CORS:
    - гарантирует CORS-заголовки даже на ошибках backend;
    - стабильно отвечает на preflight OPTIONS.
    """
    origin = request.headers.get("origin")
    origin_allowed = _is_allowed_origin(origin)

    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    if origin_allowed and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
        requested_headers = request.headers.get("access-control-request-headers")
        response.headers["Access-Control-Allow-Headers"] = requested_headers or "*"

    return response


# API routes - без префикса для обратной совместимости
app.include_router(auth.router, tags=["Auth"])
app.include_router(lessons.router, tags=["Lessons"])
app.include_router(users.router, tags=["Users"])
app.include_router(agents.router, tags=["Agents"])
app.include_router(assistant.router, tags=["Assistant"])
app.include_router(homework.router, tags=["Homework"])
app.include_router(tests.router, tags=["Tests"])
app.include_router(materials.router, tags=["Materials"])
app.include_router(monitoring.router, tags=["Monitoring"])

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

def _diagnostics_endpoints_enabled() -> bool:
    """Диагностика только при DEBUG=1/true (локально или явно на сервере)."""
    return os.getenv("DEBUG", "").strip().lower() in ("1", "true", "yes", "on")


@app.get("/debug")
def debug_storage():
    """Отладочный endpoint (без персональных данных). Включается переменной DEBUG."""
    if not _diagnostics_endpoints_enabled():
        raise HTTPException(status_code=404, detail="Not Found")
    from utils.persistent_storage import persistent_storage

    data_file = Path(persistent_storage.data_file)
    return {
        "users_count": len(persistent_storage.get("users", {})),
        "data_file_exists": data_file.is_file(),
    }

@app.get("/health")
def health():
    """Быстрая проверка живости API (без БД и тяжёлых зависимостей) — для фронта и Railway."""
    return {"status": "ok"}


@app.get("/batcher-stats")
def get_batcher_stats():
    """Статистика батчеров — только при DEBUG."""
    if not _diagnostics_endpoints_enabled():
        raise HTTPException(status_code=404, detail="Not Found")
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
        "health",
        "docs",
        "redoc",
        "openapi.json",
    )
    if full_path in api_prefixes or any(full_path.startswith(prefix) for prefix in api_prefixes):
        raise HTTPException(status_code=404, detail="Not Found")

    return FileResponse(str(FRONTEND_INDEX_FILE))
