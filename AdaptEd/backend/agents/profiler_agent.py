"""
Агент профилирования ученика
Отслеживает и обновляет когнитивный профиль ученика
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from models.cognitive_profile import (
    CognitiveProfile, 
    TaskAttempt, 
    ErrorAnalysis,
    ErrorTag,
    LearningStyle,
    ContentPreference,
    EmotionalState
)


class ProfilerAgent(BaseAgent):
    """
    Профилирует ученика на основе истории выполнения заданий
    """
    
    def __init__(self):
        super().__init__("Profiler")
        self.profiles: Dict[str, CognitiveProfile] = {}
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновляет профиль ученика
        
        Input:
        - user_id: ID ученика
        - task_attempt: TaskAttempt объект
        - error_analysis: анализ ошибки от ErrorAnalyzerAgent
        
        Output:
        - updated_profile: обновленный профиль
        - insights: выводы о прогрессе
        """
        user_id = input_data.get('user_id')
        task_attempt = input_data.get('task_attempt')
        error_analysis = input_data.get('error_analysis')
        
        self.log(f"Updating profile for user {user_id}")
        
        # Получаем или создаем профиль
        if user_id not in self.profiles:
            self.profiles[user_id] = CognitiveProfile(user_id=user_id)
        
        profile = self.profiles[user_id]
        
        # Добавляем попытку выполнения
        if task_attempt:
            profile.task_history.append(task_attempt)
        
        # Обновляем статистику
        self._update_statistics(profile)
        
        # Обновляем историю ошибок
        if error_analysis:
            self._update_error_patterns(profile, error_analysis)
        
        # Определяем стиль обучения
        self._detect_learning_style(profile)
        
        # Обновляем эмоциональное состояние
        self._update_emotional_state(profile)
        
        # Управляем мотивацией
        self._update_motivation(profile)
        
        # Генерируем инсайты
        insights = self._generate_insights(profile)
        
        self.profiles[user_id] = profile
        
        return {
            "profile": profile.dict(),
            "insights": insights
        }
    
    def get_profile(self, user_id: str) -> Optional[CognitiveProfile]:
        """Получить профиль ученика"""
        if user_id not in self.profiles:
            # Создаем новый профиль если его нет
            self.profiles[user_id] = CognitiveProfile(user_id=user_id)
        return self.profiles.get(user_id)
    
    def _update_statistics(self, profile: CognitiveProfile):
        """Обновление статистики"""
        profile.total_tasks_completed = len(profile.task_history)
        correct_count = sum(1 for attempt in profile.task_history if attempt.is_correct)
        profile.correct_tasks_count = correct_count
        profile.accuracy_rate = (correct_count / profile.total_tasks_completed * 100) if profile.total_tasks_completed > 0 else 0
    
    def _update_error_patterns(self, profile: CognitiveProfile, error_analysis: Dict[str, Any]):
        """Обновление паттернов ошибок"""
        error_type = error_analysis.get('error_type')
        if error_type:
            if error_type not in profile.error_frequency:
                profile.error_frequency[error_type] = 0
            profile.error_frequency[error_type] += 1
            
            # Добавляем в историю
            error_record = ErrorAnalysis(
                error_type=error_type,
                justification=error_analysis.get('justification', ''),
                suggested_remediation=error_analysis.get('suggested_remediation')
            )
            profile.error_history.append(error_record)
    
    def _detect_learning_style(self, profile: CognitiveProfile):
        """Определяет стиль обучения на основе поведения"""
        if len(profile.task_history) < 5:
            return
        
        # Простая эвристика: если ученик быстро усваивает - визуальный
        # Если медленно но стабильно - текст
        recent_tasks = profile.task_history[-10:]
        avg_accuracy = sum(1 for t in recent_tasks if t.is_correct) / len(recent_tasks) if recent_tasks else 0
        
        if avg_accuracy > 0.7 and profile.task_history:
            profile.learning_style = LearningStyle.VISUAL
        else:
            profile.learning_style = LearningStyle.READING
    
    def _update_emotional_state(self, profile: CognitiveProfile):
        """Обновляет эмоциональное состояние"""
        recent_tasks = profile.task_history[-5:] if len(profile.task_history) >= 5 else profile.task_history
        if not recent_tasks:
            return
        
        recent_accuracy = sum(1 for t in recent_tasks if t.is_correct) / len(recent_tasks)
        
        if recent_accuracy >= 0.8:
            profile.current_emotional_state = EmotionalState.CONFIDENT
        elif recent_accuracy >= 0.6:
            profile.current_emotional_state = EmotionalState.MOTIVATED
        elif recent_accuracy < 0.3:
            profile.current_emotional_state = EmotionalState.FRUSTRATED
        else:
            profile.current_emotional_state = EmotionalState.NEUTRAL
    
    def _update_motivation(self, profile: CognitiveProfile):
        """Обновляет систему мотивации"""
        # Начисляем очки за правильные ответы
        if profile.task_history:
            last_task = profile.task_history[-1]
            if last_task.is_correct:
                profile.points += 10
        
        # Определяем уровень
        profile.level = min(profile.points // 100 + 1, 10)
        
        # Разблокировка достижений
        if profile.points >= 50 and "first_steps" not in profile.achievements:
            profile.achievements.append("first_steps")
        if profile.points >= 200 and "steady_progress" not in profile.achievements:
            profile.achievements.append("steady_progress")
        if profile.accuracy_rate >= 80 and "high_achiever" not in profile.achievements:
            profile.achievements.append("high_achiever")
    
    def _generate_insights(self, profile: CognitiveProfile) -> Dict[str, Any]:
        """Генерирует инсайты о прогрессе"""
        insights = {
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        # Анализ самых частых ошибок
        if profile.error_frequency:
            most_common_error = max(profile.error_frequency.items(), key=lambda x: x[1])
            insights["weaknesses"].append(f"Часто встречается ошибка типа: {most_common_error[0]}")
            insights["recommendations"].append(f"Следует обратить внимание на: {most_common_error[0]}")
        
        # Прогресс
        if profile.accuracy_rate > 70:
            insights["strengths"].append(f"Высокая точность ({profile.accuracy_rate:.1f}%)")
        
        # Мотивация
        if profile.level > 1:
            insights["strengths"].append(f"Уровень {profile.level}")
        
        return insights

