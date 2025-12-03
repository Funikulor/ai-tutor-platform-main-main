"""
Агент аналитики для учителя
Агрегирует данные класса и формирует отчеты
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from models.cognitive_profile import CognitiveProfile


class TeacherAnalyticsAgent(BaseAgent):
    """
    Генерирует аналитику для учителя
    """
    
    def __init__(self):
        super().__init__("TeacherAnalytics")
        self.class_profiles: Dict[str, List[CognitiveProfile]] = {}  # class_id -> [profiles]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует отчет для учителя
        
        Input:
        - class_id: ID класса (опционально)
        - user_ids: список ID учеников (опционально)
        - report_type: тип отчета (summary, detailed, struggling)
        
        Output:
        - report: отчет с аналитикой
        """
        self.log(f"Generating analytics report")
        
        report_type = input_data.get('report_type', 'summary')
        class_id = input_data.get('class_id')
        user_ids = input_data.get('user_ids', [])
        
        # Собираем данные профилей
        profiles = self._collect_profiles(class_id, user_ids)
        
        if not profiles:
            return {"error": "No student data available"}
        
        # Генерируем отчет в зависимости от типа
        if report_type == 'summary':
            report = self._generate_summary_report(profiles)
        elif report_type == 'detailed':
            report = self._generate_detailed_report(profiles)
        elif report_type == 'struggling':
            report = self._generate_struggling_students_report(profiles)
        else:
            report = self._generate_summary_report(profiles)
        
        return report
    
    def _collect_profiles(self, class_id: str = None, user_ids: List[str] = []) -> List[CognitiveProfile]:
        """Собирает профили учеников"""
        # В реальной реализации здесь будет запрос к базе данных
        # Сейчас возвращаем заглушку
        return []
    
    def _generate_summary_report(self, profiles: List[CognitiveProfile]) -> Dict[str, Any]:
        """Генерирует сводный отчет по классу"""
        total_students = len(profiles)
        
        if total_students == 0:
            return {"error": "No students in class"}
        
        # Общая статистика
        total_tasks = sum(p.total_tasks_completed for p in profiles)
        avg_accuracy = sum(p.accuracy_rate for p in profiles) / total_students
        
        # Уровни
        level_distribution = {}
        for profile in profiles:
            level = profile.level
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # Распределение достижений
        most_common_errors = self._get_class_common_errors(profiles)
        
        return {
            "report_type": "summary",
            "class_statistics": {
                "total_students": total_students,
                "total_tasks_completed": total_tasks,
                "average_accuracy": round(avg_accuracy, 2),
                "level_distribution": level_distribution
            },
            "common_challenges": most_common_errors,
            "recommendations": self._generate_class_recommendations(profiles)
        }
    
    def _generate_detailed_report(self, profiles: List[CognitiveProfile]) -> Dict[str, Any]:
        """Генерирует детальный отчет"""
        summary = self._generate_summary_report(profiles)
        
        # Добавляем индивидуальные профили
        individual_profiles = []
        for profile in profiles:
            individual_profiles.append({
                "user_id": profile.user_id,
                "accuracy_rate": round(profile.accuracy_rate, 2),
                "total_tasks": profile.total_tasks_completed,
                "level": profile.level,
                "points": profile.points,
                "achievements": profile.achievements,
                "most_common_errors": dict(sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:3]),
                "current_emotional_state": profile.current_emotional_state.value if profile.current_emotional_state else None
            })
        
        return {
            **summary,
            "individual_profiles": individual_profiles
        }
    
    def _generate_struggling_students_report(self, profiles: List[CognitiveProfile]) -> Dict[str, Any]:
        """Выявляет отстающих учеников"""
        struggling_students = []
        
        for profile in profiles:
            # Критерии отставания
            is_struggling = (
                profile.accuracy_rate < 50 or  # Низкая точность
                len(profile.task_history) > 10 and profile.total_tasks_completed < 5 or  # Мало выполненных заданий
                any(count > 5 for count in profile.error_frequency.values())  # Частые ошибки
            )
            
            if is_struggling:
                struggling_students.append({
                    "user_id": profile.user_id,
                    "accuracy_rate": round(profile.accuracy_rate, 2),
                    "most_common_errors": dict(sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:3]),
                    "recommendations": self._generate_student_recommendations(profile)
                })
        
        return {
            "report_type": "struggling_students",
            "struggling_count": len(struggling_students),
            "students": struggling_students,
            "intervention_suggestions": self._generate_intervention_suggestions(struggling_students)
        }
    
    def _get_class_common_errors(self, profiles: List[CognitiveProfile]) -> Dict[str, int]:
        """Получает самые частые ошибки в классе"""
        class_errors = {}
        for profile in profiles:
            for error_type, count in profile.error_frequency.items():
                class_errors[error_type] = class_errors.get(error_type, 0) + count
        
        return dict(sorted(class_errors.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def _generate_class_recommendations(self, profiles: List[CognitiveProfile]) -> List[Dict[str, Any]]:
        """Генерирует рекомендации для класса"""
        recommendations = []
        
        class_errors = self._get_class_common_errors(profiles)
        if class_errors:
            top_error = list(class_errors.keys())[0]
            recommendations.append({
                "priority": "high",
                "topic": f"Тема связанная с ошибкой: {top_error}",
                "action": f"Провести дополнительное занятие по теме, так как {class_errors[top_error]} ошибок этого типа"
            })
        
        avg_accuracy = sum(p.accuracy_rate for p in profiles) / len(profiles)
        if avg_accuracy < 60:
            recommendations.append({
                "priority": "medium",
                "topic": "Общее укрепление основ",
                "action": "Рекомендуется провести факультатив по базовым операциям"
            })
        
        return recommendations
    
    def _generate_student_recommendations(self, profile: CognitiveProfile) -> List[str]:
        """Генерирует рекомендации для конкретного ученика"""
        recommendations = []
        
        if profile.accuracy_rate < 40:
            recommendations.append("Основы математики требуют закрепления")
        
        if profile.error_frequency:
            top_error = max(profile.error_frequency.items(), key=lambda x: x[1])
            recommendations.append(f"Частая ошибка: {top_error[0]}. Требуется дополнительная практика.")
        
        if profile.task_history and len(profile.task_history) < 10:
            recommendations.append("Недостаточно практики. Рекомендуется больше заданий.")
        
        return recommendations
    
    def _generate_intervention_suggestions(self, struggling_students: List[Dict]) -> List[Dict[str, Any]]:
        """Генерирует предложения по вмешательству"""
        suggestions = []
        
        if len(struggling_students) > 5:
            suggestions.append({
                "type": "group_support",
                "description": f"В классе {len(struggling_students)} учеников требуют дополнительной поддержки. Рекомендуется групповое занятие."
            })
        
        for student in struggling_students:
            if student['accuracy_rate'] < 30:
                suggestions.append({
                    "type": "individual_support",
                    "student": student['user_id'],
                    "description": "Требуется индивидуальная поддержка и консультация"
                })
        
        return suggestions

