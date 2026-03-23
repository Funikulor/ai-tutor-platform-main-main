"""
Модель для хранения аналитических данных об ученике
Используется адаптивным педагогом-аналитиком
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from enum import Enum


class Subject(str, Enum):
    """Предметы"""
    MATH = "математика"
    LITERATURE = "литература"
    RUSSIAN = "русский язык"
    HISTORY = "история"
    PHYSICS = "физика"
    CHEMISTRY = "химия"
    BIOLOGY = "биология"
    OTHER = "другое"


class LearningStyleType(str, Enum):
    """Стили обучения"""
    VISUAL = "визуал"
    AUDITORY = "аудиал"
    KINESTHETIC = "кинестетик"
    READING = "чтение"


class MotivationLevel(str, Enum):
    """Уровень мотивации"""
    HIGH = "высокая"
    MEDIUM = "средняя"
    LOW = "низкая"


class EmotionalTone(str, Enum):
    """Эмоциональный тон"""
    POSITIVE = "позитивный"
    NEUTRAL = "нейтральный"
    NEGATIVE = "негативный"
    FRUSTRATED = "фрустрированный"
    CONFIDENT = "уверенный"


class AcademicTrait(BaseModel):
    """Академические признаки ученика"""
    subject_levels: Dict[str, str] = Field(default_factory=dict)  # предмет -> уровень (начальный/средний/продвинутый)
    weak_topics: List[str] = Field(default_factory=list)  # Темы, вызывающие затруднения
    test_accuracy: str = "0%"  # Точность в тестах
    typical_errors: List[str] = Field(default_factory=list)  # Типичные ошибки
    task_completion_speed: Optional[float] = None  # Средняя скорость выполнения заданий (секунды)
    error_patterns: Dict[str, int] = Field(default_factory=dict)  # Паттерны ошибок: тип -> количество


class BehavioralTrait(BaseModel):
    """Поведенческие и когнитивные признаки"""
    learning_style: Optional[LearningStyleType] = None  # Стиль обучения
    motivation_level: MotivationLevel = MotivationLevel.MEDIUM  # Уровень мотивации
    motivation_evidence: List[str] = Field(default_factory=list)  # Доказательства уровня мотивации
    emotional_state: EmotionalTone = EmotionalTone.NEUTRAL  # Текущее эмоциональное состояние
    emotional_history: List[Dict[str, str]] = Field(default_factory=list)  # История эмоциональных состояний
    preferred_explanation_format: Optional[str] = None  # Предпочитаемый формат объяснений
    interaction_style: str = "активный"  # активный/пассивный


class ProgressMetrics(BaseModel):
    """Метрики прогресса"""
    test_results_dynamics: List[Dict[str, Any]] = Field(default_factory=list)  # Динамика результатов тестов
    hint_requests_frequency: int = 0  # Частота обращений за подсказками
    hint_requests_history: List[datetime] = Field(default_factory=list)  # История запросов подсказок
    weekly_progress: Dict[str, float] = Field(default_factory=dict)  # Прогресс по неделям
    monthly_progress: Dict[str, float] = Field(default_factory=dict)  # Прогресс по месяцам
    improvement_areas: List[str] = Field(default_factory=list)  # Области улучшения
    strengths: List[str] = Field(default_factory=list)  # Сильные стороны


class StudentAnalyticsData(BaseModel):
    """Полные аналитические данные об ученике"""
    student_id: str
    
    # Академические признаки
    academic_traits: AcademicTrait = Field(default_factory=AcademicTrait)
    
    # Поведенческие и когнитивные признаки
    behavioral_traits: BehavioralTrait = Field(default_factory=BehavioralTrait)
    
    # Метрики прогресса
    progress_metrics: ProgressMetrics = Field(default_factory=ProgressMetrics)
    
    # Настройки приватности
    data_collection_enabled: bool = True  # Разрешен ли сбор данных
    
    # Метаданные
    first_interaction_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.now)
    total_interactions: int = 0  # Общее количество взаимодействий
    
    # История диалогов для анализа
    conversation_snippets: List[Dict[str, str]] = Field(default_factory=list)  # Ключевые фрагменты диалогов

    model_config = ConfigDict(use_enum_values=True)

