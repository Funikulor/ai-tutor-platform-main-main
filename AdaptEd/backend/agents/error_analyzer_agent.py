"""
Агент анализа ошибок
Анализирует ответы ученика и определяет тип ошибки
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from models.cognitive_profile import ErrorTag, ErrorAnalysis
import re


class ErrorAnalyzerAgent(BaseAgent):
    """
    Анализирует ошибки ученика и определяет их тип
    """
    
    def __init__(self):
        super().__init__("ErrorAnalyzer")
        # Шаблоны для определения типа ошибки
        self.error_patterns = {
            ErrorTag.MISSING_FORMULA: [
                "нет формулы",
                "не использована формула",
                "пропущено применение правила"
            ],
            ErrorTag.CONCEPT_CONFUSION: [
                "перепутано",
                "неправильный принцип",
                "неверная концепция"
            ],
            ErrorTag.CARELESSNESS: [
                "незначительная ошибка",
                "описка",
                "неправильный знак"
            ],
            ErrorTag.LOGIC_GAP: [
                "пробел в логике",
                "неверный ход мысли",
                "логическая ошибка"
            ],
            ErrorTag.CALCULATION_ERROR: [
                "ошибка вычисления",
                "неправильный подсчет",
                "арифметическая ошибка"
            ]
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует ответ ученика
        
        Input:
        - task_id: ID задания
        - question: текст вопроса
        - user_answer: ответ ученика
        - correct_answer: правильный ответ
        - task_category: категория задания
        
        Output:
        - error_type: тип ошибки
        - justification: обоснование
        - suggested_remediation: рекомендация
        """
        self.log(f"Analyzing error for task {input_data.get('task_id')}")
        
        user_answer = input_data.get('user_answer')
        correct_answer = input_data.get('correct_answer')
        question = input_data.get('question', '')
        
        # Если ответ правильный - нет ошибки
        if user_answer == correct_answer:
            return {
                "has_error": False,
                "error_type": None,
                "justification": "Правильный ответ"
            }
        
        # Анализ ошибки
        error_analysis = self._analyze_error_type(user_answer, correct_answer, question)
        
        # Генерация рекомендации
        suggestion = self._generate_suggestion(error_analysis['error_type'])
        
        result = {
            "has_error": True,
            **error_analysis,
            "suggested_remediation": suggestion
        }
        
        self.log(f"Error analysis complete: {result['error_type']}")
        return result
    
    def _analyze_error_type(self, user_answer: int, correct_answer: int, question: str) -> Dict[str, Any]:
        """Определяет тип ошибки на основе разницы между ответами"""
        
        difference = abs(user_answer - correct_answer)
        
        # Анализ по разнице
        if difference == 1:
            error_type = ErrorTag.CARELESSNESS
            justification = "Незначительная ошибка на единицу. Вероятно, описка в вычислении."
        elif difference > user_answer * 0.5:  # Большая разница
            error_type = ErrorTag.LOGIC_GAP
            justification = "Существенная ошибка в логике решения."
        elif difference % 10 == 0:  # Ошибка в разряде
            error_type = ErrorTag.CARELESSNESS
            justification = "Ошибка в разряде числа."
        else:
            # Проверка на арифметическую ошибку
            if "+" in question or "-" in question or "*" in question or "/" in question:
                error_type = ErrorTag.CALCULATION_ERROR
                justification = "Ошибка в арифметических вычислениях."
            elif "/" in question:
                error_type = ErrorTag.MISSING_FORMULA
                justification = "Не использована правильная формула или метод решения."
            else:
                error_type = ErrorTag.CONCEPT_CONFUSION
                justification = "Неправильное понимание концепции задачи."
        
        return {
            "error_type": error_type.value,
            "justification": justification
        }
    
    def _generate_suggestion(self, error_type: str) -> str:
        """Генерирует рекомендацию по исправлению ошибки"""
        suggestions = {
            ErrorTag.CARELESSNESS: "Будьте внимательнее при вычислениях. Проверяйте ответ перед отправкой.",
            ErrorTag.CALCULATION_ERROR: "Потренируйтесь в арифметических операциях. Возможно, стоит вернуться к основам.",
            ErrorTag.MISSING_FORMULA: "Повторите основные формулы и методы решения подобных задач.",
            ErrorTag.CONCEPT_CONFUSION: "Изучите базовую концепцию темы. Разберите примеры пошагового решения.",
            ErrorTag.LOGIC_GAP: "Разберите логику решения задачи по шагам. Возможно, стоит начать с более простых задач."
        }
        
        return suggestions.get(error_type, "Продолжайте практиковаться. Ошибки - это часть обучения!")

