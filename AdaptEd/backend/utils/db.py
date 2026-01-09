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

# Инициализация Base (не зависит от DATABASE_URL)
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

# Инициализация engine будет выполнена после загрузки .env
_engine = None
_SessionLocal = None


def _ensure_engine():
	"""Создаёт engine/Session, если они ещё не инициализированы, но DATABASE_URL уже есть (например, после load_dotenv)."""
	global _engine, _SessionLocal
	if _engine is None and SQLA_AVAILABLE:
		DATABASE_URL = os.getenv("DATABASE_URL")
		if DATABASE_URL:
			_engine = _make_engine(DATABASE_URL)
			_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def init_db():
	"""Инициализирует базу данных: создает engine и все таблицы (только если их нет)"""
	_ensure_engine()
	if _engine is None or not SQLA_AVAILABLE:
		return
	
	# import models to register metadata (only when SQLAlchemy is available)
	try:
		from models.document import Document  # noqa: F401
		from models.homework import Homework, HomeworkSubmission  # noqa: F401
		from models.test import Test, TestQuestion, TestSubmission  # noqa: F401
		from models.user_db import User  # noqa: F401
		
		# Проверяем, существуют ли уже таблицы
		from sqlalchemy import inspect
		inspector = inspect(_engine)
		existing_tables = inspector.get_table_names()
		
		# Список ожидаемых таблиц
		expected_tables = ['documents', 'homeworks', 'homework_submissions', 
		                  'tests', 'test_questions', 'test_submissions', 'users']
		
		# Проверяем, все ли таблицы существуют
		missing_tables = [tbl for tbl in expected_tables if tbl not in existing_tables]
		
		if missing_tables:
			# Создаем только недостающие таблицы
			Base.metadata.create_all(bind=_engine)
		# Если все таблицы есть, ничего не делаем
		
	except Exception as e:
		# Тихо пропускаем ошибки при инициализации
		pass


def get_db() -> Optional["Session"]:
	_ensure_engine()
	if _SessionLocal is None:
		return None
	return _SessionLocal()


def has_db() -> bool:
	_ensure_engine()
	return _engine is not None and SQLA_AVAILABLE
