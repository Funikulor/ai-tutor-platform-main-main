from sqlalchemy import Column, Integer, String, Text, DateTime, func
from utils.db import Base


class Document(Base):
	__tablename__ = "documents"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(255), nullable=False, index=True)
	content = Column(Text, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now())





