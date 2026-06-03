"""Парсинг и сопоставление математических ответов (числа, интервалы, неравенства)."""
from typing import Optional, Tuple
import re


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
    # Поддерживаем интервалы и цепочки неравенств как "числовые" ответы.
    if interval_answers_equal(user_answer, correct_answer, tolerance=tolerance):
        return True

    u = parse_numeric_answer(user_answer)
    c = parse_numeric_answer(correct_answer)
    if u is not None and c is not None:
        return abs(u - c) < tolerance
    return False


def _parse_interval_bound(raw: str) -> Optional[float]:
    return parse_numeric_answer(str(raw).strip())


def _parse_interval_answer(s: str) -> Optional[Tuple[float, bool, float, bool]]:
    """
    Возвращает интервал в виде:
    (left_value, left_inclusive, right_value, right_inclusive)
    Поддержка форм:
    - 1<x<1.5
    - 1<=x<1.5
    - x∈(1;1.5), (1,1.5), [1;1.5]
    """
    if not s or not isinstance(s, str):
        return None

    t = s.strip().lower()
    t = t.replace(" ", "")
    t = t.replace("≤", "<=").replace("≥", ">=")
    t = t.replace("x∈", "")
    t = t.replace("xin", "")
    t = t.replace("x∊", "")

    # Формат интервала: (a;b), [a;b], (a,b), [a,b]
    m = re.match(r"^([\(\[])\s*([\-]?\d+(?:[.,]\d+)?(?:/[\-]?\d+(?:[.,]\d+)?)?)\s*[;,]\s*([\-]?\d+(?:[.,]\d+)?(?:/[\-]?\d+(?:[.,]\d+)?)?)\s*([\)\]])$", t)
    if m:
        left_val = _parse_interval_bound(m.group(2))
        right_val = _parse_interval_bound(m.group(3))
        if left_val is None or right_val is None:
            return None
        return (
            left_val,
            m.group(1) == "[",
            right_val,
            m.group(4) == "]",
        )

    # Цепочка неравенств: a<x<b / a<=x<=b
    m = re.match(
        r"^([\-]?\d+(?:[.,]\d+)?(?:/[\-]?\d+(?:[.,]\d+)?)?)(<=|<)(?:x|y|t)(<=|<)([\-]?\d+(?:[.,]\d+)?(?:/[\-]?\d+(?:[.,]\d+)?)?)$",
        t,
    )
    if m:
        left_val = _parse_interval_bound(m.group(1))
        right_val = _parse_interval_bound(m.group(4))
        if left_val is None or right_val is None:
            return None
        return (
            left_val,
            m.group(2) == "<=",
            right_val,
            m.group(3) == "<=",
        )

    return None


def interval_answers_equal(user_answer: str, correct_answer: str, tolerance: float = 0.001) -> bool:
    """Проверяет эквивалентность интервалов и цепочек неравенств."""
    u = _parse_interval_answer(user_answer)
    c = _parse_interval_answer(correct_answer)
    if not u or not c:
        return False

    u_left, u_left_inc, u_right, u_right_inc = u
    c_left, c_left_inc, c_right, c_right_inc = c

    return (
        abs(u_left - c_left) < tolerance
        and abs(u_right - c_right) < tolerance
        and u_left_inc == c_left_inc
        and u_right_inc == c_right_inc
    )


def math_answers_equal(user_answer: str, correct_answer: str, tolerance: float = 0.001) -> bool:
    """
    Универсальная проверка для коротких математических ответов:
    1) интервалы/неравенства
    2) числа/дроби
    3) fallback по нормализованной строке
    """
    if interval_answers_equal(user_answer, correct_answer, tolerance=tolerance):
        return True
    if numeric_answers_equal(user_answer, correct_answer, tolerance=tolerance):
        return True

    u = str(user_answer or "").strip().lower().replace(" ", "")
    c = str(correct_answer or "").strip().lower().replace(" ", "")
    return u == c and u != ""
