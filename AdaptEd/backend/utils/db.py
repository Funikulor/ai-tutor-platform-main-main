import os
from typing import Optional

try:
	from sqlalchemy import create_engine  # type: ignore
	from sqlalchemy.orm import sessionmaker, declarative_base, Session  # type: ignore
	SQLA_AVAILABLE = True
except Exception:
	# SQLAlchemy not installed; operate in no-DB mode
	create_engine = None  # type: ignore
	sessionmaker = None  # type: ignore
	declarative_base = None  # type: ignore
	Session = None  # type: ignore
	SQLA_AVAILABLE = False

DATABASE_URL = os.getenv("DATABASE_URL")

if SQLA_AVAILABLE:
	Base = declarative_base()
else:
	class _Base:  # lightweight placeholder to avoid import errors in modules
		pass
	Base = _Base  # type: ignore

_engine = create_engine(DATABASE_URL) if (SQLA_AVAILABLE and DATABASE_URL) else None
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine) if _engine else None


def init_db():
	if _engine is None or not SQLA_AVAILABLE:
		return
	# import models to register metadata (only when SQLAlchemy is available)
	try:
		from models.document import Document  # noqa: F401
		Base.metadata.create_all(bind=_engine)
	except Exception:
		# Silently skip DB init if models import fails
		return


def get_db() -> Optional["Session"]:
	if _SessionLocal is None:
		return None
	return _SessionLocal()


def has_db() -> bool:
	return _engine is not None and SQLA_AVAILABLE
