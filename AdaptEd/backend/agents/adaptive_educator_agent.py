"""
Адаптивный педагог-аналитик
Собирает данные об ученике в процессе диалога и тестирования
для персонализации обучения
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from models.student_analytics import (
    StudentAnalyticsData,
    AcademicTrait,
    BehavioralTrait,
    ProgressMetrics,
    LearningStyleType,
    MotivationLevel,
    EmotionalTone,
    Subject
)
from models.cognitive_profile import CognitiveProfile
from datetime import datetime, timedelta
import re


class AdaptiveEducatorAgent(BaseAgent):
    """
    Адаптивный педагог-аналитик
    Ненавязчиво собирает данные об ученике и персонализирует обучение
    """
    
    def __init__(self):
        super().__init__("AdaptiveEducator")
        self.student_data: Dict[str, StudentAnalyticsData] = {}
        self.ethics_message_shown: Dict[str, bool] = {}  # Показывали ли сообщение об этике
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает взаимодействие с учеником
        
        Input:
        - user_id: ID ученика
        - message: сообщение от ученика (опционально)
        - test_result: результат теста (опционально)
        - task_attempt: попытка выполнения задания (опционально)
        - action: тип действия (chat, test, task, get_analytics)
        
        Output:
        - response: ответ для ученика
        - analytics_data: аналитические данные (если action=get_analytics)
        - personalized_suggestion: персонализированное предложение
        """
        user_id = input_data.get('user_id')
        if not user_id:
            return {"error": "user_id is required"}
        
        action = input_data.get('action', 'chat')
        
        # Проверяем, разрешен ли сбор данных
        student_data = self._get_or_create_student_data(user_id)
        if not student_data.data_collection_enabled and action != 'get_analytics':
            # Если сбор данных отключен, просто возвращаем базовый ответ
            return {"response": "Сбор данных отключен. Продолжаем обучение."}
        
        # Показываем сообщение об этике при первом взаимодействии
        ethics_message = None
        if not self.ethics_message_shown.get(user_id, False):
            ethics_message = self._get_ethics_message()
            self.ethics_message_shown[user_id] = True
        
        if action == 'get_analytics':
            return self._get_analytics_output(user_id)
        elif action == 'chat':
            return self._process_chat(input_data, student_data, ethics_message)
        elif action == 'test':
            return self._process_test_result(input_data, student_data)
        elif action == 'task':
            return self._process_task_attempt(input_data, student_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _get_or_create_student_data(self, user_id: str) -> StudentAnalyticsData:
        """Получить или создать данные об ученике"""
        if user_id not in self.student_data:
            self.student_data[user_id] = StudentAnalyticsData(
                student_id=user_id,
                first_interaction_date=datetime.now()
            )
        return self.student_data[user_id]
    
    def _get_ethics_message(self) -> str:
        """Сообщение об этике и прозрачности"""
        return (
            "Привет! Я помогаю персонализировать твоё обучение. "
            "Все данные анонимизируются и используются только для улучшения твоих результатов. "
            "Можешь задать вопросы о приватности или отключить сбор данных командой '/стоп-сбор'!"
        )
    
    def _process_chat(self, input_data: Dict[str, Any], student_data: StudentAnalyticsData, 
                     ethics_message: Optional[str]) -> Dict[str, Any]:
        """Обработка диалога с учеником"""
        message = input_data.get('message', '')
        user_id = input_data.get('user_id')
        
        # Проверяем команды
        if '/стоп-сбор' in message.lower():
            student_data.data_collection_enabled = False
            return {
                "response": "Сбор данных отключен. Ты можешь включить его снова командой '/включить-сбор'.",
                "data_collection_enabled": False
            }
        elif '/включить-сбор' in message.lower():
            student_data.data_collection_enabled = True
            return {
                "response": "Сбор данных включен. Спасибо за доверие!",
                "data_collection_enabled": True
            }
        
        # Анализируем сообщение
        self._analyze_message(message, student_data)
        
        # Обновляем метрики
        student_data.total_interactions += 1
        student_data.last_updated = datetime.now()
        
        # Сохраняем ключевые фрагменты диалога
        if self._is_key_conversation_snippet(message):
            student_data.conversation_snippets.append({
                "content": message,
                "timestamp": str(datetime.now()),
                "type": "user_message"
            })
        
        # Генерируем персонализированный ответ
        personalized_response = self._generate_personalized_response(message, student_data)
        
        result = {
            "response": personalized_response,
            "analytics_updated": True
        }
        
        if ethics_message:
            result["ethics_message"] = ethics_message
        
        return result
    
    def _analyze_message(self, message: str, student_data: StudentAnalyticsData):
        """Анализирует сообщение ученика для сбора данных"""
        message_lower = message.lower()
        
        # Анализ эмоционального состояния
        emotional_state = self._detect_emotional_state(message)
        if emotional_state:
            student_data.behavioral_traits.emotional_state = emotional_state
            student_data.behavioral_traits.emotional_history.append({
                "state": emotional_state.value,
                "timestamp": str(datetime.now()),
                "trigger": message[:100]  # Первые 100 символов
            })
        
        # Выявление слабых тем
        weak_topics = self._extract_weak_topics(message)
        for topic in weak_topics:
            if topic not in student_data.academic_traits.weak_topics:
                student_data.academic_traits.weak_topics.append(topic)
        
        # Определение стиля обучения через предпочтения
        learning_style = self._detect_learning_style_from_message(message)
        if learning_style:
            student_data.behavioral_traits.learning_style = learning_style
        
        # Анализ мотивации
        motivation_evidence = self._analyze_motivation(message)
        if motivation_evidence:
            student_data.behavioral_traits.motivation_evidence.append(motivation_evidence)
            # Обновляем уровень мотивации
            if len(student_data.behavioral_traits.motivation_evidence) > 0:
                positive_count = sum(1 for e in student_data.behavioral_traits.motivation_evidence 
                                  if "активн" in e.lower() or "интерес" in e.lower() or "нравится" in e.lower())
                total = len(student_data.behavioral_traits.motivation_evidence)
                if positive_count / total > 0.6:
                    student_data.behavioral_traits.motivation_level = MotivationLevel.HIGH
                elif positive_count / total < 0.3:
                    student_data.behavioral_traits.motivation_level = MotivationLevel.LOW
                else:
                    student_data.behavioral_traits.motivation_level = MotivationLevel.MEDIUM
    
    def _detect_emotional_state(self, message: str) -> Optional[EmotionalTone]:
        """Определяет эмоциональное состояние из сообщения"""
        message_lower = message.lower()
        
        # Фразы стресса и фрустрации
        stress_phrases = [
            "никогда не пойму", "слишком сложно", "не получается", 
            "не понимаю", "не могу", "слишком трудно", "не справлюсь"
        ]
        if any(phrase in message_lower for phrase in stress_phrases):
            return EmotionalTone.FRUSTRATED
        
        # Позитивные фразы
        positive_phrases = [
            "понял", "получилось", "легко", "интересно", "нравится",
            "спасибо", "отлично", "классно"
        ]
        if any(phrase in message_lower for phrase in positive_phrases):
            return EmotionalTone.POSITIVE
        
        # Уверенность
        confident_phrases = [
            "знаю", "уверен", "точно", "легко решу", "справлюсь"
        ]
        if any(phrase in message_lower for phrase in confident_phrases):
            return EmotionalTone.CONFIDENT
        
        return None
    
    def _extract_weak_topics(self, message: str) -> List[str]:
        """Извлекает упоминания слабых тем из сообщения"""
        topics = []
        message_lower = message.lower()
        
        # Предметы
        subjects_map = {
            "математик": "математика",
            "алгебр": "алгебра",
            "геометри": "геометрия",
            "литератур": "литература",
            "русск": "русский язык",
            "истори": "история",
            "физик": "физика",
            "хими": "химия",
            "биологи": "биология"
        }
        
        for keyword, subject in subjects_map.items():
            if keyword in message_lower:
                topics.append(subject)
        
        # Конкретные темы
        topic_keywords = {
            "дроб": "дроби",
            "уравнени": "уравнения",
            "процент": "проценты",
            "график": "графики",
            "система уравнений": "системы уравнений",
            "тригонометр": "тригонометрия"
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in message_lower:
                topics.append(topic)
        
        return topics
    
    def _detect_learning_style_from_message(self, message: str) -> Optional[LearningStyleType]:
        """Определяет стиль обучения из сообщения"""
        message_lower = message.lower()
        
        visual_keywords = ["график", "картинк", "визуал", "рисунок", "схема", "диаграмм"]
        if any(kw in message_lower for kw in visual_keywords):
            return LearningStyleType.VISUAL
        
        auditory_keywords = ["объясни", "расскажи", "послушай", "аудио"]
        if any(kw in message_lower for kw in auditory_keywords):
            return LearningStyleType.AUDITORY
        
        kinesthetic_keywords = ["попробую", "сделаю", "потрогать", "практик"]
        if any(kw in message_lower for kw in kinesthetic_keywords):
            return LearningStyleType.KINESTHETIC
        
        return None
    
    def _analyze_motivation(self, message: str) -> Optional[str]:
        """Анализирует мотивацию из сообщения"""
        message_lower = message.lower()
        
        active_phrases = ["хочу", "интересно", "давай", "попробую", "готов"]
        if any(phrase in message_lower for phrase in active_phrases):
            return "Активные запросы и интерес к обучению"
        
        passive_phrases = ["не хочу", "не интересно", "скучно", "не готов"]
        if any(phrase in message_lower for phrase in passive_phrases):
            return "Низкая активность в диалоге"
        
        return None
    
    def _is_key_conversation_snippet(self, message: str) -> bool:
        """Определяет, является ли сообщение ключевым фрагментом"""
        # Сохраняем сообщения, содержащие упоминания тем, проблем или интересов
        key_indicators = [
            "не понимаю", "сложно", "интересно", "нравится", "не получается",
            "помоги", "объясни", "как решить"
        ]
        return any(indicator in message.lower() for indicator in key_indicators)
    
    def _generate_personalized_response(self, message: str, student_data: StudentAnalyticsData) -> str:
        """Генерирует персонализированный ответ на основе данных об ученике"""
        # Если ученик фрустрирован, снижаем сложность и добавляем поддержку
        if student_data.behavioral_traits.emotional_state == EmotionalTone.FRUSTRATED:
            return (
                "Понимаю, что это может быть сложно. Давай разберём это по шагам, "
                "начиная с более простого примера. Ты справишься!"
            )
        
        # Используем данные о слабых темах
        if student_data.academic_traits.weak_topics:
            weak_topics_str = ", ".join(student_data.academic_traits.weak_topics[-3:])
            if any(topic in message.lower() for topic in [t.lower() for t in student_data.academic_traits.weak_topics]):
                return (
                    f"Я вижу, что тебе нужна помощь с {weak_topics_str}. "
                    f"Давай разберём это вместе! Можешь выбрать формат: с картинкой, "
                    f"пошаговое объяснение или интерактивный пример."
                )
        
        # Используем стиль обучения
        if student_data.behavioral_traits.learning_style == LearningStyleType.VISUAL:
            if "график" not in message.lower() and "картинк" not in message.lower():
                return (
                    f"{message[:50]}... Хочешь, чтобы я показал это на графике или схеме? "
                    f"Визуальное представление часто помогает лучше понять!"
                )
        
        # Базовый ответ (будет дополнен в assistant service)
        return ""
    
    def _process_test_result(self, input_data: Dict[str, Any], student_data: StudentAnalyticsData) -> Dict[str, Any]:
        """Обрабатывает результат теста"""
        test_result = input_data.get('test_result', {})
        subject = test_result.get('subject', 'другое')
        accuracy = test_result.get('accuracy', 0)
        errors = test_result.get('errors', [])
        time_spent = test_result.get('time_spent_seconds')
        
        # Обновляем академические признаки
        student_data.academic_traits.test_accuracy = f"{accuracy}%"
        student_data.academic_traits.subject_levels[subject] = self._determine_level(accuracy)
        
        # Добавляем ошибки в слабые темы
        for error in errors:
            if error not in student_data.academic_traits.weak_topics:
                student_data.academic_traits.weak_topics.append(error)
            # Обновляем паттерны ошибок
            student_data.academic_traits.error_patterns[error] = \
                student_data.academic_traits.error_patterns.get(error, 0) + 1
        
        # Обновляем скорость выполнения
        if time_spent:
            if student_data.academic_traits.task_completion_speed:
                # Усредняем
                student_data.academic_traits.task_completion_speed = \
                    (student_data.academic_traits.task_completion_speed + time_spent) / 2
            else:
                student_data.academic_traits.task_completion_speed = time_spent
        
        # Обновляем метрики прогресса
        student_data.progress_metrics.test_results_dynamics.append({
            "subject": subject,
            "accuracy": accuracy,
            "timestamp": str(datetime.now()),
            "errors": errors
        })
        
        # Обновляем недельный/месячный прогресс
        now = datetime.now()
        week_key = f"{now.year}-W{now.isocalendar()[1]}"
        month_key = f"{now.year}-{now.month:02d}"
        
        student_data.progress_metrics.weekly_progress[week_key] = accuracy
        student_data.progress_metrics.monthly_progress[month_key] = accuracy
        
        student_data.last_updated = datetime.now()
        
        # Генерируем рефлексивный вопрос
        reflection_question = self._generate_reflection_question(test_result, student_data)
        
        return {
            "analytics_updated": True,
            "reflection_question": reflection_question,
            "personalized_suggestion": self._generate_test_suggestion(test_result, student_data)
        }
    
    def _process_task_attempt(self, input_data: Dict[str, Any], student_data: StudentAnalyticsData) -> Dict[str, Any]:
        """Обрабатывает попытку выполнения задания"""
        task_attempt = input_data.get('task_attempt', {})
        is_correct = task_attempt.get('is_correct', False)
        time_spent = task_attempt.get('time_spent_seconds')
        error_type = task_attempt.get('error_type')
        
        # Обновляем типичные ошибки
        if not is_correct and error_type:
            if error_type not in student_data.academic_traits.typical_errors:
                student_data.academic_traits.typical_errors.append(error_type)
            student_data.academic_traits.error_patterns[error_type] = \
                student_data.academic_traits.error_patterns.get(error_type, 0) + 1
        
        # Обновляем скорость
        if time_spent:
            if student_data.academic_traits.task_completion_speed:
                student_data.academic_traits.task_completion_speed = \
                    (student_data.academic_traits.task_completion_speed + time_spent) / 2
            else:
                student_data.academic_traits.task_completion_speed = time_spent
        
        student_data.last_updated = datetime.now()
        
        return {
            "analytics_updated": True,
            "suggestion": self._generate_task_suggestion(task_attempt, student_data)
        }
    
    def _determine_level(self, accuracy: float) -> str:
        """Определяет уровень знаний на основе точности"""
        if accuracy >= 80:
            return "продвинутый"
        elif accuracy >= 60:
            return "средний"
        else:
            return "начальный"
    
    def _generate_reflection_question(self, test_result: Dict[str, Any], 
                                     student_data: StudentAnalyticsData) -> str:
        """Генерирует рефлексивный вопрос после теста"""
        accuracy = test_result.get('accuracy', 0)
        
        if accuracy < 50:
            return "Как тебе эта задача? Было ли что-то непонятно? Может, стоит разобрать примеры вместе?"
        elif accuracy < 80:
            return "Неплохо! Есть моменты, которые можно улучшить. Хочешь разобрать ошибки?"
        else:
            return "Отлично справился! Готов к более сложным заданиям?"
    
    def _generate_test_suggestion(self, test_result: Dict[str, Any], 
                                 student_data: StudentAnalyticsData) -> str:
        """Генерирует персонализированное предложение после теста"""
        errors = test_result.get('errors', [])
        if errors:
            error_topic = errors[0]
            return (
                f"В прошлом тесте были ошибки в теме '{error_topic}'. "
                f"Давай разберём пример вместе? Можешь выбрать уровень сложности."
            )
        return "Отлично! Готов к новой теме?"
    
    def _generate_task_suggestion(self, task_attempt: Dict[str, Any], 
                                  student_data: StudentAnalyticsData) -> str:
        """Генерирует предложение после выполнения задания"""
        is_correct = task_attempt.get('is_correct', False)
        if not is_correct:
            error_type = task_attempt.get('error_type', 'ошибка')
            return f"Есть ошибка типа '{error_type}'. Хочешь попробовать ещё раз с подсказкой?"
        return "Правильно! Хочешь попробовать более сложное задание?"
    
    def _get_analytics_output(self, user_id: str) -> Dict[str, Any]:
        """Возвращает аналитические данные в формате JSON"""
        student_data = self._get_or_create_student_data(user_id)
        
        # Определяем стиль обучения для вывода
        learning_style_str = None
        if student_data.behavioral_traits.learning_style:
            learning_style_str = student_data.behavioral_traits.learning_style.value
        
        # Формируем уровень мотивации с доказательствами
        motivation_str = student_data.behavioral_traits.motivation_level.value
        if student_data.behavioral_traits.motivation_evidence:
            motivation_str += f" ({', '.join(student_data.behavioral_traits.motivation_evidence[-2:])})"
        
        return {
            "student_id": user_id,
            "academic_traits": {
                "math_level": student_data.academic_traits.subject_levels.get("математика", "не определен"),
                "weak_topics": student_data.academic_traits.weak_topics,
                "test_accuracy": student_data.academic_traits.test_accuracy,
                "typical_errors": student_data.academic_traits.typical_errors,
                "task_completion_speed": student_data.academic_traits.task_completion_speed
            },
            "behavioral_traits": {
                "learning_style": learning_style_str,
                "motivation_level": motivation_str,
                "emotional_state": student_data.behavioral_traits.emotional_state.value,
                "interaction_style": student_data.behavioral_traits.interaction_style
            },
            "progress_metrics": {
                "hint_requests_frequency": student_data.progress_metrics.hint_requests_frequency,
                "weekly_progress": student_data.progress_metrics.weekly_progress,
                "monthly_progress": student_data.progress_metrics.monthly_progress,
                "improvement_areas": student_data.progress_metrics.improvement_areas,
                "strengths": student_data.progress_metrics.strengths
            },
            "data_collection_enabled": student_data.data_collection_enabled,
            "total_interactions": student_data.total_interactions
        }
    
    def record_hint_request(self, user_id: str):
        """Записывает запрос подсказки"""
        student_data = self._get_or_create_student_data(user_id)
        student_data.progress_metrics.hint_requests_frequency += 1
        student_data.progress_metrics.hint_requests_history.append(datetime.now())
        student_data.last_updated = datetime.now()
    
    def get_student_data(self, user_id: str) -> Optional[StudentAnalyticsData]:
        """Получить данные об ученике"""
        return self.student_data.get(user_id)








