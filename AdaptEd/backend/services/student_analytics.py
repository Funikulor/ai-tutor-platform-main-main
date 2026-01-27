"""
Сервис для управления аналитикой учеников
Интегрирует AdaptiveEducatorAgent с системой
"""
from typing import Dict, Any, Optional
from agents.adaptive_educator_agent import AdaptiveEducatorAgent
from agents.profiler_agent import ProfilerAgent
from models.student_analytics import StudentAnalyticsData
from models.cognitive_profile import CognitiveProfile


class StudentAnalyticsService:
    """Сервис для управления аналитикой учеников"""
    
    def __init__(self):
        self.adaptive_educator = AdaptiveEducatorAgent()
        self.profiler = None  # Будет установлен автоматически при первом использовании
    
    def _get_profiler(self) -> Optional[ProfilerAgent]:
        """Получить ProfilerAgent из orchestrator"""
        if self.profiler is None:
            try:
                from agents.orchestrator import AgentOrchestrator
                orchestrator = AgentOrchestrator()
                self.profiler = orchestrator.profiler
            except Exception:
                pass
        return self.profiler
    
    def process_chat_message(self, user_id: str, message: str, 
                            cognitive_profile: Optional[CognitiveProfile] = None) -> Dict[str, Any]:
        """
        Обрабатывает сообщение в чате и собирает аналитику
        
        Returns:
        - response: ответ для ученика
        - analytics_updated: обновлены ли аналитические данные
        - ethics_message: сообщение об этике (если первое взаимодействие)
        """
        input_data = {
            "user_id": user_id,
            "message": message,
            "action": "chat"
        }
        
        result = self.adaptive_educator.process(input_data)
        
        # Интегрируем с CognitiveProfile если доступен
        if cognitive_profile:
            self._sync_with_cognitive_profile(user_id, cognitive_profile)
        
        return result
    
    def process_test_result(self, user_id: str, test_result: Dict[str, Any],
                           cognitive_profile: Optional[CognitiveProfile] = None) -> Dict[str, Any]:
        """
        Обрабатывает результат теста
        
        test_result должен содержать:
        - subject: предмет
        - accuracy: точность (0-100)
        - errors: список ошибок/тем
        - time_spent_seconds: время выполнения
        """
        input_data = {
            "user_id": user_id,
            "test_result": test_result,
            "action": "test"
        }
        
        result = self.adaptive_educator.process(input_data)
        
        # Интегрируем с CognitiveProfile
        if cognitive_profile:
            self._sync_with_cognitive_profile(user_id, cognitive_profile)
        
        return result
    
    def process_task_attempt(self, user_id: str, task_attempt: Dict[str, Any],
                            cognitive_profile: Optional[CognitiveProfile] = None) -> Dict[str, Any]:
        """
        Обрабатывает попытку выполнения задания
        
        task_attempt должен содержать:
        - is_correct: правильность ответа
        - error_type: тип ошибки (опционально)
        - time_spent_seconds: время выполнения
        """
        input_data = {
            "user_id": user_id,
            "task_attempt": task_attempt,
            "action": "task"
        }
        
        result = self.adaptive_educator.process(input_data)
        
        # Интегрируем с CognitiveProfile
        if cognitive_profile:
            self._sync_with_cognitive_profile(user_id, cognitive_profile)
        
        return result
    
    def get_analytics(self, user_id: str) -> Dict[str, Any]:
        """Получить аналитические данные об ученике"""
        input_data = {
            "user_id": user_id,
            "action": "get_analytics"
        }
        return self.adaptive_educator.process(input_data)
    
    def record_hint_request(self, user_id: str):
        """Записать запрос подсказки"""
        self.adaptive_educator.record_hint_request(user_id)
    
    def _sync_with_cognitive_profile(self, user_id: str, cognitive_profile: CognitiveProfile):
        """Синхронизирует данные с CognitiveProfile (двусторонняя синхронизация)"""
        student_data = self.adaptive_educator.get_student_data(user_id)
        if not student_data:
            return
        
        # Синхронизируем слабые темы из CognitiveProfile в StudentAnalytics
        if cognitive_profile.error_frequency:
            top_errors = sorted(
                cognitive_profile.error_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            for error_tag, count in top_errors:
                error_str = str(error_tag.value) if hasattr(error_tag, 'value') else str(error_tag)
                if error_str not in student_data.academic_traits.weak_topics:
                    student_data.academic_traits.weak_topics.append(error_str)
        
        # Синхронизируем слабые темы из topic_mastery
        for topic, mastery in cognitive_profile.topic_mastery.items():
            if mastery < 0.5 and topic not in student_data.academic_traits.weak_topics:
                student_data.academic_traits.weak_topics.append(topic)
        
        # Синхронизируем точность тестов
        if cognitive_profile.accuracy_rate > 0:
            student_data.academic_traits.test_accuracy = f"{cognitive_profile.accuracy_rate:.0f}%"
        
        # Синхронизируем стиль обучения
        if cognitive_profile.learning_style:
            from models.student_analytics import LearningStyleType
            style_map = {
                "visual": LearningStyleType.VISUAL,
                "auditory": LearningStyleType.AUDITORY,
                "kinesthetic": LearningStyleType.KINESTHETIC,
                "reading": LearningStyleType.READING
            }
            style_str = cognitive_profile.learning_style.value if hasattr(cognitive_profile.learning_style, 'value') else str(cognitive_profile.learning_style)
            if style_str in style_map:
                student_data.behavioral_traits.learning_style = style_map[style_str]
        
        # Синхронизируем эмоциональное состояние
        if cognitive_profile.current_emotional_state:
            from models.student_analytics import EmotionalTone
            emotion_map = {
                "confident": EmotionalTone.CONFIDENT,
                "neutral": EmotionalTone.NEUTRAL,
                "frustrated": EmotionalTone.FRUSTRATED,
                "motivated": EmotionalTone.POSITIVE,
                "encouraged": EmotionalTone.POSITIVE
            }
            emotion_str = cognitive_profile.current_emotional_state.value if hasattr(cognitive_profile.current_emotional_state, 'value') else str(cognitive_profile.current_emotional_state)
            if emotion_str in emotion_map:
                student_data.behavioral_traits.emotional_state = emotion_map[emotion_str]
        
        # Обратная синхронизация: обновляем CognitiveProfile из StudentAnalytics
        profiler = self._get_profiler()
        if profiler:
            # Обновляем тренды улучшения в метриках прогресса
            if cognitive_profile.improvement_trends:
                for topic, trend in cognitive_profile.improvement_trends.items():
                    if trend > 0.05:  # Улучшение > 5%
                        if topic not in student_data.progress_metrics.improvement_areas:
                            student_data.progress_metrics.improvement_areas.append(topic)
                    elif trend < -0.05:  # Ухудшение > 5%
                        if topic not in student_data.progress_metrics.improvement_areas:
                            student_data.progress_metrics.improvement_areas.append(topic)
        
        # Сохраняем обновленные данные
        self.adaptive_educator._save_student_data(user_id)


# Глобальный экземпляр сервиса
_analytics_service = None


def get_analytics_service() -> StudentAnalyticsService:
    """Получить или создать экземпляр сервиса"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = StudentAnalyticsService()
    return _analytics_service

