"""
API маршруты для работы с ИИ-агентами
"""
import sys
import os

# Добавляем путь к backend для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re
from agents.orchestrator import AgentOrchestrator

router = APIRouter()
orchestrator = AgentOrchestrator()


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
        
        # Если числовые ответы, сравниваем как числа
        try:
            user_num = float(submission.user_answer)
            correct_num = float(submission.correct_answer)
            is_correct = abs(user_num - correct_num) < 0.01  # Допуск для числовых ответов
        except (ValueError, TypeError):
            pass  # Используем строковое сравнение
        
        # Обрабатываем через orchestrator
        result = orchestrator.process_task_submission(
            user_id=submission.user_id,
            task_id=submission.task_id,
            question=submission.question,
            user_answer=submission.user_answer,
            correct_answer=submission.correct_answer,
            topic=submission.topic,
            time_spent_seconds=submission.time_spent_seconds
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
        from services.assistant import get_assistant_service
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
        
        # Генерируем задание через AI
        prompt = f"""Ты - учитель математики. Создай одно математическое задание по теме "{target_topic}" для ученика 9 класса.

{student_context}

{"ВАЖНО: Создай задание с интересной тематикой, связанной с интересами ученика. Например, если ученик любит футбол, создай задачу про футбол (расстояние до ворот, скорость мяча и т.д.). Задание должно быть увлекательным и практичным." if use_thematic else "Создай обычное математическое задание, но сфокусированное на слабых местах ученика."}

КРИТИЧЕСКИ ВАЖНО:
- НЕ используй LaTeX синтаксис (\\frac, \\sqrt, \\(, \\[ и т.д.)
- Пиши математические формулы обычным текстом:
  * Дроби: ВСЕГДА используй скобки для числителя и знаменателя, если они содержат операции:
    - ПРАВИЛЬНО: (3x - 5) / 2, (2x + 3) / 4, (x + 1) / (x - 1)
    - НЕПРАВИЛЬНО: 2x+3/4 (без скобок), 3x-5/2 (без скобок)
    - Для простых дробей можно: x/2, 3/4, но для сложных ВСЕГДА скобки: (2x+3)/4
  * Степени: x^2 или x²
  * Корни: √(x+1) или корень из (x+1)
  * Пример: "Решите уравнение: (3x - 5) / 2 = x + 4" вместо "\\frac{{3x-5}}{{2}} = x+4"
  * Пример: "Найдите значение: (2x + 3) / 4 = 5 - x/2" (обрати внимание на скобки!)

ОБЯЗАТЕЛЬНО верни ответ ТОЛЬКО в формате JSON, без дополнительного текста до или после JSON.

ВАЖНО для поля "explanation":
- Объяснение должно быть ПОЛНЫМ и ПОДРОБНЫМ
- Опиши каждый шаг решения по порядку
- НЕ пиши просто "Решение задания" или "Проверьте решение самостоятельно"
- Объясни, как получить правильный ответ, шаг за шагом
- Используй обычный текст, БЕЗ LaTeX
- НЕ используй markdown форматирование (**, ###, --- и т.д.)
- Пиши простым, понятным языком, как будто объясняешь другу
- Сделай объяснение интересным и увлекательным для ученика
- Используй эмодзи для визуального разделения шагов (например: 🔹, 📝, ✅)
- КРИТИЧЕСКИ ВАЖНО: НЕ используй технические переменные типа t_ball, t_keeper, v1, v2 и т.д. в тексте объяснения
- Вместо переменных используй описательные фразы: "время полета мяча", "скорость вратаря", "расстояние до ворот"
- Каждый шаг должен быть на отдельной строке, начинай с эмодзи и описания шага
- Используй переносы строк между шагами для лучшей читаемости

Пример правильного ответа:
{{
  "topic": "Линейные уравнения",
  "difficulty": 3,
  "type": "numeric",
  "question": "Решите уравнение: (3x - 5) / 2 = x + 4",
  "correctAnswer": "13",
  "explanation": "Шаг 1: Умножаем обе части уравнения на 2, чтобы избавиться от дроби. Получаем: 3x - 5 = 2(x + 4). Шаг 2: Раскрываем скобки: 3x - 5 = 2x + 8. Шаг 3: Переносим все слагаемые с x в левую часть, а числа в правую: 3x - 2x = 8 + 5. Шаг 4: Упрощаем: x = 13. Ответ: x = 13"
}}

Твой ответ (только JSON, без комментариев):
{{
  "topic": "{target_topic}",
  "difficulty": 1-5,
  "type": "multiple-choice" | "numeric" | "text",
  "question": "текст вопроса БЕЗ LaTeX",
  "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
  "correctAnswer": "правильный ответ",
  "explanation": "ПОДРОБНОЕ объяснение с шагами решения БЕЗ LaTeX (минимум 2-3 предложения, опиши каждый шаг)"
}}"""
        
        # Генерируем через assistant service
        assistant = get_assistant_service()
        raw_response = assistant._generate(prompt, max_new_tokens=1200)
        
        # Логируем ответ для отладки
        print(f"[AdaptiveTask] Raw AI response length: {len(raw_response)}")
        print(f"[AdaptiveTask] Raw AI response preview: {raw_response[:300]}")
        
        # Парсим JSON из ответа
        import json
        import re
        
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
        
        # Устанавливаем значения по умолчанию
        if "topic" not in task_data:
            task_data["topic"] = target_topic
        if "difficulty" not in task_data:
            task_data["difficulty"] = 3
        if "type" not in task_data:
            task_data["type"] = "numeric"
        # Если объяснение отсутствует или пустое, генерируем его
        if "explanation" not in task_data or not task_data["explanation"] or task_data["explanation"].strip() in ["Решение задания", "Проверьте решение самостоятельно"]:
            # Генерируем объяснение на основе вопроса и ответа
            try:
                explanation_prompt = f"""Объясни подробно и интересно, как решить эту задачу пошагово:

Вопрос: {task_data.get("question", "")}
Правильный ответ: {task_data.get("correctAnswer", "")}

ВАЖНО:
- Опиши каждый шаг решения подробно, используя обычный текст (БЕЗ LaTeX)
- НЕ используй markdown форматирование (**, ###, --- и т.д.)
- Пиши простым, понятным языком, как будто объясняешь другу
- Сделай объяснение интересным и увлекательным
- Используй эмодзи для визуального разделения шагов (например: 🔹, 📝, ✅, 💡)
- Объяснение должно быть понятным для ученика 9 класса
- Начни с краткого введения, затем опиши каждый шаг по порядку
- КРИТИЧЕСКИ ВАЖНО: Объяснение должно быть ПОЛНЫМ и ЗАВЕРШЕННЫМ - опиши все шаги до финального ответа, не обрывай на середине
- КРИТИЧЕСКИ ВАЖНО: НЕ используй технические переменные типа t_ball, t_keeper, v1, v2, s1, s2 и т.д. в тексте объяснения
- Вместо переменных используй описательные фразы: "время полета мяча", "скорость вратаря", "расстояние до ворот", "время движения"
- Каждый шаг должен быть на отдельной строке, начинай с эмодзи 🔹 и описания шага
- Используй переносы строк между шагами для лучшей читаемости
- Формат: каждый шаг на новой строке, начинай с 🔹 Шаг N: описание"""
                
                explanation_response = assistant._generate(explanation_prompt, max_new_tokens=1000)
                # Очищаем ответ от лишнего
                explanation_clean = explanation_response.strip()
                # Убираем кавычки, если они есть
                if explanation_clean.startswith('"') and explanation_clean.endswith('"'):
                    explanation_clean = explanation_clean[1:-1]
                # Убираем markdown форматирование более тщательно
                import re
                explanation_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', explanation_clean)  # **текст** -> текст
                explanation_clean = re.sub(r'#{1,6}\s*', '', explanation_clean)  # Заголовки
                explanation_clean = re.sub(r'---+', '', explanation_clean)  # Разделители ---
                explanation_clean = re.sub(r'`([^`]+)`', r'\1', explanation_clean)  # `код` -> код
                explanation_clean = re.sub(r'\*\s+', '• ', explanation_clean)  # Списки * -> •
                explanation_clean = explanation_clean.replace('**', '').replace('###', '').replace('---', '').replace('#', '')
                # Убираем лишние пустые строки
                explanation_clean = re.sub(r'\n{3,}', '\n\n', explanation_clean)
                # Убираем проблемные символы
                explanation_clean = explanation_clean.replace('\uFFFD', '')  # Убираем символ замены
                # Заменяем технические переменные на описательные фразы
                explanation_clean = re.sub(r'\bt_ball\b', 'время полета мяча', explanation_clean, flags=re.IGNORECASE)
                explanation_clean = re.sub(r'\bt_keeper\b', 'время движения вратаря', explanation_clean, flags=re.IGNORECASE)
                explanation_clean = re.sub(r'\bt_(\w+)\b', r'время \1', explanation_clean, flags=re.IGNORECASE)
                explanation_clean = re.sub(r'\bv(\d+)\b', r'скорость \1', explanation_clean, flags=re.IGNORECASE)
                explanation_clean = re.sub(r'\bs(\d+)\b', r'расстояние \1', explanation_clean, flags=re.IGNORECASE)
                # Если весь текст в одной строке, пытаемся разбить по шагам
                if '\n' not in explanation_clean and 'Шаг' in explanation_clean:
                    # Разбиваем по "Шаг N:" или "🔹 Шаг N:"
                    explanation_clean = re.sub(r'(🔹\s*)?Шаг\s*(\d+)[:.]\s*', r'\n🔹 Шаг \2: ', explanation_clean, flags=re.IGNORECASE)
                task_data["explanation"] = explanation_clean.strip() if explanation_clean.strip() else "Подробное объяснение решения будет добавлено позже."
            except Exception as e:
                print(f"[AdaptiveTask] Error generating explanation: {e}")
                task_data["explanation"] = "Подробное объяснение решения будет добавлено позже."
        
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

