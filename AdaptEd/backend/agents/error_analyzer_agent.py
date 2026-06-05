"""
Агент анализа ошибок
Определяет тип ошибки ученика.

Гибридная стратегия:
- числовые ответы (например, 42 vs 41) → быстрые детерминированные эвристики
  по разнице ответов (без обращения к LLM);
- нечисловые ответы (интервалы 1<x<1.5, несколько корней, уравнения, текст)
  → классификация через LLM со строгим JSON; если LLM недоступен или вернул
  некорректный результат — откатываемся на эвристики.
"""
import json
import os
import re
from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from models.cognitive_profile import ErrorTag, ErrorAnalysis


# Допустимые теги для LLM-классификации (значения ErrorTag)
_VALID_TAGS = {
    ErrorTag.MISSING_FORMULA.value,
    ErrorTag.CONCEPT_CONFUSION.value,
    ErrorTag.CARELESSNESS.value,
    ErrorTag.LOGIC_GAP.value,
    ErrorTag.CALCULATION_ERROR.value,
}


class ErrorAnalyzerAgent(BaseAgent):
    """
    Анализирует ошибки ученика и определяет их тип
    """

    def __init__(self):
        super().__init__("ErrorAnalyzer")
        # LLM-классификацию можно отключить переменной окружения (для офлайна/демо)
        self.use_llm = os.getenv("ERROR_ANALYSIS_USE_LLM", "1").lower() not in ("0", "false", "no")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует ответ ученика

        Input:
        - task_id: ID задания
        - question: текст вопроса
        - user_answer: ответ ученика
        - correct_answer: правильный ответ

        Output:
        - has_error: была ли ошибка
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

        # Гибрид: числовые ответы разбираем эвристиками, остальное — через LLM
        if self.use_llm and not self._is_numeric_pair(user_answer, correct_answer):
            error_analysis = self._classify_with_llm(user_answer, correct_answer, question)
            if error_analysis is None:
                error_analysis = self._analyze_error_type(user_answer, correct_answer, question)
            else:
                self.log("Тип ошибки определён через LLM")
        else:
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

    def _is_numeric_pair(self, user_answer: Any, correct_answer: Any) -> bool:
        """Оба ответа парсятся как числа? Тогда эвристики по разнице надёжны."""
        try:
            float(str(user_answer).strip())
            float(str(correct_answer).strip())
            return True
        except (ValueError, TypeError):
            return False

    def _classify_with_llm(
        self, user_answer: Any, correct_answer: Any, question: str
    ) -> Optional[Dict[str, Any]]:
        """
        Классифицирует ошибку через LLM. Возвращает {error_type, justification}
        или None, если LLM недоступен / вернул некорректный ответ (→ фолбэк на эвристики).
        """
        # Ленивый импорт, чтобы избежать циклической зависимости с services.assistant
        try:
            from services.assistant import (
                get_assistant_service,
                assistant_response_means_llm_down,
            )
        except Exception:
            return None

        prompt = (
            "Ты — учитель математики. Определи ТИП ошибки ученика по его ответу.\n"
            f"Задача: {question}\n"
            f"Правильный ответ: {correct_answer}\n"
            f"Ответ ученика: {user_answer}\n\n"
            "Выбери РОВНО один тип из списка:\n"
            "- missing_formula — не применил нужную формулу или метод решения\n"
            "- concept_confusion — не понял понятие или тему\n"
            "- carelessness — невнимательность, описка при верном методе\n"
            "- logic_gap — пропущен шаг или корень, ошибка в логике решения\n"
            "- calculation_error — арифметическая ошибка в вычислениях\n\n"
            "Ответ строго в JSON без текста до и после: "
            '{"error_type": "<один_из_типов>", "justification": "<кратко по-русски, одно предложение>"}'
        )

        try:
            assistant = get_assistant_service()
            raw = assistant._generate(prompt, max_new_tokens=160, sanitize_output=False)
        except Exception as e:
            self.log(f"LLM-классификация недоступна: {e}", level="WARN")
            return None

        if not raw or assistant_response_means_llm_down(raw):
            return None

        parsed = self._parse_llm_json(raw)
        if not parsed:
            return None

        error_type = str(parsed.get("error_type", "")).strip().lower()
        if error_type not in _VALID_TAGS:
            return None

        justification = str(parsed.get("justification", "")).strip()
        if not justification:
            justification = "Тип ошибки определён по разбору ответа."

        return {"error_type": error_type, "justification": justification}

    def _parse_llm_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """Достаёт JSON-объект из ответа LLM (терпимо к тексту вокруг)."""
        if not raw:
            return None
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        candidate = match.group(0) if match else raw
        try:
            data = json.loads(candidate)
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _analyze_error_type(self, user_answer: str, correct_answer: str, question: str) -> Dict[str, Any]:
        """Определяет тип ошибки эвристически по разнице между ответами (фолбэк)."""

        # Пытаемся сравнить как числа
        try:
            user_num = float(str(user_answer).strip())
            correct_num = float(str(correct_answer).strip())
            difference = abs(user_num - correct_num)
        except (ValueError, TypeError):
            # Если не числа, сравниваем как строки
            difference = 0 if str(user_answer).strip().lower() == str(correct_answer).strip().lower() else 999

        # Анализ по разнице (для числовых ответов)
        if difference < 0.01:  # Ответы совпадают (для чисел)
            error_type = ErrorTag.CARELESSNESS
            justification = "Ответы очень близки, возможно небольшая описка."
        elif difference == 999:  # Строковые ответы не совпадают
            # Анализируем строковые ответы
            user_lower = str(user_answer).strip().lower()
            correct_lower = str(correct_answer).strip().lower()

            # Проверяем, есть ли общие части
            if any(word in correct_lower for word in user_lower.split() if len(word) > 2):
                error_type = ErrorTag.CARELESSNESS
                justification = "Ответ частично правильный, но есть неточности в формулировке."
            elif "x" in question.lower() or "=" in question:
                error_type = ErrorTag.MISSING_FORMULA
                justification = "Не использована правильная формула или метод решения уравнения."
            else:
                error_type = ErrorTag.CONCEPT_CONFUSION
                justification = "Неправильное понимание концепции задачи."
        elif difference == 1:
            error_type = ErrorTag.CARELESSNESS
            justification = "Незначительная ошибка на единицу. Вероятно, описка в вычислении."
        elif difference > 10:  # Большая разница
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
