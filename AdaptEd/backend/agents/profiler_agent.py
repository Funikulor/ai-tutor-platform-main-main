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
from utils.persistent_storage import persistent_storage
from utils.batched_saver import get_profiler_batcher
from datetime import datetime, timedelta
import json


class ProfilerAgent(BaseAgent):
    """
    Профилирует ученика на основе истории выполнения заданий
    """
    
    def __init__(self):
        super().__init__("Profiler")
        self.profiles: Dict[str, CognitiveProfile] = {}
        self._load_profiles()  # Загружаем профили при инициализации
    
    def _load_profiles(self):
        """Загружает профили из persistent_storage"""
        try:
            profiles_data = persistent_storage.get("cognitive_profiles", {})
            for user_id, profile_data in profiles_data.items():
                try:
                    # Конвертируем данные обратно в CognitiveProfile
                    profile = CognitiveProfile(**profile_data)
                    self.profiles[user_id] = profile
                    self.log(f"Загружен профиль для пользователя {user_id}")
                except Exception as e:
                    self.log(f"Ошибка загрузки профиля {user_id}: {e}")
            self.log(f"Загружено {len(self.profiles)} профилей из хранилища")
        except Exception as e:
            self.log(f"Ошибка загрузки профилей: {e}")
    
    def _save_profile(self, user_id: str, force: bool = False):
        """
        Сохраняет профиль в persistent_storage через батчинг
        
        Args:
            user_id: ID пользователя
            force: Если True, сохраняет немедленно (для критичных обновлений)
        """
        try:
            if user_id in self.profiles:
                profile = self.profiles[user_id]
                # Конвертируем в dict для сохранения
                profile_dict = profile.dict()
                # Обновляем last_updated
                profile_dict['last_updated'] = datetime.now().isoformat()
                
                # Используем батчинг для сохранения
                batcher = get_profiler_batcher()
                if force:
                    # Принудительное сохранение (например, при завершении)
                    batcher.flush(user_id)
                    # Также сохраняем напрямую для гарантии
                    profiles_data = persistent_storage.get("cognitive_profiles", {})
                    profiles_data[user_id] = profile_dict
                    persistent_storage.set("cognitive_profiles", profiles_data)
                else:
                    # Планируем сохранение через батчер
                    batcher.schedule_save(user_id, profile_dict)
        except Exception as e:
            self.log(f"Ошибка сохранения профиля {user_id}: {e}")
    
    def flush_all_profiles(self):
        """Принудительно сохраняет все профили (используется при завершении)"""
        batcher = get_profiler_batcher()
        batcher.flush_all()
    
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
        
        # Обновляем мастерство по темам
        if task_attempt:
            self._update_topic_mastery(profile, task_attempt)
        
        # Обновляем историю ошибок
        if error_analysis:
            self._update_error_patterns(profile, error_analysis)
        
        # Определяем стиль обучения
        self._detect_learning_style(profile)
        
        # Обновляем эмоциональное состояние
        self._update_emotional_state(profile)
        
        # Управляем мотивацией
        self._update_motivation(profile)
        
        # Обновляем долгосрочную память о прогрессе
        self._update_progress_history(profile)
        
        # Генерируем инсайты
        insights = self._generate_insights(profile)
        
        self.profiles[user_id] = profile
        # Сохраняем профиль после обновления
        self._save_profile(user_id)
        
        return {
            "profile": profile.dict(),
            "insights": insights
        }
    
    def get_profile(self, user_id: str) -> Optional[CognitiveProfile]:
        """Получить профиль ученика"""
        if user_id not in self.profiles:
            # Создаем новый профиль если его нет
            self.profiles[user_id] = CognitiveProfile(user_id=user_id)
            # Сохраняем новый профиль
            self._save_profile(user_id)
        return self.profiles.get(user_id)
    
    def get_all_profiles(self) -> Dict[str, CognitiveProfile]:
        """Получить все профили учеников"""
        return self.profiles
    
    def _update_statistics(self, profile: CognitiveProfile):
        """Обновление статистики"""
        profile.total_tasks_completed = len(profile.task_history)
        correct_count = sum(1 for attempt in profile.task_history if attempt.is_correct)
        profile.correct_tasks_count = correct_count
        # accuracy_rate в процентах (0-100)
        profile.accuracy_rate = (correct_count / profile.total_tasks_completed * 100) if profile.total_tasks_completed > 0 else 0.0
    
    def _update_topic_mastery(self, profile: CognitiveProfile, task_attempt: TaskAttempt):
        """Обновляет мастерство по темам на основе выполнения заданий"""
        if not task_attempt.topic:
            return
        
        topic = task_attempt.topic
        
        # Инициализируем тему, если её нет
        if topic not in profile.topic_mastery:
            profile.topic_mastery[topic] = 0.5  # Начальное значение 50%
        
        # Обновляем мастерство на основе результата
        if task_attempt.is_correct:
            # Правильный ответ: увеличиваем мастерство
            profile.topic_mastery[topic] = min(1.0, profile.topic_mastery[topic] + 0.05)  # +5% за правильный ответ
        else:
            # Неправильный ответ: уменьшаем мастерство
            profile.topic_mastery[topic] = max(0.0, profile.topic_mastery[topic] - 0.03)  # -3% за неправильный ответ
        
        # Округляем до 2 знаков после запятой
        profile.topic_mastery[topic] = round(profile.topic_mastery[topic], 2)
    
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
    
    def _update_progress_history(self, profile: CognitiveProfile):
        """Обновляет долгосрочную память о прогрессе"""
        now = datetime.now()
        today = now.date().isoformat()
        
        # Находим или создаем запись за сегодня
        today_record = None
        for record in profile.progress_history:
            if record.get("date") == today:
                today_record = record
                break
        
        if not today_record:
            today_record = {
                "date": today,
                "tasks_completed": 0,
                "correct_tasks": 0,
                "topics_worked": [],
                "accuracy": 0.0
            }
            profile.progress_history.append(today_record)
        
        # Обновляем статистику за сегодня
        today_record["tasks_completed"] = len([t for t in profile.task_history 
                                               if t.timestamp.date().isoformat() == today])
        today_record["correct_tasks"] = len([t for t in profile.task_history 
                                             if t.is_correct and t.timestamp.date().isoformat() == today])
        if today_record["tasks_completed"] > 0:
            today_record["accuracy"] = today_record["correct_tasks"] / today_record["tasks_completed"]
        
        # Обновляем темы
        today_topics = set()
        for task in profile.task_history:
            if task.timestamp.date().isoformat() == today and task.topic:
                today_topics.add(task.topic)
        today_record["topics_worked"] = list(today_topics)
        
        # Вычисляем скорость обучения (заданий в день за последние 7 дней)
        last_7_days = [now - timedelta(days=i) for i in range(7)]
        tasks_last_7_days = len([t for t in profile.task_history 
                                 if t.timestamp.date() in [d.date() for d in last_7_days]])
        profile.learning_velocity = tasks_last_7_days / 7.0
        
        # Вычисляем тренды улучшения по темам
        self._calculate_improvement_trends(profile)
    
    def _calculate_improvement_trends(self, profile: CognitiveProfile):
        """Вычисляет тренды улучшения по темам"""
        now = datetime.now()
        # Берем последние 30 дней
        last_30_days = [now - timedelta(days=i) for i in range(30)]
        
        # Группируем задачи по темам и периодам
        for topic in profile.topic_mastery.keys():
            # Задачи по теме за последние 15 дней
            recent_tasks = [t for t in profile.task_history 
                           if t.topic == topic and t.timestamp.date() in [d.date() for d in last_30_days[-15:]]]
            # Задачи по теме за предыдущие 15 дней
            older_tasks = [t for t in profile.task_history 
                          if t.topic == topic and t.timestamp.date() in [d.date() for d in last_30_days[:15]]]
            
            if len(recent_tasks) > 0 and len(older_tasks) > 0:
                recent_accuracy = sum(1 for t in recent_tasks if t.is_correct) / len(recent_tasks)
                older_accuracy = sum(1 for t in older_tasks if t.is_correct) / len(older_tasks)
                # Тренд: положительный если улучшение > 5%
                improvement = recent_accuracy - older_accuracy
                profile.improvement_trends[topic] = improvement

