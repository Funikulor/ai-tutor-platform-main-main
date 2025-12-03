"""
Агент-наставник
Генерирует эмпатичные и мотивирующие сообщения
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from models.cognitive_profile import CognitiveProfile, EmotionalState


class MentorAgent(BaseAgent):
    """
    Агент, который общается с учеником на уровне наставника
    """
    
    def __init__(self):
        super().__init__("Mentor")
        self.conversation_history: Dict[str, list] = {}
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует мотивирующее сообщение для ученика
        
        Input:
        - user_id: ID ученика
        - profile: профиль ученика
        - task_result: результат выполнения задания (correct/wrong/timeout)
        - context: дополнительный контекст
        
        Output:
        - message: мотивирующее сообщение
        - tone: тон сообщения
        - suggestions: предложения для помощи
        """
        user_id = input_data.get('user_id')
        profile = input_data.get('profile')
        task_result = input_data.get('task_result', 'unknown')
        
        self.log(f"Generating mentor message for user {user_id}")
        
        # Анализируем ситуацию
        emotional_state = profile.current_emotional_state if profile else EmotionalState.NEUTRAL
        
        # Генерируем сообщение
        message = self._generate_message(task_result, emotional_state, profile)
        
        # Определяем тон
        tone = self._determine_tone(task_result, emotional_state)
        
        # Генерируем предложения
        suggestions = self._generate_suggestions(profile, task_result)
        
        return {
            "message": message,
            "tone": tone,
            "suggestions": suggestions,
            "encouragement_level": self._calculate_encouragement_level(profile, task_result)
        }
    
    def _generate_message(self, task_result: str, emotional_state: EmotionalState, profile: Optional[CognitiveProfile]) -> str:
        """Генерирует персонализированное сообщение"""
        
        # Сообщения для правильного ответа
        if task_result == 'correct':
            messages = [
                "Отлично! Ты справился! 🎉",
                "Правильно! Твои знания растут! 💪",
                "Великолепно! Продолжай в том же духе! 🌟",
                "Так держать! Ты делаешь успехи! ⭐"
            ]
            if profile and profile.level > 5:
                messages.insert(0, f"Уровень {profile.level}! Ты настоящий мастер! 🏆")
        
        # Сообщения для неправильного ответа
        elif task_result == 'wrong':
            messages = [
                "Не расстраивайся! Ошибки - это часть обучения. 😊",
                "Не беда! Давай разберемся вместе. 💙",
                "Это сложная задача. Ты уже много знаешь! 💪",
                "Каждая ошибка - это урок. Продолжай пытаться! 🌱"
            ]
            
            if emotional_state == EmotionalState.FRUSTRATED:
                messages = [
                    "Вижу, что задача вызвала затруднения. Давай возьмем перерыв? ☕",
                    "Порой нужно сделать паузу. Ты уже много достиг! 🌟",
                    "Всякое бывает. Главное - не сдаваться! 💪"
                ]
        
        # Сообщения для прогресса
        else:
            messages = [
                "Ты на правильном пути! 🚀",
                "Продолжай учиться! Каждый шаг важен! 💫",
                "Твой прогресс впечатляет! 🌟"
            ]
        
        # Добавляем информацию о прогрессе
        if profile:
            if profile.accuracy_rate >= 70:
                messages.append(f"Твоя точность {profile.accuracy_rate:.1f}% - это отличный результат! 🎯")
            if profile.achievements:
                messages.append(f"У тебя {len(profile.achievements)} достижений! {', '.join(profile.achievements)} 🏅")
        
        import random
        return random.choice(messages)
    
    def _determine_tone(self, task_result: str, emotional_state: EmotionalState) -> str:
        """Определяет тон сообщения"""
        if task_result == 'correct':
            return "celebratory"
        elif task_result == 'wrong' and emotional_state == EmotionalState.FRUSTRATED:
            return "supportive"
        elif task_result == 'wrong':
            return "encouraging"
        else:
            return "neutral"
    
    def _generate_suggestions(self, profile: Optional[CognitiveProfile], task_result: str) -> list:
        """Генерирует предложения помощи"""
        suggestions = []
        
        if task_result == 'wrong':
            suggestions.append({
                "type": "hint",
                "title": "Получить подсказку",
                "description": "Разобрать задачу по шагам"
            })
            suggestions.append({
                "type": "video",
                "title": "Посмотреть объяснение",
                "description": "Видеоурок по этой теме"
            })
            suggestions.append({
                "type": "break",
                "title": "Сделать перерыв",
                "description": "Вернуться через несколько минут"
            })
        else:
            suggestions.append({
                "type": "continue",
                "title": "Следующее задание",
                "description": "Продолжить обучение"
            })
            suggestions.append({
                "type": "review",
                "title": "Повторить тему",
                "description": "Закрепить материал"
            })
        
        # Добавляем специфичные предложения на основе профиля
        if profile:
            if profile.points < 100:
                suggestions.append({
                    "type": "achievement",
                    "title": "Достижения",
                    "description": f"Ты на уровне {profile.level}! Заработай больше очков!"
                })
        
        return suggestions
    
    def _calculate_encouragement_level(self, profile: Optional[CognitiveProfile], task_result: str) -> int:
        """Вычисляет уровень поддержки (1-5)"""
        level = 3  # Нейтральный уровень
        
        if task_result == 'correct':
            level = 5  # Максимальная поддержка
        elif task_result == 'wrong':
            level = 2  # Повышенная поддержка
        
        # Учитываем прогресс ученика
        if profile:
            if profile.accuracy_rate < 50:
                level += 1  # Дополнительная поддержка для отстающих
            elif profile.accuracy_rate > 80:
                level += 1  # Позитивное подкрепление для успешных
        
        return min(level, 5)

