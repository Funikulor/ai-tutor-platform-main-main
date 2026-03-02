"""Парсинг числовых ответов (дроби и десятичные) для единой проверки правильности."""
from typing import Optional


def parse_numeric_answer(s: str) -> Optional[float]:
    """Парсит число из строки: десятичное (0.5, 3.375) или дробь (1/2, 27/8)."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip().replace(",", ".")
    if "/" in s:
        parts = s.split("/", 1)
        if len(parts) == 2:
            try:
                a, b = float(parts[0].strip()), float(parts[1].strip())
                if b != 0:
                    return a / b
            except (ValueError, TypeError):
                pass
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def numeric_answers_equal(user_answer: str, correct_answer: str, tolerance: float = 0.001) -> bool:
    """Считает ответ верным, если оба числа и разница в пределах tolerance (3.375 и 27/8 — да)."""
    u = parse_numeric_answer(user_answer)
    c = parse_numeric_answer(correct_answer)
    if u is not None and c is not None:
        return abs(u - c) < tolerance
    return False
