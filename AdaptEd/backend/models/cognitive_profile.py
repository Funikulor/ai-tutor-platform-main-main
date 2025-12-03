"""
Модель когнитивного профиля ученика
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class ErrorTag(str, Enum):
    """Типы ошибок ученика"""
    MISSING_FORMULA = "missing_formula"
    CONCEPT_CONFUSION = "concept_confusion"
    CARELESSNESS = "carelessness"
    LOGIC_GAP = "logic_gap"
    CALCULATION_ERROR = "calculation_error"
    NOT_ATTEMPTED = "not_attempted"


class LearningStyle(str, Enum):
    """Стили обучения"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"


class ContentPreference(str, Enum):
    """Предпочтения по формату контента"""
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    MINI_TEST = "mini_test"


class EmotionalState(str, Enum):
    """Эмоциональные состояния"""
    CONFIDENT = "confident"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ENCOURAGED = "encouraged"
    MOTIVATED = "motivated"


class ErrorAnalysis(BaseModel):
    """Анализ конкретной ошибки"""
    error_type: ErrorTag
    justification: str
    similar_errors_count: int = 0
    suggested_remediation: Optional[str] = None


class TaskAttempt(BaseModel):
    """Попытка выполнения задания"""
    task_id: int
    question: str
    user_answer: Optional[int]
    correct_answer: int
    is_correct: bool
    time_spent_seconds: Optional[int] = None
    attempts_count: int = 1
    error_analysis: Optional[ErrorAnalysis] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class CognitiveProfile(BaseModel):
    """Полный когнитивный профиль ученика"""
    user_id: str
    
    # Знания по темам (0.0 - 1.0)
    topic_mastery: Dict[str, float] = Field(default_factory=dict)
    
    # История ошибок
    error_history: List[ErrorAnalysis] = Field(default_factory=list)
    
    # Статистика ошибок по типам
    error_frequency: Dict[ErrorTag, int] = Field(default_factory=dict)
    
    # Стиль обучения (определяется на основе поведения)
    learning_style: Optional[LearningStyle] = None
    
    # Предпочтения по контенту
    content_preferences: List[ContentPreference] = Field(default_factory=list)
    
    # Текущее эмоциональное состояние
    current_emotional_state: EmotionalState = EmotionalState.NEUTRAL
    
    # История заданий
    task_history: List[TaskAttempt] = Field(default_factory=list)
    
    # Прогресс
    total_tasks_completed: int = 0
    correct_tasks_count: int = 0
    accuracy_rate: float = 0.0
    
    # Назначенные задания учителем
    assigned_tasks: Dict[str, List[int]] = Field(default_factory=dict)  # topic -> [task_ids]
    
    # Мотивация
    points: int = 0
    level: int = 1
    achievements: List[str] = Field(default_factory=list)
    
    # Метаданные
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True

