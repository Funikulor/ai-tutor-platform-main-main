from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from utils.db import Base


class ChatSession(Base):  # type: ignore
	__tablename__ = "chat_sessions"

	id = Column(String(64), primary_key=True, index=True)
	user_id = Column(String(64), nullable=False, index=True)
	title = Column(String(255), nullable=False, default="Новый чат")
	messages_json = Column(Text, nullable=False, default="[]")
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

