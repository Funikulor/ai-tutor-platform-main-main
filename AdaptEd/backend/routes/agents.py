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
from agents.orchestrator import AgentOrchestrator

router = APIRouter()
orchestrator = AgentOrchestrator()


class TaskSubmission(BaseModel):
    """Модель для отправки задания"""
    user_id: str
    task_id: int
    question: str
    user_answer: int
    correct_answer: int


class TaskGenerationRequest(BaseModel):
    """Запрос на генерацию заданий"""
    user_id: str
    topic: Optional[str] = "general"
    count: Optional[int] = 3


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
    """
    try:
        result = orchestrator.process_task_submission(
            user_id=submission.user_id,
            task_id=submission.task_id,
            question=submission.question,
            user_answer=submission.user_answer,
            correct_answer=submission.correct_answer
        )
        return result
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

