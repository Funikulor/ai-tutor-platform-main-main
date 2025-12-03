"""
Агент генерации заданий
Создает персонализированные задания на основе профиля ученика
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from models.cognitive_profile import CognitiveProfile, ErrorTag


class TaskGeneratorAgent(BaseAgent):
    """
    Генерирует персонализированные задания для ученика
    """
    
    def __init__(self):
        super().__init__("TaskGenerator")
        # База заданий по темам
        self.task_bank = self._initialize_task_bank()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует задания для ученика
        
        Input:
        - user_id: ID ученика
        - profile: CognitiveProfile ученика
        - topic: тема задания (опционально)
        - count: количество заданий (по умолчанию 1-3)
        
        Output:
        - tasks: список персонализированных заданий
        """
        self.log(f"Generating tasks for user {input_data.get('user_id')}")
        
        profile = input_data.get('profile')
        topic = input_data.get('topic', 'general')
        count = input_data.get('count', 3)
        
        # Определяем уровень сложности на основе профиля
        difficulty = self._determine_difficulty(profile)
        
        # Получаем типичные ошибки ученика
        common_errors = self._get_common_errors(profile)
        
        # Генерируем задания
        tasks = self._generate_personalized_tasks(topic, difficulty, common_errors, count)
        
        return {
            "tasks": tasks,
            "difficulty": difficulty,
            "reasoning": f"Сгенерировано {len(tasks)} заданий уровня {difficulty} с учетом типичных ошибок ученика"
        }
    
    def _initialize_task_bank(self) -> Dict[str, List[Dict]]:
        """Инициализация базы заданий"""
        return {
            "addition": [
                {"question": "15 + 8", "answer": 23, "level": "beginner"},
                {"question": "47 + 56", "answer": 103, "level": "intermediate"},
                {"question": "234 + 567", "answer": 801, "level": "advanced"},
            ],
            "subtraction": [
                {"question": "20 - 7", "answer": 13, "level": "beginner"},
                {"question": "85 - 29", "answer": 56, "level": "intermediate"},
                {"question": "1000 - 345", "answer": 655, "level": "advanced"},
            ],
            "multiplication": [
                {"question": "6 × 7", "answer": 42, "level": "beginner"},
                {"question": "13 × 5", "answer": 65, "level": "intermediate"},
                {"question": "23 × 15", "answer": 345, "level": "advanced"},
            ],
            "division": [
                {"question": "24 ÷ 4", "answer": 6, "level": "beginner"},
                {"question": "81 ÷ 9", "answer": 9, "level": "intermediate"},
                {"question": "156 ÷ 12", "answer": 13, "level": "advanced"},
            ],
            "mixed": [
                {"question": "15 + 8 - 5", "answer": 18, "level": "intermediate"},
                {"question": "6 × 3 + 10", "answer": 28, "level": "intermediate"},
                {"question": "(10 + 5) × 2", "answer": 30, "level": "advanced"},
                {"question": "50 - (20 + 10)", "answer": 20, "level": "advanced"},
            ],
        }
    
    def _determine_difficulty(self, profile: CognitiveProfile) -> str:
        """Определяет уровень сложности для ученика"""
        if not profile.task_history:
            return "beginner"
        
        # Анализируем последние задачи
        recent_tasks = profile.task_history[-10:] if len(profile.task_history) >= 10 else profile.task_history
        accuracy = sum(1 for t in recent_tasks if t.is_correct) / len(recent_tasks) if recent_tasks else 0
        
        if accuracy >= 0.8:
            return "advanced"
        elif accuracy >= 0.6:
            return "intermediate"
        else:
            return "beginner"
    
    def _get_common_errors(self, profile: CognitiveProfile) -> List[str]:
        """Получает список типичных ошибок ученика"""
        if not profile.error_frequency:
            return []
        
        # Сортируем ошибки по частоте
        sorted_errors = sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)
        return [error[0] for error in sorted_errors[:3]]
    
    def _generate_personalized_tasks(self, topic: str, difficulty: str, common_errors: List[str], count: int) -> List[Dict]:
        """Генерирует персонализированные задания"""
        tasks = []
        
        # Выбираем категорию заданий
        category = topic if topic in self.task_bank else "mixed"
        
        # Фильтруем по уровню сложности
        available_tasks = [
            task for task in self.task_bank.get(category, [])
            if task["level"] == difficulty
        ]
        
        # Если нет задач нужного уровня, берем ближайший
        if not available_tasks:
            for level in ["beginner", "intermediate", "advanced"]:
                available_tasks = [
                    task for task in self.task_bank.get(category, [])
                    if task["level"] == level
                ]
                if available_tasks:
                    break
        
        # Генерируем задания
        import random
        selected_tasks = random.sample(available_tasks, min(count, len(available_tasks)))
        
        # Добавляем ID и другие метаданные
        for i, task in enumerate(selected_tasks):
            tasks.append({
                "id": len(tasks) + 1000,  # Генерируем ID
                "question": task["question"],
                "correct_answer": task["answer"],
                "category": category,
                "difficulty": difficulty,
                "targeted_errors": common_errors,
                "hint": self._generate_hint(task["question"], common_errors)
            })
        
        return tasks
    
    def _generate_hint(self, question: str, common_errors: List[str]) -> str:
        """Генерирует подсказку с учетом типичных ошибок"""
        hints = {
            ErrorTag.CARELESSNESS: "Будьте внимательны при вычислениях. Проверьте ответ.",
            ErrorTag.CALCULATION_ERROR: "Выполняйте вычисления пошагово.",
            ErrorTag.MISSING_FORMULA: "Помните о порядке операций: умножение и деление выполняются перед сложением и вычитанием.",
            ErrorTag.CONCEPT_CONFUSION: "Разберите задачу на части и решайте пошагово.",
            ErrorTag.LOGIC_GAP: "Подумайте о логике задачи. Что нужно найти? Как связаны данные?"
        }
        
        if common_errors and common_errors[0] in hints:
            return hints[common_errors[0]]
        
        return "Решайте задачу внимательно и проверяйте свой ответ."

