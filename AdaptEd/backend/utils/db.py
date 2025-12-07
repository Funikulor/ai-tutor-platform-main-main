import os
from typing import Optional

try:
	from sqlalchemy import create_engine  # type: ignore
	from sqlalchemy.orm import sessionmaker, declarative_base, Session  # type: ignore
	from sqlalchemy.pool import NullPool  # type: ignore
	SQLA_AVAILABLE = True
except Exception:
	# SQLAlchemy not installed; operate in no-DB mode
	create_engine = None  # type: ignore
	sessionmaker = None  # type: ignore
	declarative_base = None  # type: ignore
	Session = None  # type: ignore
	NullPool = None  # type: ignore
	SQLA_AVAILABLE = False

DATABASE_URL = os.getenv("DATABASE_URL")

if SQLA_AVAILABLE:
	Base = declarative_base()
else:
	class _Base:  # lightweight placeholder to avoid import errors in modules
		pass
	Base = _Base  # type: ignore

def _make_engine(db_url: str):
	connect_args = {}
	engine_kwargs = {}
	if db_url.startswith("sqlite"):
		# SQLite в файле: отключаем check_same_thread и берём минимальный pool
		connect_args = {"check_same_thread": False}
		engine_kwargs = {"pool_pre_ping": True, "poolclass": NullPool}
	else:
		engine_kwargs = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}
	return create_engine(db_url, connect_args=connect_args, **engine_kwargs)


_engine = _make_engine(DATABASE_URL) if (SQLA_AVAILABLE and DATABASE_URL) else None
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine) if _engine else None


def _ensure_engine():
	"""Создаёт engine/Session, если они ещё не инициализированы, но DATABASE_URL уже есть (например, после load_dotenv)."""
	global _engine, _SessionLocal, DATABASE_URL
	if _engine is None and SQLA_AVAILABLE:
		DATABASE_URL = os.getenv("DATABASE_URL")
		if DATABASE_URL:
			_engine = _make_engine(DATABASE_URL)
			_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def init_db():
	_ensure_engine()
	if _engine is None or not SQLA_AVAILABLE:
		return
	# import models to register metadata (only when SQLAlchemy is available)
	try:
		from models.document import Document  # noqa: F401
		from models.homework import Homework, HomeworkSubmission  # noqa: F401
		from models.test import Test, TestQuestion, TestSubmission  # noqa: F401
		Base.metadata.create_all(bind=_engine)
	except Exception:
		# Silently skip DB init if models import fails
		return


def get_db() -> Optional["Session"]:
	_ensure_engine()
	if _SessionLocal is None:
		return None
	return _SessionLocal()


def has_db() -> bool:
	_ensure_engine()
	return _engine is not None and SQLA_AVAILABLE
