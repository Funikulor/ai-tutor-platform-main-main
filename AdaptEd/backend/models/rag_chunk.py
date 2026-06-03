"""
Модель для RAG: хранит фрагменты знаний (темы / куски учебника) и их эмбеддинги.

embedding хранится как JSON-массив чисел (вектор), чтобы не требовать
расширения pgvector — для прототипа сравнение делаем на стороне Python (numpy).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from utils.db import Base


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, index=True)
    # Узкая тема, которую вернём как ярлык (например, "Квадратные уравнения").
    topic = Column(String(255), nullable=False, index=True)
    # Текст фрагмента: описание темы или кусок учебника.
    text = Column(Text, nullable=False)
    # Источник: "taxonomy" (ручной список тем) или название учебника.
    source = Column(String(255), nullable=False, default="taxonomy", index=True)
    # Вектор-эмбеддинг как список float (JSON). Размерность зависит от модели (1536).
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
