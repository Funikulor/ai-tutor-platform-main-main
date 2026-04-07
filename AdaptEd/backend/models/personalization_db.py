from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, JSON, String

from utils.db import Base


class CognitiveProfileRecord(Base):  # type: ignore
    __tablename__ = "cognitive_profiles"

    user_id = Column(String(64), primary_key=True, index=True)
    payload = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StudentAnalyticsRecord(Base):  # type: ignore
    __tablename__ = "student_analytics"

    user_id = Column(String(64), primary_key=True, index=True)
    payload = Column(JSON, nullable=False)
    ethics_message_shown = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PersonalityProfileRecord(Base):  # type: ignore
    __tablename__ = "personality_profiles"

    user_id = Column(String(64), primary_key=True, index=True)
    payload = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
