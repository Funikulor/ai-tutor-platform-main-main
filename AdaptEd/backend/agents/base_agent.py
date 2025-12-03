"""
Базовый класс для всех ИИ-агентов
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json


class AgentMessage(BaseModel):
    """Формат сообщения между агентами"""
    from_agent: str
    to_agent: str
    message_type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None


class BaseAgent(ABC):
    """
    Базовый класс для всех ИИ-агентов в системе
    """
    
    def __init__(self, name: str):
        self.name = name
        self.message_queue = []
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка входных данных агентом
        Должен быть реализован в каждом конкретном агенте
        """
        pass
    
    def send_message(self, to_agent: str, message_type: str, data: Dict[str, Any]):
        """Отправка сообщения другому агенту"""
        message = AgentMessage(
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            data=data
        )
        self.message_queue.append(message)
        return message
    
    def receive_message(self) -> Optional[AgentMessage]:
        """Получение сообщения из очереди"""
        if self.message_queue:
            return self.message_queue.pop(0)
        return None
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование действий агента"""
        print(f"[{self.name}] [{level}] {message}")

