from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from utils.db import Base


class Homework(Base):  # type: ignore
	__tablename__ = "homeworks"

	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(String(255), nullable=False)
	description = Column(Text, nullable=True)
	subject = Column(String(100), nullable=True)
	due_date = Column(DateTime, nullable=True)
	status = Column(String(50), default="new")  # new | in_progress | submitted | checked
	assigned_to = Column(String(64), nullable=False)  # user_id ученика
	created_by = Column(String(64), nullable=True)  # teacher_id
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	submissions = relationship("HomeworkSubmission", back_populates="homework")


class HomeworkSubmission(Base):  # type: ignore
	__tablename__ = "homework_submissions"

	id = Column(Integer, primary_key=True, autoincrement=True)
	homework_id = Column(Integer, ForeignKey("homeworks.id"), nullable=False)
	user_id = Column(String(64), nullable=False)
	answer_text = Column(Text, nullable=True)
	feedback = Column(Text, nullable=True)
	score = Column(Float, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)

	homework = relationship("Homework", back_populates="submissions")






