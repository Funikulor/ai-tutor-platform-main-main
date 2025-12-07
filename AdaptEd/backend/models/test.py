from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from utils.db import Base


class Test(Base):  # type: ignore
	__tablename__ = "tests"

	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(String(255), nullable=False)
	topic = Column(String(255), nullable=True)
	difficulty = Column(String(50), nullable=True)
	source = Column(String(50), default="manual")  # manual | ai
	creator_id = Column(String(64), nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)

	questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
	submissions = relationship("TestSubmission", back_populates="test", cascade="all, delete-orphan")


class TestQuestion(Base):  # type: ignore
	__tablename__ = "test_questions"

	id = Column(Integer, primary_key=True, autoincrement=True)
	test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
	question = Column(Text, nullable=False)
	options = Column(JSON, nullable=False)  # list of str
	correct_index = Column(Integer, nullable=False)
	explanation = Column(Text, nullable=True)

	test = relationship("Test", back_populates="questions")


class TestSubmission(Base):  # type: ignore
	__tablename__ = "test_submissions"

	id = Column(Integer, primary_key=True, autoincrement=True)
	test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
	user_id = Column(String(64), nullable=False)
	answers = Column(JSON, nullable=False)  # list of int
	score = Column(Integer, nullable=True)  # 0..100
	feedback = Column(Text, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)

	test = relationship("Test", back_populates="submissions")



