"""
Оркестратор агентов
Координирует взаимодействие между агентами
"""
from typing import Dict, Any, Optional
from .error_analyzer_agent import ErrorAnalyzerAgent
from .profiler_agent import ProfilerAgent
from .task_generator_agent import TaskGeneratorAgent
from .mentor_agent import MentorAgent
from .teacher_analytics_agent import TeacherAnalyticsAgent
from models.cognitive_profile import TaskAttempt, ErrorTag


class AgentOrchestrator:
    """
    Координирует работу всех агентов
    """
    
    def __init__(self):
        self.error_analyzer = ErrorAnalyzerAgent()
        self.profiler = ProfilerAgent()
        self.task_generator = TaskGeneratorAgent()
        self.mentor = MentorAgent()
        self.teacher_analytics = TeacherAnalyticsAgent()
    
    def process_task_submission(self, user_id: str, task_id: int, question: str, 
                                user_answer: int, correct_answer: int) -> Dict[str, Any]:
        """
        Обрабатывает отправку задания учеником
        
        Returns:
        - is_correct: правильность ответа
        - error_analysis: анализ ошибки
        - mentor_message: сообщение от наставника
        - updated_profile: обновленный профиль
        """
        # Проверяем ответ
        is_correct = user_answer == correct_answer
        
        # Создаем попытку выполнения
        task_attempt = TaskAttempt(
            task_id=task_id,
            question=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct
        )
        
        # Анализируем ошибку
        error_analysis = None
        if not is_correct:
            error_analysis = self.error_analyzer.process({
                'task_id': task_id,
                'question': question,
                'user_answer': user_answer,
                'correct_answer': correct_answer
            })
        
        # Получаем профиль (создается автоматически если не существует)
        profile = self.profiler.get_profile(user_id)
        
        # Обновляем профиль
        profile_result = self.profiler.process({
            'user_id': user_id,
            'task_attempt': task_attempt,
            'error_analysis': error_analysis
        })
        
        # Получаем обновленный профиль
        profile = self.profiler.get_profile(user_id)
        
        # Получаем сообщение от наставника
        mentor_message = self.mentor.process({
            'user_id': user_id,
            'profile': profile,
            'task_result': 'correct' if is_correct else 'wrong'
        })
        
        return {
            'is_correct': is_correct,
            'error_analysis': error_analysis,
            'mentor_message': mentor_message,
            'updated_profile': profile_result,
            'correct_answer': correct_answer
        }
    
    def generate_personalized_tasks(self, user_id: str, topic: str = "general", count: int = 3) -> Dict[str, Any]:
        """Генерирует персонализированные задания для ученика"""
        # Получаем профиль (создается автоматически если не существует)
        profile = self.profiler.get_profile(user_id)
        
        tasks = self.task_generator.process({
            'user_id': user_id,
            'profile': profile,
            'topic': topic,
            'count': count
        })
        
        return tasks
    
    def get_student_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Получает данные для дашборда ученика"""
        profile = self.profiler.get_profile(user_id)
        
        if not profile:
            return {'error': 'Profile not found'}
        
        # Генерируем персонализированное сообщение
        mentor_message = self.mentor.process({
            'user_id': user_id,
            'profile': profile,
            'task_result': 'progress'
        })
        
        return {
            'profile': {
                'user_id': profile.user_id,
                'accuracy_rate': profile.accuracy_rate,
                'total_tasks_completed': profile.total_tasks_completed,
                'correct_tasks_count': profile.correct_tasks_count,
                'level': profile.level,
                'points': profile.points,
                'achievements': profile.achievements,
                'current_emotional_state': profile.current_emotional_state.value if profile.current_emotional_state else None
            },
            'recent_tasks': profile.task_history[-10:] if len(profile.task_history) > 10 else profile.task_history,
            'error_patterns': dict(sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:5]),
            'mentor_message': mentor_message
        }
    
    def get_teacher_report(self, class_id: str = None, report_type: str = 'summary') -> Dict[str, Any]:
        """Получает отчет для учителя"""
        # Здесь можно добавить логику для получения профилей класса
        return self.teacher_analytics.process({
            'class_id': class_id,
            'report_type': report_type
        })
    
    def assign_task_to_student(self, user_id: str, topic: str, task_ids: list):
        """Назначает задания ученику"""
        profile = self.profiler.get_profile(user_id)
        
        if not profile:
            profile = self.profiler.profiles[user_id] = self.profiler.process({'user_id': user_id})['profile']
        
        if topic not in profile.assigned_tasks:
            profile.assigned_tasks[topic] = []
        
        profile.assigned_tasks[topic].extend(task_ids)
        
        return {'status': 'tasks_assigned', 'assigned_tasks': profile.assigned_tasks}

