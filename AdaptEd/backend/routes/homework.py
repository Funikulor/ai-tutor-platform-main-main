"""
API маршруты для домашних заданий
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re
from agents.orchestrator import AgentOrchestrator
from services.assistant import assistant_service

router = APIRouter()
orchestrator = AgentOrchestrator()


class HomeworkSubmission(BaseModel):
    """Модель для сдачи домашнего задания"""
    user_id: str
    homework_id: Optional[str] = None
    task_id: Optional[int] = None
    question: str
    answer: Optional[str] = None  # Ответ (может быть числом или текстом)
    solution_description: str  # Подробное описание решения
    topic: Optional[str] = None


class TestGenerationRequest(BaseModel):
    """Запрос на генерацию теста"""
    user_id: str
    topic: str
    difficulty: Optional[str] = "medium"  # easy, medium, hard
    question_count: Optional[int] = 5


class TestQuestion(BaseModel):
    """Вопрос теста"""
    question: str
    options: List[str]  # Варианты ответов
    correct_answer: int  # Индекс правильного ответа
    explanation: Optional[str] = None


class TestSubmission(BaseModel):
    """Сдача теста"""
    user_id: str
    test_id: str
    answers: Dict[int, Any]  # {question_index: answer}


@router.post("/homework/submit", response_model=Dict[str, Any])
async def submit_homework(submission: HomeworkSubmission):
    """
    Сдача домашнего задания с анализом решения
    """
    try:
        # Анализируем описание решения через LLM для выявления слабых мест
        analysis_prompt = f"""Проанализируй описание решения ученика и определи:
1. Правильность решения
2. Слабые места в понимании
3. Типы ошибок (если есть)
4. Рекомендации по улучшению

Задача: {submission.question}
Описание решения ученика: {submission.solution_description}

Верни анализ в структурированном виде."""
        
        analysis = assistant_service._generate(analysis_prompt, max_new_tokens=400)
        
        # Обновляем профиль ученика
        profile = orchestrator.profiler.get_profile(submission.user_id)
        if profile:
            # Добавляем информацию о слабых местах из описания
            weakness_keywords = ["не понимаю", "забыл", "не помню", "не знаю", "сложно"]
            solution_lower = submission.solution_description.lower()
            for keyword in weakness_keywords:
                if keyword in solution_lower:
                    # Извлекаем тему
                    if submission.topic:
                        if submission.topic not in profile.topic_mastery:
                            profile.topic_mastery[submission.topic] = 0.5
                        else:
                            profile.topic_mastery[submission.topic] = max(0.0, profile.topic_mastery[submission.topic] - 0.1)
        
        return {
            "status": "submitted",
            "analysis": analysis,
            "recommendations": "Рекомендуется повторить материал по теме" if submission.topic else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tests/generate", response_model=Dict[str, Any])
async def generate_test(request: TestGenerationRequest):
    """
    Генерация персонализированного теста через нейронку
    """
    try:
        # Получаем профиль ученика
        profile = orchestrator.profiler.get_profile(request.user_id)
        
        # Формируем промпт для генерации теста
        weakness_context = ""
        if profile:
            # Добавляем информацию о слабых местах
            if profile.error_frequency:
                top_errors = sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:2]
                weakness_context = f"Ученик часто ошибается в: {', '.join([str(e[0].value) for e in top_errors])}. "
            
            # Добавляем информацию о знаниях по теме
            if request.topic in profile.topic_mastery:
                mastery = profile.topic_mastery[request.topic]
                difficulty_note = "легкие" if mastery < 0.4 else "средние" if mastery < 0.7 else "сложные"
                weakness_context += f"Знания по теме: {mastery:.1%}. "
        
        prompt = f"""Создай тест по теме "{request.topic}" для ученика 5-9 класса.
{weakness_context}
Сложность: {request.difficulty}
Количество вопросов: {request.question_count}

Для каждого вопроса создай:
1. Вопрос
2. 4 варианта ответа (один правильный)
3. Объяснение правильного ответа

Верни в формате JSON:
{{
  "questions": [
    {{
      "question": "текст вопроса",
      "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
      "correct_answer": 0,
      "explanation": "объяснение"
    }}
  ]
}}"""
        
        generated_text = assistant_service._generate(prompt, max_new_tokens=1000)
        
        # Ищем JSON в ответе
        json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
        if json_match:
            try:
                test_data = json.loads(json_match.group())
                questions = test_data.get("questions", [])
                
                # Создаем ID теста
                test_id = f"test_{request.user_id}_{datetime.now().timestamp()}"
                
                return {
                    "test_id": test_id,
                    "topic": request.topic,
                    "questions": questions,
                    "difficulty": request.difficulty
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: создаем простой тест вручную
        questions = [
            {
                "question": f"Пример вопроса по теме {request.topic}?",
                "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
                "correct_answer": 0,
                "explanation": "Правильный ответ - первый вариант"
            }
        ] * request.question_count
        
        return {
            "test_id": f"test_{request.user_id}_{datetime.now().timestamp()}",
            "topic": request.topic,
            "questions": questions,
            "difficulty": request.difficulty
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tests/submit", response_model=Dict[str, Any])
async def submit_test(submission: TestSubmission):
    """
    Сдача теста с анализом результатов
    """
    try:
        # Здесь должна быть логика получения теста по test_id
        # Для упрощения считаем что тест уже есть
        
        # Анализируем результаты
        profile = orchestrator.profiler.get_profile(submission.user_id)
        
        # Обновляем профиль на основе результатов теста
        # (в реальности нужно получить вопросы теста)
        
        return {
            "status": "submitted",
            "score": 0,  # Будет рассчитан на основе ответов
            "analysis": "Анализ результатов теста"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{user_id}", response_model=Dict[str, Any])
async def get_student_statistics(user_id: str):
    """
    Получение статистики и слабых мест ученика
    """
    try:
        profile = orchestrator.profiler.get_profile(user_id)
        personality_profile = assistant_service.get_personality_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Определяем слабые места
        weaknesses = []
        
        # По частоте ошибок
        if profile.error_frequency:
            top_errors = sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            weaknesses.extend([{
                "type": "error_pattern",
                "name": str(err[0].value),
                "frequency": err[1],
                "description": f"Часто встречается ошибка типа: {err[0].value}"
            } for err in top_errors])
        
        # По темам с низким мастерством
        for topic, mastery in profile.topic_mastery.items():
            if mastery < 0.5:
                weaknesses.append({
                    "type": "topic_mastery",
                    "name": topic,
                    "mastery": mastery,
                    "description": f"Низкое понимание темы: {topic} ({mastery:.1%})"
                })
        
        # Из профиля личности
        if personality_profile and personality_profile.mentioned_weaknesses:
            weaknesses.extend([{
                "type": "mentioned",
                "name": w,
                "description": f"Упомянуто в диалоге: {w}"
            } for w in personality_profile.mentioned_weaknesses])
        
        return {
            "user_id": user_id,
            "statistics": {
                "total_tasks": profile.total_tasks_completed,
                "correct_tasks": profile.correct_tasks_count,
                "accuracy_rate": profile.accuracy_rate,
                "level": profile.level,
                "points": profile.points
            },
            "weaknesses": weaknesses,
            "strengths": [
                topic for topic, mastery in profile.topic_mastery.items() if mastery >= 0.7
            ],
            "personality": personality_profile.dict() if personality_profile else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

