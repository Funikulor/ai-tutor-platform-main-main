"""
API маршруты для работы с ИИ-агентами
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re
import random
from utils.orchestrator_singleton import get_orchestrator

router = APIRouter()
orchestrator = get_orchestrator()


from utils.answer_parse import parse_numeric_answer as _parse_numeric_answer


class TaskSubmission(BaseModel):
    """Модель для отправки задания"""
    user_id: str
    task_id: int
    question: str
    user_answer: str  # Может быть строкой для разных типов заданий
    correct_answer: str
    topic: Optional[str] = None
    time_spent_seconds: Optional[int] = None


class TaskGenerationRequest(BaseModel):
    """Запрос на генерацию заданий"""
    user_id: str
    topic: Optional[str] = "general"
    count: Optional[int] = 3
    use_thematic: Optional[bool] = False  # Использовать тематические задания (с воображением)


class TaskAssignment(BaseModel):
    """Назначение заданий ученику"""
    user_id: str
    topic: str
    task_ids: List[int]


@router.post("/agents/submit-task", response_model=Dict[str, Any])
async def submit_task(submission: TaskSubmission):
    """
    Отправка задания учеником
    
    Возвращает:
    - Анализ ошибки (если есть)
    - Сообщение от наставника
    - Обновленный профиль ученика
    - Объяснение задания (если передано)
    """
    try:
        # Определяем правильность ответа (с учетом разных типов заданий)
        is_correct = submission.user_answer.lower().strip() == submission.correct_answer.lower().strip()

        # Числовые ответы: поддерживаем дроби (1/2, 3/4) и десятичные (0.5)
        user_num = _parse_numeric_answer(submission.user_answer)
        correct_num = _parse_numeric_answer(submission.correct_answer)
        if user_num is not None and correct_num is not None:
            is_correct = abs(user_num - correct_num) < 0.001  # Допуск для числовых ответов
        
        # Обрабатываем через orchestrator
        effective_topic = (submission.topic or "").strip() or "Адаптивные задания"
        result = orchestrator.process_task_submission(
            user_id=submission.user_id,
            task_id=submission.task_id,
            question=submission.question,
            user_answer=submission.user_answer,
            correct_answer=submission.correct_answer,
            topic=effective_topic,
            time_spent_seconds=submission.time_spent_seconds,
            verified_is_correct=is_correct,
        )
        
        # Также сохраняем в аналитику
        try:
            from services.student_analytics import get_analytics_service
            analytics_service = get_analytics_service()
            profile = orchestrator.profiler.get_profile(submission.user_id)
            
            task_attempt = {
                "is_correct": is_correct,
                "time_spent_seconds": submission.time_spent_seconds,
                "topic": submission.topic or "общая"
            }
            
            analytics_service.process_task_attempt(
                user_id=submission.user_id,
                task_attempt=task_attempt,
                cognitive_profile=profile
            )
        except Exception as e:
            print(f"Error saving to analytics: {e}")

        # Добавляем объяснение, если оно передано в запросе
        explanation = getattr(submission, 'explanation', None)
        
        return {
            **result,
            "is_correct": is_correct,
            "explanation": explanation  # Передаем объяснение из запроса
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/generate-tasks", response_model=Dict[str, Any])
async def generate_tasks(request: TaskGenerationRequest):
    """
    Генерация персонализированных заданий для ученика
    """
    try:
        result = orchestrator.generate_personalized_tasks(
            user_id=request.user_id,
            topic=request.topic,
            count=request.count
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/generate-adaptive-task", response_model=Dict[str, Any])
async def generate_adaptive_task(request: Dict[str, Any]):
    """
    Генерация одного адаптивного задания для ученика
    Учитывает слабые темы, стиль обучения и интересы
    """
    try:
        user_id = request.get("user_id")
        use_thematic = request.get("use_thematic", False)  # Тумблер для тематических заданий
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Получаем профиль ученика
        profile = orchestrator.profiler.get_profile(user_id)
        
        # Получаем профиль личности для интересов
        from services.assistant import assistant_response_means_llm_down, get_assistant_service

        assistant = get_assistant_service()
        personality_profile = assistant.get_personality_profile(user_id)
        
        # Определяем слабые темы
        weak_topics = []
        if profile.topic_mastery:
            for topic, mastery in profile.topic_mastery.items():
                if mastery < 0.7:  # Темы с мастерством меньше 70%
                    weak_topics.append({
                        "name": topic,
                        "mastery": mastery
                    })
        
        # Сортируем по мастерству (меньше = хуже)
        weak_topics.sort(key=lambda x: x["mastery"])
        
        # Выбираем самую слабую тему или используем переданную
        target_topic = request.get("topic")
        if not target_topic and weak_topics:
            target_topic = weak_topics[0]["name"]
        elif not target_topic:
            target_topic = "общая математика"
        
        # Получаем интересы ученика
        interests = []
        if personality_profile and personality_profile.interests:
            interests = personality_profile.interests[:3]  # Берем топ-3 интереса
        
        # Формируем контекст для генерации
        student_context = f"Ученик имеет проблемы с темой: {target_topic}"
        if weak_topics:
            topics_list = ", ".join([t["name"] for t in weak_topics[:3]])
            student_context += f". Слабые темы: {topics_list}"
        
        if interests and use_thematic:
            interests_str = ", ".join(interests)
            student_context += f". Интересы ученика: {interests_str}. Используй примеры из этих областей (например, если ученик любит футбол, создай задачу про футбол)."
        
        # Разнообразие: случайный тип задачи, чтобы не повторялось одно и то же
        problem_types = [
            "уравнение с неизвестным в знаменателе (например 2/(x-1) + 1 = 3)",
            "квадратное уравнение вида ax^2 + bx + c = 0",
            "неравенство (линейное или квадратное)",
            "уравнение с корнем, например √(2x+1) = 5",
            "задача на проценты или пропорции (составь уравнение по условию)",
            "линейное уравнение с другой структурой: не (3x-5)/2 + (2x+3)/4, а например одна дробь или три слагаемых",
            "упростить выражение и найти значение при заданном x",
            "уравнение с модулем |x - 3| = 7",
        ]
        type_hint = random.choice(problem_types)
        thematic_hint = " Тематика по интересам ученика (футбол, игры и т.д.)." if use_thematic else ""
        prompt = f"""Учитель математики. Одно задание по теме "{target_topic}" для 9 класса. {student_context}.{thematic_hint}

РАЗНООБРАЗИЕ: Создай задание, отличное от шаблона «(3x-5)/2 + (2x+3)/4 = число». Используй такой тип: {type_hint}.

Правила: БЕЗ LaTeX. Дроби со скобками: (3x-5)/2. Степени: x^2. Корни: √(x+1).
Ответ — только JSON, без текста до/после.

КРИТИЧНО для correctAnswer: указывай ТОЧНЫЙ ответ (дробь 27/8 или десятичное 3.375). НИКОГДА не округляй до целого. В объяснении тоже точный ответ.

{{
  "topic": "{target_topic}",
  "difficulty": 3,
  "type": "numeric",
  "question": "текст вопроса без LaTeX",
  "options": [],
  "correctAnswer": "точное число: целое, дробь (27/8) или десятичное (3.375)",
  "explanation": "Краткое пошаговое объяснение с точным ответом, без LaTeX и markdown"
}}"""
        
        raw_response = assistant._generate(
            prompt,
            max_new_tokens=650,
            sanitize_output=False,
        )
        
        # Нет ответа от LLM — в теле ошибки клиенту не передаём внутренние инструкции (они в логах backend)
        if raw_response and assistant_response_means_llm_down(raw_response):
            raise HTTPException(
                status_code=503,
                detail=(
                    "Генерация задания временно недоступна. "
                    "Попробуйте позже или обратитесь к администратору платформы."
                ),
            )
        
        # Логируем ответ для отладки
        print(f"[AdaptiveTask] Raw AI response length: {len(raw_response)}")
        print(f"[AdaptiveTask] Raw AI response preview: {raw_response[:300]}")
        
        # Парсим JSON из ответа
        
        # Пытаемся найти JSON в ответе (более гибкий поиск)
        task_data = None
        
        # Вариант 1: Ищем JSON блок между ```json и ```
        json_code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
        if json_code_block:
            try:
                task_data = json.loads(json_code_block.group(1))
            except json.JSONDecodeError:
                pass
        
        # Вариант 2: Ищем JSON объект в фигурных скобках
        if not task_data:
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    task_data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Пытаемся найти более глубокий JSON
                    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                    if json_match:
                        try:
                            task_data = json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass
        
        # Вариант 3: Если JSON не найден, пытаемся извлечь данные из текста
        if not task_data:
            # Пытаемся извлечь данные из структурированного текста
            topic_match = re.search(r'"topic"\s*:\s*"([^"]+)"', raw_response) or re.search(r'topic["\']?\s*:\s*["\']?([^"\']+)', raw_response)
            question_match = re.search(r'"question"\s*:\s*"([^"]+)"', raw_response, re.DOTALL) or re.search(r'question["\']?\s*:\s*["\']?([^"\']+)', raw_response, re.DOTALL)
            answer_match = re.search(r'"correctAnswer"\s*:\s*"([^"]+)"', raw_response) or re.search(r'correctAnswer["\']?\s*:\s*["\']?([^"\']+)', raw_response)
            
            if question_match:
                # Создаем задание из извлеченных данных
                task_data = {
                    "topic": target_topic,
                    "difficulty": 3,
                    "type": "numeric",
                    "question": question_match.group(1).strip().replace('\\n', '\n'),
                    "correctAnswer": answer_match.group(1).strip() if answer_match else "не указан",
                    "explanation": "Решение задания"
                }
            else:
                # Последняя попытка: используем весь ответ как вопрос
                cleaned_response = raw_response.strip()
                if cleaned_response and len(cleaned_response) > 20:
                    task_data = {
                        "topic": target_topic,
                        "difficulty": 3,
                        "type": "text",
                        "question": cleaned_response[:500],  # Берем первые 500 символов
                        "correctAnswer": "не указан",
                        "explanation": "Проверьте решение самостоятельно"
                    }
        
        if not task_data:
            print(f"[AdaptiveTask] ERROR: Could not parse JSON from response")
            print(f"[AdaptiveTask] Full response: {raw_response}")
            raise HTTPException(
                status_code=500, 
                detail=f"Не удалось найти JSON в ответе AI. Попробуйте еще раз или проверьте настройки AI."
            )
        
        # Валидация обязательных полей
        required_fields = ["question", "correctAnswer"]
        for field in required_fields:
            if field not in task_data:
                print(f"[AdaptiveTask] WARNING: Missing field '{field}' in task_data")
                if field == "question":
                    task_data["question"] = f"Задание по теме {target_topic}"
                elif field == "correctAnswer":
                    task_data["correctAnswer"] = "не указан"
        
        # Очищаем explanation от markdown, если оно есть
        if "explanation" in task_data and task_data["explanation"]:
            explanation = task_data["explanation"]
            explanation = re.sub(r'\*\*([^*]+)\*\*', r'\1', explanation)  # **текст** -> текст
            explanation = re.sub(r'#{1,6}\s*', '', explanation)  # Заголовки
            explanation = re.sub(r'---+', '', explanation)  # Разделители ---
            explanation = re.sub(r'`([^`]+)`', r'\1', explanation)  # `код` -> код
            explanation = explanation.replace('**', '').replace('###', '').replace('---', '').replace('#', '')
            explanation = re.sub(r'\n{3,}', '\n\n', explanation)  # Убираем лишние пустые строки
            task_data["explanation"] = explanation.strip()
        
        # Если модель подставила неверный правильный ответ (например коэффициент 1.2 вместо ответа 1500) — берём из объяснения
        stored = (task_data.get("correctAnswer") or "").strip()
        expl = task_data.get("explanation") or ""
        # Ищем ВСЕ числа в контексте ответа (x = ..., Ответ: ..., рублей, равно ...). Берём ПОСЛЕДНЕЕ вхождение — это обычно итоговый ответ.
        candidates = []
        patterns = [
            r'[xX]\s*=\s*(\d+/\d+|\d+[.,]\d+|\d+)\s*[.\s)]',  # x = 1500 или x = 27/8
            r'[Оо]твет[:\s]+(\d+/\d+|\d+[.,]\d+|\d+)\s*[.\s]',
            r'[равно|=]\s*(\d+/\d+|\d+[.,]\d+|\d+)\s*[.\s]',
            r'\b(\d+)\s*руб',
            r'[Бб]ыла[^\d]*(\d+)\s*руб',
            r'[Цц]ена[^\d]*(\d+)\s*руб',
            r'\b(\d+/\d+)\s*[.,)]',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, expl, re.IGNORECASE):
                raw = match.group(1).replace(",", ".")
                candidates.append((match.end(), raw))  # позиция конца в тексте, значение
        # Сортируем по позиции — последнее вхождение в тексте = финальный ответ
        if candidates:
            candidates.sort(key=lambda x: x[0])
            last_raw = candidates[-1][1]
            extracted_num = _parse_numeric_answer(last_raw)
            stored_num = _parse_numeric_answer(stored)
            if extracted_num is not None:
                # Подменяем, если модель дала явно не тот ответ (например 1.2 вместо 1500)
                if stored_num is None or abs(extracted_num - stored_num) > 0.001:
                    task_data["correctAnswer"] = last_raw if "/" in last_raw else str(int(extracted_num) if extracted_num == int(extracted_num) else extracted_num)
                    print(f"[AdaptiveTask] correctAnswer из объяснения: было '{stored}', стало '{task_data['correctAnswer']}'")
        
        # Устанавливаем значения по умолчанию
        if "topic" not in task_data:
            task_data["topic"] = target_topic
        if "difficulty" not in task_data:
            task_data["difficulty"] = 3
        if "type" not in task_data:
            task_data["type"] = "numeric"
        # Объяснение без второго запроса к AI — быстрее отдача задания
        if "explanation" not in task_data or not task_data["explanation"] or task_data["explanation"].strip() in ["Решение задания", "Проверьте решение самостоятельно"]:
            task_data["explanation"] = "Проверьте решение по шагам. После отправки ответа будет доступно подробное объяснение."
        
        print(f"[AdaptiveTask] Successfully parsed task: topic={task_data.get('topic')}, type={task_data.get('type')}")
        
        # Добавляем метаданные
        task_data["id"] = int(datetime.now().timestamp() * 1000) % 1000000  # Генерируем ID
        task_data["generatedVariant"] = task_data["id"] % 1000
        task_data["targetTopic"] = target_topic
        task_data["isThematic"] = use_thematic
        
        return {
            "task": task_data,
            "targetTopic": target_topic,
            "weakTopics": [t["name"] for t in weak_topics[:3]]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/dashboard/{user_id}", response_model=Dict[str, Any])
async def get_student_dashboard(user_id: str):
    """
    Получение данных для дашборда ученика
    """
    try:
        result = orchestrator.get_student_dashboard(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/assign-tasks", response_model=Dict[str, Any])
async def assign_tasks(assignment: TaskAssignment):
    """
    Назначение заданий ученику учителем
    """
    try:
        result = orchestrator.assign_task_to_student(
            user_id=assignment.user_id,
            topic=assignment.topic,
            task_ids=assignment.task_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/teacher-report", response_model=Dict[str, Any])
async def get_teacher_report(
    report_type: str = "summary",
    class_id: Optional[str] = None
):
    """
    Получение отчета для учителя
    
    report_type: summary, detailed, struggling
    """
    try:
        result = orchestrator.get_teacher_report(
            class_id=class_id,
            report_type=report_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/profile/{user_id}", response_model=Dict[str, Any])
async def get_user_profile(user_id: str):
    """
    Получение полного профиля ученика
    """
    try:
        profiler = orchestrator.profiler
        profile = profiler.get_profile(user_id)  # Создается автоматически
        
        return profile.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

