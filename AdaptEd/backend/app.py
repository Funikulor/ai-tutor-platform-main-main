import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routes import lessons, users, agents, auth
from routes import assistant, homework, tests, materials, monitoring, rag

try:
	from dotenv import load_dotenv  # type: ignore
	env_path = os.path.join(os.path.dirname(__file__), '.env')
	load_dotenv(env_path)
	print(f"[App] Загружен .env из: {env_path}")
	proxy_set = bool(os.getenv("PROXYAPI_KEY"))
	hf_tok_set = bool(os.getenv("HF_API_TOKEN"))
	exp_raw = (os.getenv("ASSISTANT_PROVIDER") or "").strip()
	exp = exp_raw.lower()
	if exp == "neuroapi" or exp == "openai":
		exp = "proxyapi"
	if exp in ("proxyapi", "hf_api", "local"):
		effective = exp
	elif proxy_set:
		effective = "proxyapi"
	elif hf_tok_set:
		effective = "hf_api"
	else:
		effective = "proxyapi"
	if exp_raw:
		exp_disp = exp_raw
		if exp_raw.lower() in ("openai", "neuroapi"):
			exp_disp = f"{exp_raw} (совместимо с ProxyAPI/OpenAI-compatible HTTP)"
		print(f"[App] ASSISTANT_PROVIDER={exp_disp!r} → канал {effective!r}")
	else:
		print(
			f"[App] ASSISTANT_PROVIDER не задан → канал {effective!r} "
			f"(ключи: PROXYAPI_KEY={'да' if proxy_set else 'нет'}, HF_API_TOKEN={'да' if hf_tok_set else 'нет'})"
		)
	print(f"[App] PROXYAPI_KEY={'установлен' if proxy_set else 'не установлен'}, HF_API_TOKEN={'установлен' if hf_tok_set else 'не установлен'}")
	if not proxy_set and not hf_tok_set:
		print(
			"[App] ВНИМАНИЕ: ни PROXYAPI_KEY, ни HF_API_TOKEN не заданы — онлайн-LLM недоступен по ключу. "
			"Укажите PROXYAPI_KEY (ProxyAPI / NeuroAPI) в Railway Variables или HF_API_TOKEN."
		)
	elif exp_raw.lower() == "proxyapi" and not proxy_set:
		print(
			"[App] ВНИМАНИЕ: указан ASSISTANT_PROVIDER=proxyapi, но PROXYAPI_KEY пуст. "
			"Задайте ключ или временно попробуйте ASSISTANT_PROVIDER=hf_api с HF_API_TOKEN."
		)
	elif exp_raw.lower() == "hf_api" and not hf_tok_set:
		print(
			"[App] ВНИМАНИЕ: указан ASSISTANT_PROVIDER=hf_api, но HF_API_TOKEN пуст. "
			"Часть запросов к Hugging Face без токена может не проходить; задайте токен."
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
        try:
            response = await call_next(request)
        except HTTPException as exc:
            response = JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
        except Exception:
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )

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
app.include_router(rag.router, tags=["RAG"])

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
        "rag/",
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
