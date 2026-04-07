from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from utils.db import Base


class StudentDebt(Base):  # type: ignore
    __tablename__ = "student_debts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, default="topic_gap")  # test | homework | manual | topic_gap
    source_id = Column(String(128), nullable=True)
    status = Column(String(50), nullable=False, default="open")  # open | in_progress | resolved | archived
    priority = Column(Integer, nullable=False, default=2)  # 1..5
    progress = Column(Float, nullable=False, default=0.0)  # 0..100
    due_date = Column(DateTime, nullable=True)
    target_accuracy = Column(Float, nullable=False, default=80.0)
    created_by = Column(String(64), nullable=True)  # teacher_id | system
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    remedial_assignments = relationship("RemedialAssignment", back_populates="debt", cascade="all, delete-orphan")


class RemedialAssignment(Base):  # type: ignore
    __tablename__ = "remedial_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    debt_id = Column(Integer, ForeignKey("student_debts.id"), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    kind = Column(String(50), nullable=False)  # adaptive_task | material | course
    payload = Column(JSON, nullable=False, default={})
    attempts_required = Column(Integer, nullable=False, default=1)
    attempts_done = Column(Integer, nullable=False, default=0)
    progress = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="assigned")  # assigned | in_progress | completed
    due_date = Column(DateTime, nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    debt = relationship("StudentDebt", back_populates="remedial_assignments")
