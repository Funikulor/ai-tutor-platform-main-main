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

# Если DATABASE_URL не установлен, используем SQLite по умолчанию
if not DATABASE_URL and SQLA_AVAILABLE:
	backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	sqlite_path = os.path.join(backend_dir, "adapted.db")
	DATABASE_URL = f"sqlite:///{sqlite_path}"
	print(f"[DB] DATABASE_URL не установлен, используем SQLite: {sqlite_path}")

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
		from models.chat import ChatSession  # noqa: F401
		from models.homework import Homework, HomeworkSubmission  # noqa: F401
		from models.test import Test, TestQuestion, TestSubmission  # noqa: F401
		from models.user_db import User  # noqa: F401
		from models.curriculum import (  # noqa: F401
			CurriculumSubject,
			CurriculumSection,
			CurriculumTopic,
			CurriculumTopicTask,
		)
		Base.metadata.create_all(bind=_engine)
		try:
			from sqlalchemy import text

			def _sqlite_has_column(conn, table_name: str, column_name: str) -> bool:
				r = conn.execute(text(f"PRAGMA table_info({table_name})"))
				cols = [row[1] for row in r.fetchall()]
				return column_name in cols

			def _ensure_column(conn, table_name: str, column_name: str, column_type: str):
				if DATABASE_URL and "sqlite" in DATABASE_URL:
					if not _sqlite_has_column(conn, table_name, column_name):
						conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
					return

				# Postgres / other engines that support IF NOT EXISTS.
				conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"))

			with _engine.connect() as conn:
				# Existing users compatibility columns.
				_ensure_column(conn, "users", "parent_fio", "VARCHAR(255)")
				_ensure_column(conn, "users", "parent_phone", "VARCHAR(20)")
				_ensure_column(conn, "users", "avatar_seed", "VARCHAR(64)")

				# Test/homework rework columns.
				_ensure_column(conn, "test_questions", "correct_answer", "JSON")
				_ensure_column(conn, "test_submissions", "homework_id", "INTEGER")
				_ensure_column(conn, "test_submissions", "question_results", "JSON")
				_ensure_column(conn, "test_submissions", "correct_count", "INTEGER")
				_ensure_column(conn, "test_submissions", "total_questions", "INTEGER")
				_ensure_column(conn, "test_submissions", "summary", "TEXT")
				_ensure_column(conn, "homeworks", "kind", "VARCHAR(50)")
				_ensure_column(conn, "homeworks", "test_id", "INTEGER")
				_ensure_column(conn, "homeworks", "assignment_type", "VARCHAR(50)")
				_ensure_column(conn, "homework_submissions", "test_submission_id", "INTEGER")
				# Каталог → библиотека (JSON в SQLite как TEXT, в Postgres — JSONB через IF NOT EXISTS)
				if DATABASE_URL and "sqlite" in DATABASE_URL:
					_ensure_column(conn, "curriculum_topics", "library_material_ids", "TEXT")
					_ensure_column(conn, "curriculum_topics", "library_course_ids", "TEXT")
				else:
					try:
						conn.execute(
							text(
								"ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS library_material_ids JSONB DEFAULT '[]'::jsonb"
							)
						)
						conn.execute(
							text(
								"ALTER TABLE curriculum_topics ADD COLUMN IF NOT EXISTS library_course_ids JSONB DEFAULT '[]'::jsonb"
							)
						)
					except Exception:
						pass
				conn.commit()
		except Exception:
			pass
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
