"""
Модель профиля личности ученика на основе диалога
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class PersonalityTrait(BaseModel):
    """Черта личности"""
    trait_name: str  # e.g., "curiosity", "persistence", "confidence"
    score: float = Field(ge=0.0, le=1.0)  # 0.0 - 1.0
    evidence: List[str] = Field(default_factory=list)  # Примеры из диалога


class CommunicationStyle(BaseModel):
    """Стиль общения"""
    formality: float = Field(default=0.5, ge=0.0, le=1.0)  # 0 - неформальный, 1 - формальный
    verbosity: float = Field(default=0.5, ge=0.0, le=1.0)  # 0 - краткий, 1 - подробный
    question_frequency: float = Field(default=0.5, ge=0.0, le=1.0)  # Частота задавания вопросов
    emotional_tone: str = "neutral"  # positive, neutral, negative, frustrated


class PersonalityProfile(BaseModel):
    """Профиль личности ученика"""
    user_id: str
    
    # Черты личности
    traits: Dict[str, PersonalityTrait] = Field(default_factory=dict)
    
    # Стиль общения
    communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)
    
    # История диалогов
    chat_history: List[Dict[str, str]] = Field(default_factory=list)  # [{role, content, timestamp}]
    
    # Выявленные интересы
    interests: List[str] = Field(default_factory=list)
    
    # Выявленные слабые места (из диалога)
    mentioned_weaknesses: List[str] = Field(default_factory=list)
    
    # Метаданные
    last_updated: datetime = Field(default_factory=datetime.now)
    total_messages: int = 0



