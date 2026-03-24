"""
Каталог «предмет → раздел → тема» для админки (хранение в PostgreSQL / SQLite).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from utils.db import Base


class CurriculumSubject(Base):  # type: ignore
    __tablename__ = "curriculum_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sections = relationship(
        "CurriculumSection",
        back_populates="subject",
        order_by="CurriculumSection.sort_order",
        cascade="all, delete-orphan",
    )


class CurriculumSection(Base):  # type: ignore
    __tablename__ = "curriculum_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("curriculum_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    subject = relationship("CurriculumSubject", back_populates="sections")
    topics = relationship(
        "CurriculumTopic",
        back_populates="section",
        order_by="CurriculumTopic.sort_order",
        cascade="all, delete-orphan",
    )


class CurriculumTopic(Base):  # type: ignore
    __tablename__ = "curriculum_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("curriculum_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    teacher_notes = Column(Text, nullable=False, default="")
    grade_hint = Column(String(128), nullable=False, default="")
    elements_count = Column(Integer, nullable=False, default=0)
    tasks_count = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    # Связь с библиотекой: id материалов и мини-курсов из /materials и /library/courses
    library_material_ids = Column(JSON, nullable=True)
    library_course_ids = Column(JSON, nullable=True)

    section = relationship("CurriculumSection", back_populates="topics")
    catalog_tasks = relationship(
        "CurriculumTopicTask",
        back_populates="topic",
        order_by="CurriculumTopicTask.id",
        cascade="all, delete-orphan",
    )


class CurriculumTopicTask(Base):  # type: ignore
    __tablename__ = "curriculum_topic_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False, default="")

    topic = relationship("CurriculumTopic", back_populates="catalog_tasks")
