"""
API маршруты для домашних заданий
"""
from fastapi import APIRouter, HTTPException, Depends
from routes.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import re
from collections import defaultdict
from agents.orchestrator import AgentOrchestrator
from services.assistant import get_assistant_service
from utils.db import get_db, has_db
from sqlalchemy.orm import Session
from models.homework import Homework, HomeworkSubmission as HomeworkSubmissionORM
from utils.db import Base
from sqlalchemy import select
from models.test import TestSubmission, Test

router = APIRouter()
orchestrator = AgentOrchestrator()
assistant_service = None  # будет создан по запросу

def _assistant():
	global assistant_service
	if assistant_service is None:
		assistant_service = get_assistant_service()
	return assistant_service


class HomeworkSubmissionPayload(BaseModel):
    """Модель для сдачи домашнего задания (старый формат, без БД)"""
    user_id: str
    homework_id: Optional[str] = None
    task_id: Optional[int] = None
    question: str
    answer: Optional[str] = None  # Ответ (может быть числом или текстом)
    solution_description: str  # Подробное описание решения
    topic: Optional[str] = None


# Новые схемы для работы с БД (должны быть определены до использования в эндпоинтах)
class HomeworkCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: str
    created_by: Optional[str] = None


class HomeworkOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    subject: Optional[str]
    due_date: Optional[datetime]
    status: str
    assigned_to: str
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HomeworkSubmitDB(BaseModel):
    answer_text: Optional[str] = None
    user_id: str


# ====== Новые эндпоинты на Postgres ======

@router.get("/homeworks", response_model=List[HomeworkOut])
async def list_homeworks(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    # Пробуем использовать БД
    if has_db() and db is not None:
        try:
            stmt = select(Homework)
            if user_id:
                stmt = stmt.where(Homework.assigned_to == user_id)
            rows = db.execute(stmt).scalars().all()
            return rows
        except Exception as e:
            print(f"Error fetching homeworks from DB: {e}")
    
    # Fallback на persistent_storage
    from utils.persistent_storage import persistent_storage
    homeworks = persistent_storage.get("homeworks", [])
    
    if user_id:
        homeworks = [hw for hw in homeworks if hw.get('assigned_to') == user_id]
    
    # Преобразуем в формат HomeworkOut
    result = []
    for hw in homeworks:
        result.append({
            "id": hw.get('id', 0),
            "title": hw.get('title', ''),
            "description": hw.get('description'),
            "subject": hw.get('subject'),
            "due_date": hw.get('due_date'),
            "status": hw.get('status', 'new'),
            "assigned_to": hw.get('assigned_to', ''),
            "created_by": hw.get('created_by'),
            "created_at": hw.get('created_at', datetime.now())
        })
    
    return result


@router.post("/homeworks", response_model=HomeworkOut)
async def create_homework(payload: HomeworkCreate, db: Session = Depends(get_db)):
    # Пробуем использовать БД
    if has_db() and db is not None:
        try:
            hw = Homework(
                title=payload.title,
                description=payload.description,
                subject=payload.subject,
                due_date=payload.due_date,
                assigned_to=payload.assigned_to,
                created_by=payload.created_by,
                status="new",
            )
            db.add(hw)
            db.commit()
            db.refresh(hw)
            return hw
        except Exception as e:
            print(f"Error creating homework in DB: {e}")
            db.rollback()
    
    # Fallback на persistent_storage
    from utils.persistent_storage import persistent_storage
    homeworks = persistent_storage.get("homeworks", [])
    
    new_id = max([hw.get('id', 0) for hw in homeworks], default=0) + 1
    new_homework = {
        "id": new_id,
        "title": payload.title,
        "description": payload.description,
        "subject": payload.subject,
        "due_date": payload.due_date.isoformat() if payload.due_date else None,
        "assigned_to": payload.assigned_to,
        "created_by": payload.created_by,
        "status": "new",
        "created_at": datetime.now().isoformat()
    }
    
    homeworks.append(new_homework)
    persistent_storage.set("homeworks", homeworks)
    
    return {
        "id": new_id,
        "title": payload.title,
        "description": payload.description,
        "subject": payload.subject,
        "due_date": payload.due_date,
        "status": "new",
        "assigned_to": payload.assigned_to,
        "created_by": payload.created_by,
        "created_at": datetime.now()
    }


@router.post("/homeworks/{homework_id}/submit", response_model=Dict[str, Any])
async def submit_homework_db(homework_id: int, payload: HomeworkSubmitDB, db: Session = Depends(get_db)):
    # Пробуем использовать БД
    if has_db() and db is not None:
        try:
            hw = db.get(Homework, homework_id)
            if not hw:
                raise HTTPException(status_code=404, detail="Homework not found")
            if hw.assigned_to != payload.user_id:
                raise HTTPException(status_code=403, detail="Homework is assigned to another student")

            submission = HomeworkSubmissionORM(
                homework_id=homework_id,
                user_id=payload.user_id,
                answer_text=payload.answer_text or "",
                created_at=datetime.utcnow(),
            )

            # Генерируем короткий фидбек через ассистента (неблокирующий)
            feedback = None
            try:
                assist = _assistant()
                prompt = (
                    "Кратко оцени ответ ученика и дай 1-2 рекомендации.\n"
                    f"Задание: {hw.title}\n"
                    f"Описание: {hw.description or ''}\n"
                    f"Ответ ученика: {payload.answer_text or ''}\n"
                )
                feedback = assist._generate(prompt, max_new_tokens=300)
            except Exception:
                feedback = None

            submission.feedback = feedback
            db.add(submission)

            # Обновляем статус домашки
            hw.status = "submitted"
            db.add(hw)

            db.commit()
            db.refresh(submission)
            db.refresh(hw)

            return {
                "status": "submitted",
                "homework": {
                    "id": hw.id,
                    "title": hw.title,
                    "description": hw.description,
                    "status": hw.status
                },
                "submission": {
                    "id": submission.id,
                    "user_id": submission.user_id,
                    "answer_text": submission.answer_text,
                    "feedback": submission.feedback,
                    "created_at": submission.created_at,
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error submitting homework to DB: {e}")
            db.rollback()
    
    # Fallback на persistent_storage
    from utils.persistent_storage import persistent_storage
    homeworks = persistent_storage.get("homeworks", [])
    hw = next((hw for hw in homeworks if hw.get('id') == homework_id), None)
    
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    if hw.get('assigned_to') != payload.user_id:
        raise HTTPException(status_code=403, detail="Homework is assigned to another student")
    
    # Генерируем фидбек
    feedback = None
    try:
        assist = _assistant()
        prompt = (
            "Кратко оцени ответ ученика и дай 1-2 рекомендации.\n"
            f"Задание: {hw.get('title', '')}\n"
            f"Описание: {hw.get('description', '')}\n"
            f"Ответ ученика: {payload.answer_text or ''}\n"
        )
        feedback = assist._generate(prompt, max_new_tokens=300)
    except Exception:
        feedback = None
    
    # Сохраняем submission
    submissions = persistent_storage.get("homework_submissions", [])
    new_submission_id = max([s.get('id', 0) for s in submissions], default=0) + 1
    submission = {
        "id": new_submission_id,
        "homework_id": homework_id,
        "user_id": payload.user_id,
        "answer_text": payload.answer_text or "",
        "feedback": feedback,
        "created_at": datetime.now().isoformat()
    }
    submissions.append(submission)
    persistent_storage.set("homework_submissions", submissions)
    
    # Обновляем статус домашки
    hw['status'] = "submitted"
    persistent_storage.set("homeworks", homeworks)
    
    return {
        "status": "submitted",
        "homework": {
            "id": hw.get('id'),
            "title": hw.get('title'),
            "description": hw.get('description'),
            "status": "submitted"
        },
        "submission": {
            "id": new_submission_id,
            "user_id": payload.user_id,
            "answer_text": payload.answer_text or "",
            "feedback": feedback,
            "created_at": datetime.now()
        },
    }


@router.get("/homeworks/{homework_id}/submissions", response_model=List[Dict[str, Any]])
async def list_submissions(homework_id: int, db: Session = Depends(get_db)):
    # Пробуем использовать БД
    if has_db() and db is not None:
        try:
            hw = db.get(Homework, homework_id)
            if not hw:
                raise HTTPException(status_code=404, detail="Homework not found")
            stmt = select(HomeworkSubmissionORM).where(HomeworkSubmissionORM.homework_id == homework_id)
            rows = db.execute(stmt).scalars().all()
            return [
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "answer_text": s.answer_text,
                    "feedback": s.feedback,
                    "score": s.score,
                    "created_at": s.created_at,
                }
                for s in rows
            ]
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error fetching submissions from DB: {e}")
    
    # Fallback на persistent_storage
    from utils.persistent_storage import persistent_storage
    homeworks = persistent_storage.get("homeworks", [])
    hw = next((hw for hw in homeworks if hw.get('id') == homework_id), None)
    
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    submissions = persistent_storage.get("homework_submissions", [])
    homework_submissions = [s for s in submissions if s.get('homework_id') == homework_id]
    
    return [
        {
            "id": s.get('id', 0),
            "user_id": s.get('user_id', ''),
            "answer_text": s.get('answer_text', ''),
            "feedback": s.get('feedback'),
            "score": s.get('score'),
            "created_at": s.get('created_at')
        }
        for s in homework_submissions
    ]


@router.post("/homework/submit", response_model=Dict[str, Any])
async def submit_homework(submission: HomeworkSubmissionPayload):
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
        
        analysis = _assistant()._generate(analysis_prompt, max_new_tokens=400)
        
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


# УДАЛЕН: эндпоинт /tests/generate перенесен в routes/tests.py
# УДАЛЕН: эндпоинт /tests/submit перенесен в routes/tests.py
# Используйте эндпоинты из routes/tests.py для работы с тестами


@router.get("/statistics/{user_id}", response_model=Dict[str, Any])
async def get_student_statistics(user_id: str):
    """
    Получение статистики и слабых мест ученика
    """
    try:
        profile = orchestrator.profiler.get_profile(user_id)
        personality_profile = _assistant().get_personality_profile(user_id)
        
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


@router.get("/progress/{user_id}", response_model=Dict[str, Any])
async def get_student_progress(user_id: str, db: Session = Depends(get_db)):
    """
    Получение полной статистики прогресса ученика для дашборда
    Включает: статистику, слабые места, недельные данные, недавнюю активность
    """
    try:
        # Получаем базовую статистику
        profile = orchestrator.profiler.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Получаем аналитику
        analytics_data = None
        try:
            from services.student_analytics import get_analytics_service
            analytics_service = get_analytics_service()
            analytics_data = analytics_service.get_analytics(user_id)
        except Exception:
            pass
        
        # Получаем историю тестов из БД
        test_submissions = []
        weekly_data = defaultdict(lambda: {"scores": [], "tasks": 0})
        recent_activities = []
        
        if has_db() and db is not None:
            try:
                # Получаем последние 30 дней тестов
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                stmt = select(TestSubmission).where(
                    TestSubmission.user_id == user_id,
                    TestSubmission.created_at >= thirty_days_ago
                ).order_by(TestSubmission.created_at.desc())
                submissions = db.execute(stmt).scalars().all()
                
                for sub in submissions:
                    # Получаем информацию о тесте
                    topic = "Неизвестная тема"
                    try:
                        if sub.test_id:
                            test = db.get(Test, sub.test_id)
                            if test and hasattr(test, 'topic') and test.topic:
                                topic = test.topic
                    except Exception:
                        pass
                    
                    test_submissions.append({
                        "date": sub.created_at.isoformat() if sub.created_at else None,
                        "topic": topic,
                        "score": sub.score or 0,
                        "test_id": sub.test_id
                    })
                    
                    # Добавляем в недавнюю активность (последние 10)
                    if len(recent_activities) < 10:
                        recent_activities.append({
                            "date": sub.created_at.strftime("%Y-%m-%d") if sub.created_at else "",
                            "topic": topic,
                            "score": sub.score or 0,
                            "time": 0  # Время не сохраняется в TestSubmission
                        })
                    
                    # Группируем по неделям для графика
                    if sub.created_at:
                        week_start = sub.created_at - timedelta(days=sub.created_at.weekday())
                        week_key = week_start.strftime("%Y-%m-%d")
                        weekly_data[week_key]["scores"].append(sub.score or 0)
                        weekly_data[week_key]["tasks"] += 1
            except Exception as e:
                print(f"Error fetching test submissions: {e}")
        
        # Формируем недельные данные для графика (последние 7 дней)
        weekly_chart_data = []
        day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        today = datetime.utcnow()
        
        for i in range(6, -1, -1):  # Последние 7 дней
            day = today - timedelta(days=i)
            day_key = day.strftime("%Y-%m-%d")
            day_name = day_names[day.weekday()]
            
            # Находим все тесты за этот день
            day_scores = []
            day_tasks = 0
            for sub in test_submissions:
                if sub["date"] and sub["date"].startswith(day_key):
                    day_scores.append(sub["score"])
                    day_tasks += 1
            
            avg_score = sum(day_scores) / len(day_scores) if day_scores else 0
            weekly_chart_data.append({
                "day": day_name,
                "score": round(avg_score, 1),
                "tasks": day_tasks
            })
        
        # Формируем данные о типах ошибок для графика
        error_types_data = []
        error_type_labels = {
            "missing_formula": "Отсутствие формулы",
            "concept_confusion": "Концептуальные",
            "carelessness": "Небрежность",
            "logic_gap": "Логические пробелы",
            "calculation_error": "Вычислительные",
            "not_attempted": "Не решено"
        }
        
        if profile.error_frequency:
            for error_tag, count in profile.error_frequency.items():
                error_type_str = str(error_tag.value) if hasattr(error_tag, 'value') else str(error_tag)
                label = error_type_labels.get(error_type_str, error_type_str.replace('_', ' ').title())
                error_types_data.append({
                    "type": label,
                    "count": count
                })
        
        # Если нет данных об ошибках, возвращаем пустой массив
        if not error_types_data:
            error_types_data = []
        
        # Добавляем задания из истории в недавнюю активность
        if profile.task_history:
            for task in sorted(profile.task_history, key=lambda t: t.timestamp, reverse=True)[:10]:
                if len(recent_activities) >= 10:
                    break
                task_date = task.timestamp.strftime("%Y-%m-%d") if hasattr(task.timestamp, 'strftime') else str(task.timestamp)[:10]
                # Извлекаем тему из вопроса или используем общую
                topic = "Задание"
                if hasattr(task, 'question') and task.question:
                    # Пытаемся найти тему в вопросе
                    for known_topic in profile.topic_mastery.keys():
                        if known_topic.lower() in str(task.question).lower():
                            topic = known_topic
                            break
                
                score = 100 if task.is_correct else 0
                time_spent = task.time_spent_seconds or 0
                
                recent_activities.append({
                    "date": task_date,
                    "topic": topic,
                    "score": score,
                    "time": time_spent // 60  # Конвертируем секунды в минуты
                })
        
        # Сортируем недавнюю активность по дате (новые первые)
        recent_activities.sort(key=lambda x: x["date"], reverse=True)
        recent_activities = recent_activities[:10]  # Берем только последние 10
        
        # Определяем слабые места
        weak_topics = []
        for topic, mastery in profile.topic_mastery.items():
            if mastery < 0.7:  # Темы с мастерством меньше 70%
                # Подсчитываем ошибки по этой теме из истории заданий
                errors_count = sum(1 for task in profile.task_history 
                                 if not task.is_correct and topic.lower() in str(task.question).lower())
                weak_topics.append({
                    "name": topic,
                    "progress": int(mastery * 100),
                    "errors": errors_count
                })
        
        # Сортируем по прогрессу (меньше = хуже)
        weak_topics.sort(key=lambda x: x["progress"])
        weak_topics = weak_topics[:3]  # Топ-3 слабых места
        
        # Подсчитываем общее количество тем
        total_topics = len(profile.topic_mastery) if profile.topic_mastery else 24
        completed_topics = sum(1 for mastery in profile.topic_mastery.values() if mastery >= 0.7) if profile.topic_mastery else 0
        
        # Подсчитываем streak (дни подряд с активностью)
        current_streak = 0
        if profile.task_history:
            # Сортируем по дате
            sorted_tasks = sorted(profile.task_history, key=lambda t: t.timestamp, reverse=True)
            current_date = datetime.utcnow().date()
            for i, task in enumerate(sorted_tasks):
                task_date = task.timestamp.date() if hasattr(task.timestamp, 'date') else datetime.fromisoformat(str(task.timestamp)).date() if isinstance(task.timestamp, str) else current_date
                days_diff = (current_date - task_date).days
                if days_diff == i:
                    current_streak += 1
                else:
                    break
        
        return {
            "user_id": user_id,
            "progress": {
                "totalTopics": total_topics,
                "completedTopics": completed_topics,
                "currentStreak": current_streak,
                "totalPoints": profile.points,
                "averageAccuracy": round(profile.accuracy_rate, 1),
                "weakTopics": weak_topics,
                "recentActivities": recent_activities[:10],  # Последние 10 активностей
                "errorTypes": error_types_data  # Типы ошибок для графика
            },
            "weeklyData": weekly_chart_data,
            "statistics": {
                "total_tasks": profile.total_tasks_completed,
                "correct_tasks": profile.correct_tasks_count,
                "accuracy_rate": profile.accuracy_rate,
                "level": profile.level,
                "points": profile.points
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/{user_id}", response_model=Dict[str, Any])
async def get_knowledge_graph(user_id: str, db: Session = Depends(get_db)):
    """
    Получение данных для графа знаний ученика
    Возвращает структурированные данные о знаниях по темам
    """
    try:
        profile = orchestrator.profiler.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Группируем темы по категориям (упрощенная структура)
        # Можно расширить, добавив больше категорий
        topic_categories = {
            "Алгебра": ["уравнение", "функция", "алгебра", "линейн", "квадратн", "многочлен", "степень", "корень"],
            "Геометрия": ["геометр", "треугольник", "площадь", "объем", "пифагор", "тригонометр", "синус", "косинус"],
            "Арифметика": ["арифметик", "дробь", "процент", "пропорция", "число"],
        }
        
        # Создаем структуру графа знаний
        knowledge_nodes = []
        
        # Обрабатываем каждую тему из topic_mastery
        for topic_name, mastery_value in profile.topic_mastery.items():
            mastery_level = int(mastery_value * 100)  # Конвертируем в проценты
            
            # Определяем статус на основе уровня мастерства
            if mastery_level >= 80:
                status = 'mastered'
            elif mastery_level >= 60:
                status = 'learning'
            elif mastery_level >= 40:
                status = 'needs-work'
            else:
                status = 'needs-work'
            
            # Подсчитываем ошибки по этой теме
            error_count = 0
            last_attempt = None
            
            if profile.task_history:
                for task in profile.task_history:
                    # Проверяем, относится ли задание к этой теме
                    task_text = str(task.question).lower() if hasattr(task, 'question') and task.question else ""
                    topic_lower = topic_name.lower()
                    
                    if topic_lower in task_text or any(keyword in task_text for keyword in topic_lower.split()):
                        if not task.is_correct:
                            error_count += 1
                        
                        # Находим последнюю попытку
                        if task.timestamp:
                            task_date = task.timestamp.date() if hasattr(task.timestamp, 'date') else datetime.fromisoformat(str(task.timestamp)).date() if isinstance(task.timestamp, str) else None
                            if task_date:
                                date_str = task_date.strftime("%Y-%m-%d")
                                if not last_attempt or date_str > last_attempt:
                                    last_attempt = date_str
            
            # Определяем категорию темы
            category = "Общее"
            topic_lower = topic_name.lower()
            for cat_name, keywords in topic_categories.items():
                if any(keyword in topic_lower for keyword in keywords):
                    category = cat_name
                    break
            
            knowledge_nodes.append({
                "id": topic_name.lower().replace(" ", "-"),
                "name": topic_name,
                "level": "topic",
                "masteryLevel": mastery_level,
                "status": status,
                "errorCount": error_count,
                "lastAttempt": last_attempt,
                "category": category
            })
        
        # Группируем по категориям
        categorized_data = {}
        for node in knowledge_nodes:
            category = node.get("category", "Общее")
            if category not in categorized_data:
                categorized_data[category] = []
            categorized_data[category].append(node)
        
        # Создаем иерархическую структуру
        math_node = {
            "id": "math",
            "name": "Математика",
            "level": "subject",
            "masteryLevel": int(sum(node["masteryLevel"] for node in knowledge_nodes) / len(knowledge_nodes)) if knowledge_nodes else 0,
            "status": "learning",
            "children": []
        }
        
        # Добавляем категории как секции
        for category, nodes in categorized_data.items():
            category_mastery = int(sum(node["masteryLevel"] for node in nodes) / len(nodes)) if nodes else 0
            category_status = "mastered" if category_mastery >= 80 else ("learning" if category_mastery >= 60 else "needs-work")
            
            category_node = {
                "id": category.lower().replace(" ", "-"),
                "name": category,
                "level": "section",
                "masteryLevel": category_mastery,
                "status": category_status,
                "children": nodes
            }
            math_node["children"].append(category_node)
        
        # Если нет категорий, добавляем все темы напрямую
        if not math_node["children"]:
            math_node["children"] = knowledge_nodes
        
        # Определяем области, требующие внимания (слабо освоенные темы)
        problem_areas = []
        for node in knowledge_nodes:
            if node["masteryLevel"] < 70 or node["errorCount"] > 5:
                problem_areas.append({
                    "name": node["name"],
                    "masteryLevel": node["masteryLevel"],
                    "errorCount": node["errorCount"],
                    "status": node["status"]
                })
        
        # Сортируем по уровню мастерства (худшие первые)
        problem_areas.sort(key=lambda x: x["masteryLevel"])
        problem_areas = problem_areas[:5]  # Топ-5 проблемных областей
        
        return {
            "knowledgeGraph": math_node,
            "problemAreas": problem_areas,
            "totalTopics": len(knowledge_nodes),
            "masteredTopics": sum(1 for node in knowledge_nodes if node["masteryLevel"] >= 80),
            "overallProgress": math_node["masteryLevel"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_knowledge_graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_admin_stats(db: Session = Depends(get_db)):
    """
    Получение системной статистики для админа
    """
    try:
        from utils.auth_service import auth_service
        
        # Получаем всех пользователей
        all_users = auth_service.get_all_users()
        total_users = len(all_users)
        
        # Подсчитываем по ролям
        students_count = sum(1 for u in all_users if u.get('role') == 'student')
        teachers_count = sum(1 for u in all_users if u.get('role') == 'teacher')
        
        # Подсчитываем общее количество заданий из всех профилей
        total_tasks = 0
        total_materials = 0
        ai_queries = 0
        
        # Собираем данные из всех профилей
        for user in all_users:
            user_id = user.get('user_id')
            if user_id:
                profile = orchestrator.profiler.get_profile(user_id)
                if profile:
                    total_tasks += profile.total_tasks_completed
        
        # Подсчитываем количество уникальных тем
        all_topics = set()
        for user in all_users:
            user_id = user.get('user_id')
            if user_id:
                profile = orchestrator.profiler.get_profile(user_id)
                if profile and profile.topic_mastery:
                    all_topics.update(profile.topic_mastery.keys())
        total_materials = len(all_topics)
        
        return {
            "totalUsers": total_users,
            "totalTasks": total_tasks,
            "totalMaterials": total_materials,
            "aiQueries": ai_queries,
            "studentsCount": students_count,
            "teachersCount": teachers_count,
            "storageUsed": "N/A",
            "uptime": "99.8%"
        }
    except Exception as e:
        print(f"Error in get_admin_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/users", response_model=List[Dict[str, Any]])
async def get_admin_users(db: Session = Depends(get_db)):
    """
    Получение списка всех пользователей для админа
    """
    try:
        from utils.auth_service import auth_service
        
        users = auth_service.get_all_users()
        
        # Форматируем данные для отображения
        formatted_users = []
        for user in users:
            formatted_users.append({
                "id": user.get('user_id', ''),
                "name": user.get('full_name', user.get('email', 'Неизвестно')),
                "email": user.get('email', ''),
                "role": user.get('role', 'student'),
                "status": "active" if user.get('is_active', True) else "inactive",
                "class_id": user.get('class_id'),
                "phone": user.get('phone'),
                "parent_fio": user.get('parent_fio'),
                "parent_phone": user.get('parent_phone'),
            })
        
        return formatted_users
    except Exception as e:
        print(f"Error in get_admin_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teacher/class-analytics", response_model=Dict[str, Any])
async def get_class_analytics(class_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Получение аналитики класса для учителя
    """
    try:
        from utils.auth_service import auth_service
        
        # Получаем всех пользователей
        all_users = auth_service.get_all_users()
        
        # Фильтруем студентов (если указан class_id, фильтруем по классу)
        students = [u for u in all_users if u.get('role') == 'student']
        if class_id:
            students = [s for s in students if s.get('class_id') == class_id]
        
        # Формируем данные о студентах
        class_data = []
        all_topics = set()
        topic_errors = defaultdict(lambda: {"count": 0, "students": set(), "error_types": defaultdict(int)})
        
        for student in students:
            user_id = student.get('user_id')
            if not user_id:
                continue
                
            profile = orchestrator.profiler.get_profile(user_id)
            if not profile:
                continue
            
            # Подсчитываем ошибки
            error_count = sum(1 for task in profile.task_history if not task.is_correct)
            
            # Подсчитываем изученные темы (мастерство >= 70%)
            completed_topics = sum(1 for mastery in profile.topic_mastery.values() if mastery >= 0.7) if profile.topic_mastery else 0
            
            # Определяем статус
            if profile.accuracy_rate >= 85:
                status = 'excellent'
            elif profile.accuracy_rate >= 70:
                status = 'good'
            elif profile.accuracy_rate >= 60:
                status = 'average'
            else:
                status = 'needs-help'
            
            class_data.append({
                "student": student.get('full_name', student.get('email', 'Неизвестно')),
                "score": round(profile.accuracy_rate, 0),
                "topics": completed_topics,
                "errors": error_count,
                "status": status,
                "user_id": user_id
            })
            
            # Собираем данные об ошибках по темам
            for task in profile.task_history:
                if not task.is_correct and task.topic:
                    topic_errors[task.topic]["count"] += 1
                    topic_errors[task.topic]["students"].add(user_id)
                    if task.error_analysis and task.error_analysis.error_type:
                        topic_errors[task.topic]["error_types"][task.error_analysis.error_type] += 1
                    all_topics.add(task.topic)
        
        # Формируем список частых ошибок
        common_errors = []
        for topic, data in sorted(topic_errors.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
            error_type = max(data["error_types"].items(), key=lambda x: x[1])[0] if data["error_types"] else "Неизвестная"
            frequency = int((data["count"] / len(students) * 100)) if students else 0
            common_errors.append({
                "topic": topic,
                "students": len(data["students"]),
                "errorType": error_type,
                "frequency": min(frequency, 100)
            })
        
        # Формируем данные о производительности по темам
        topic_performance = []
        for topic in all_topics:
            topic_scores = []
            topic_completions = 0
            for student in students:
                user_id = student.get('user_id')
                if not user_id:
                    continue
                profile = orchestrator.profiler.get_profile(user_id)
                if profile and profile.topic_mastery and topic in profile.topic_mastery:
                    mastery = profile.topic_mastery[topic]
                    topic_scores.append(mastery * 100)
                    if mastery >= 0.7:
                        topic_completions += 1
            
            if topic_scores:
                avg_score = sum(topic_scores) / len(topic_scores)
                completion_rate = (topic_completions / len(students) * 100) if students else 0
                topic_performance.append({
                    "topic": topic,
                    "avgScore": round(avg_score, 0),
                    "completion": round(completion_rate, 0)
                })
        
        # Сортируем по среднему баллу
        topic_performance.sort(key=lambda x: x["avgScore"], reverse=True)
        
        return {
            "classData": class_data,
            "commonErrors": common_errors,
            "topicPerformance": topic_performance[:10],
            "totalStudents": len(class_data),
            "averageScore": round(sum(s["score"] for s in class_data) / len(class_data), 0) if class_data else 0,
            "needsHelpCount": sum(1 for s in class_data if s["status"] == "needs-help")
        }
    except Exception as e:
        print(f"Error in get_class_analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/material", response_model=Dict[str, Any])
async def mark_material_studied(request: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Отметить материал как изученный
    Обновляет topic_mastery и сохраняет историю изучения
    """
    try:
        user_id = request.get("user_id")
        material_id = request.get("material_id")
        topic = request.get("topic")
        subject = request.get("subject", "Математика")
        time_spent_seconds = request.get("time_spent_seconds", 0)
        completion_percentage = request.get("completion_percentage", 1.0)
        
        if not user_id or not material_id or not topic:
            raise HTTPException(status_code=400, detail="user_id, material_id и topic обязательны")
        
        # Получаем профиль ученика
        profile = orchestrator.profiler.get_profile(user_id)
        
        # Создаем запись об изучении
        from models.cognitive_profile import MaterialStudy
        study_record = MaterialStudy(
            material_id=material_id,
            topic=topic,
            subject=subject,
            time_spent_seconds=time_spent_seconds,
            completed=True,
            completion_percentage=completion_percentage
        )
        
        # Добавляем в историю изучения
        profile.material_study_history.append(study_record)
        
        # Обновляем мастерство по теме
        # Если тема уже есть, увеличиваем мастерство
        # Если нет, устанавливаем начальное значение
        if topic not in profile.topic_mastery:
            profile.topic_mastery[topic] = 0.3  # Начальное значение после изучения материала
        else:
            # Увеличиваем мастерство на основе времени изучения и процента завершения
            # Минимум +0.1, максимум +0.2
            mastery_increase = min(0.2, max(0.1, completion_percentage * 0.15))
            profile.topic_mastery[topic] = min(1.0, profile.topic_mastery[topic] + mastery_increase)
        
        # Округляем до 2 знаков
        profile.topic_mastery[topic] = round(profile.topic_mastery[topic], 2)
        
        # Начисляем очки за изучение материала
        points_earned = int(time_spent_seconds / 60) * 2  # 2 очка за каждую минуту изучения
        profile.points += points_earned
        
        # Обновляем уровень
        profile.level = min(profile.points // 100 + 1, 10)
        
        return {
            "success": True,
            "topic_mastery": profile.topic_mastery.get(topic, 0),
            "points_earned": points_earned,
            "total_points": profile.points,
            "level": profile.level
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in mark_material_studied: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/study/progress/{user_id}", response_model=Dict[str, Any])
async def get_study_progress(user_id: str, db: Session = Depends(get_db)):
    """
    Получить прогресс изучения материалов
    """
    try:
        profile = orchestrator.profiler.get_profile(user_id)
        
        # Группируем по темам
        topics_studied = {}
        total_time = 0
        materials_completed = 0
        
        for study in profile.material_study_history:
            if study.completed:
                materials_completed += 1
                total_time += study.time_spent_seconds
                
                if study.topic not in topics_studied:
                    topics_studied[study.topic] = {
                        "materials_count": 0,
                        "total_time": 0,
                        "last_studied": study.timestamp.isoformat() if hasattr(study.timestamp, 'isoformat') else str(study.timestamp)
                    }
                
                topics_studied[study.topic]["materials_count"] += 1
                topics_studied[study.topic]["total_time"] += study.time_spent_seconds
        
        return {
            "total_materials_studied": materials_completed,
            "total_time_minutes": total_time // 60,
            "topics_studied": topics_studied,
            "topic_mastery": profile.topic_mastery
        }
    except Exception as e:
        print(f"Error in get_study_progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{user_id}", response_model=Dict[str, Any])
async def get_recommendations(user_id: str, topic: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Получить рекомендации материалов на основе прогресса ученика
    """
    try:
        profile = orchestrator.profiler.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Определяем тему для рекомендаций
        target_topic = topic
        if not target_topic:
            # Находим самую слабую тему
            if profile.topic_mastery:
                weak_topics = sorted(profile.topic_mastery.items(), key=lambda x: x[1])[:1]
                if weak_topics:
                    target_topic = weak_topics[0][0]
        
        # Маппинг тем к материалам
        topic_to_materials = {
            "Алгебра": [
                {
                    "type": "article",
                    "title": "Основы алгебры: полное руководство",
                    "description": "Систематизация базовых знаний по алгебре: уравнения, неравенства, функции",
                    "relevance": 95,
                    "materialId": "math-algebra-basics"
                },
                {
                    "type": "article",
                    "title": "Методы решения квадратных уравнений",
                    "description": "Дискриминант, формула корней, теорема Виета",
                    "relevance": 88,
                    "materialId": "math-quadratic-eq"
                }
            ],
            "Геометрия": [
                {
                    "type": "article",
                    "title": "Теорема Пифагора: теория и примеры",
                    "description": "Подробное объяснение теоремы с практическими примерами и визуализацией",
                    "relevance": 95,
                    "materialId": "math-pythagorean"
                }
            ],
            "Арифметика": [
                {
                    "type": "pdf",
                    "title": "Дроби: от простого к сложному",
                    "description": "Полный справочник по работе с обыкновенными и десятичными дробями",
                    "relevance": 90,
                    "materialId": "math-fractions-pdf"
                }
            ]
        }
        
        # Если есть конкретная тема, ищем материалы для неё
        materials = []
        if target_topic:
            # Ищем точное совпадение
            if target_topic in topic_to_materials:
                materials = topic_to_materials[target_topic]
            else:
                # Ищем частичное совпадение
                for topic_key, topic_materials in topic_to_materials.items():
                    if topic_key.lower() in target_topic.lower() or target_topic.lower() in topic_key.lower():
                        materials = topic_materials
                        break
        
        # Если не нашли материалы по теме, предлагаем общие
        if not materials:
            # Собираем материалы из всех тем, сортируем по релевантности
            all_materials = []
            for topic_materials in topic_to_materials.values():
                all_materials.extend(topic_materials)
            
            # Если есть слабые темы, повышаем релевантность соответствующих материалов
            if profile.topic_mastery:
                weak_topics = sorted(profile.topic_mastery.items(), key=lambda x: x[1])[:3]
                for weak_topic, mastery in weak_topics:
                    for topic_key, topic_materials in topic_to_materials.items():
                        if topic_key.lower() in weak_topic.lower() or weak_topic.lower() in topic_key.lower():
                            for mat in topic_materials:
                                # Повышаем релевантность на основе слабости темы
                                mat["relevance"] = min(100, mat.get("relevance", 70) + int((0.7 - mastery) * 30))
            
            # Сортируем по релевантности и берем топ-2
            all_materials.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            materials = all_materials[:2]
        
        # Если всё равно нет материалов, даём дефолтные
        if not materials:
            materials = [
                {
                    "type": "article",
                    "title": "Основы алгебры: полное руководство",
                    "description": "Систематизация базовых знаний",
                    "relevance": 85,
                    "materialId": "math-algebra-basics"
                },
                {
                    "type": "video",
                    "title": "Решение задач повышенной сложности",
                    "description": "Видеокурс от ведущих преподавателей",
                    "relevance": 78,
                    "materialId": "math-advanced-problems"
                }
            ]
        
        return {
            "title": f"Рекомендации по теме: {target_topic or 'Общие материалы'}" if target_topic else "Продолжайте в том же духе!",
            "description": "Система подобрала материалы на основе вашего прогресса" if target_topic else "Вы делаете отличные успехи. Система подберет следующее задание для закрепления материала.",
            "materials": materials
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/ratings", response_model=Dict[str, Any])
async def get_materials_ratings(db: Session = Depends(get_db)):
    """
    Получить рейтинги материалов на основе реальных данных
    Рейтинг рассчитывается на основе:
    - Количества учеников, изучивших материал
    - Среднего процента завершения
    - Улучшения topic_mastery после изучения
    - Времени, потраченного на изучение
    """
    try:
        all_profiles = orchestrator.profiler.get_all_profiles()
        
        # Собираем статистику по материалам
        material_stats = defaultdict(lambda: {
            "study_count": 0,
            "total_completion": 0.0,
            "total_time": 0,
            "mastery_improvements": [],
            "topics": set()
        })
        
        # Анализируем историю изучения материалов
        for user_id, profile in all_profiles.items():
            if profile.material_study_history:
                for study in profile.material_study_history:
                    material_id = study.material_id
                    material_stats[material_id]["study_count"] += 1
                    material_stats[material_id]["total_completion"] += study.completion_percentage
                    material_stats[material_id]["total_time"] += study.time_spent_seconds
                    material_stats[material_id]["topics"].add(study.topic)
                    
                    # Проверяем улучшение мастерства по теме
                    if study.topic in profile.topic_mastery:
                        # Ищем мастерство до и после изучения (упрощенно)
                        # В реальной системе нужно хранить mastery до изучения
                        current_mastery = profile.topic_mastery[study.topic]
                        if current_mastery > 0.3:  # Если мастерство выше начального
                            material_stats[material_id]["mastery_improvements"].append(current_mastery)
        
        # Рассчитываем рейтинги для каждого материала
        material_ratings = {}
        
        for material_id, stats in material_stats.items():
            if stats["study_count"] == 0:
                # Если материал не изучался, используем базовый рейтинг
                material_ratings[material_id] = 4.5
                continue
            
            # Средний процент завершения
            avg_completion = stats["total_completion"] / stats["study_count"]
            
            # Среднее время изучения (в минутах)
            avg_time_minutes = (stats["total_time"] / stats["study_count"]) / 60
            
            # Среднее улучшение мастерства
            avg_mastery_improvement = 0.0
            if stats["mastery_improvements"]:
                avg_mastery_improvement = sum(stats["mastery_improvements"]) / len(stats["mastery_improvements"])
            
            # Базовый рейтинг (от 3.0 до 5.0)
            base_rating = 3.0
            
            # Бонусы:
            # 1. За количество изучений (популярность)
            popularity_bonus = min(0.5, stats["study_count"] * 0.05)  # До +0.5 за популярность
            
            # 2. За процент завершения (качество материала)
            completion_bonus = avg_completion * 0.8  # До +0.8 за 100% завершения
            
            # 3. За улучшение мастерства (эффективность)
            mastery_bonus = min(0.5, avg_mastery_improvement * 0.5)  # До +0.5 за эффективность
            
            # 4. За время изучения (адекватность длительности)
            # Если среднее время 10-20 минут - это хорошо
            time_bonus = 0.0
            if 10 <= avg_time_minutes <= 20:
                time_bonus = 0.2
            elif 5 <= avg_time_minutes < 10 or 20 < avg_time_minutes <= 30:
                time_bonus = 0.1
            
            # Итоговый рейтинг
            rating = base_rating + popularity_bonus + completion_bonus + mastery_bonus + time_bonus
            
            # Ограничиваем от 3.0 до 5.0
            rating = max(3.0, min(5.0, rating))
            
            # Округляем до 1 знака после запятой
            material_ratings[material_id] = round(rating, 1)
        
        return {
            "ratings": material_ratings,
            "total_materials": len(material_ratings)
        }
    except Exception as e:
        print(f"Error in get_materials_ratings: {e}")
        import traceback
        traceback.print_exc()
        # Возвращаем пустой словарь при ошибке
        return {
            "ratings": {},
            "total_materials": 0
        }


@router.get("/admin/content-structure", response_model=Dict[str, Any])
async def get_content_structure(db: Session = Depends(get_db)):
    """
    Получить структуру образовательного контента для панели администратора
    Анализирует реальные материалы и задания из системы
    """
    try:
        # Получаем все профили учеников
        all_profiles = orchestrator.profiler.get_all_profiles()
        
        # Собираем статистику по темам из заданий
        topic_stats = defaultdict(lambda: {
            "tasks_count": 0,
            "correct_count": 0,
            "materials_count": 0,
            "subjects": set()
        })
        
        # Анализируем материалы из истории изучения и заданий
        for user_id, profile in all_profiles.items():
            # Анализируем задания
            if profile.task_history:
                for task in profile.task_history:
                    if task.topic:
                        topic_stats[task.topic]["tasks_count"] += 1
                        if task.is_correct:
                            topic_stats[task.topic]["correct_count"] += 1
            
            # Анализируем изученные материалы
            if profile.material_study_history:
                for material in profile.material_study_history:
                    if material.topic:
                        topic_stats[material.topic]["materials_count"] += 1
                        if material.subject:
                            topic_stats[material.topic]["subjects"].add(material.subject)
        
        # Маппинг тем к предметам и разделам (на основе реальных материалов из LibraryTab)
        topic_mapping = {
            "Алгебра": {"subject": "Математика", "section": "Алгебра"},
            "Геометрия": {"subject": "Математика", "section": "Геометрия"},
            "Арифметика": {"subject": "Математика", "section": "Арифметика"},
            "Уравнения": {"subject": "Математика", "section": "Алгебра"},
            "Функции": {"subject": "Математика", "section": "Алгебра"},
            "Неравенства": {"subject": "Математика", "section": "Алгебра"},
            "Треугольники": {"subject": "Математика", "section": "Геометрия"},
            "Окружности": {"subject": "Математика", "section": "Геометрия"},
            "Теорема Пифагора": {"subject": "Математика", "section": "Геометрия"},
            "Квадратные уравнения": {"subject": "Математика", "section": "Алгебра"},
        }
        
        # Формируем структуру контента на основе реальных данных
        subject_structure = defaultdict(lambda: {
            "sections": defaultdict(lambda: {
                "topics": []
            })
        })
        
        # Добавляем темы из реальных данных
        for topic, stats in topic_stats.items():
            mapping = topic_mapping.get(topic, {"subject": "Математика", "section": "Другое"})
            subject = mapping["subject"]
            section = mapping["section"]
            
            # Подсчитываем элементы (материалы + задания)
            elements = stats["materials_count"] + max(1, stats["tasks_count"] // 4)  # Примерно 4 задания = 1 элемент
            
            subject_structure[subject]["sections"][section]["topics"].append({
                "id": abs(hash(topic)) % 10000,  # Простой ID
                "name": topic,
                "elements": max(1, elements),
                "tasks": stats["tasks_count"]
            })
        
        # Добавляем известные материалы из LibraryTab (если их нет в статистике)
        known_materials = {
            "Алгебра": {"subject": "Математика", "section": "Алгебра", "elements": 12},
            "Геометрия": {"subject": "Математика", "section": "Геометрия", "elements": 10},
        }
        
        for topic, info in known_materials.items():
            if topic not in topic_stats:
                subject_structure[info["subject"]]["sections"][info["section"]]["topics"].append({
                    "id": abs(hash(topic)) % 10000,
                    "name": topic,
                    "elements": info["elements"],
                    "tasks": 0
                })
        
        # Преобразуем в нужный формат
        content_structure = []
        for subject_name, subject_data in subject_structure.items():
            sections_list = []
            for section_name, section_data in subject_data["sections"].items():
                if section_data["topics"]:  # Добавляем только если есть темы
                    sections_list.append({
                        "id": abs(hash(f"{subject_name}_{section_name}")) % 10000,
                        "name": section_name,
                        "topics": section_data["topics"]
                    })
            
            if sections_list:  # Добавляем только если есть разделы
                content_structure.append({
                    "id": abs(hash(subject_name)) % 10000,
                    "subject": subject_name,
                    "sections": sections_list
                })
        
        # Проверяем сохраненную структуру контента из админ-панели
        from utils.persistent_storage import persistent_storage
        admin_content = persistent_storage.get("admin_content_structure", None)
        
        # Если есть админ-контент, используем его как основу и дополняем статистикой
        if admin_content and len(admin_content) > 0:
            # Создаем словарь для быстрого поиска статистики по темам
            topic_stats_dict = {topic: stats for topic, stats in topic_stats.items()}
            
            # Обновляем статистику в админ-контенте
            for admin_subject in admin_content:
                for admin_section in admin_subject.get('sections', []):
                    for admin_topic in admin_section.get('topics', []):
                        topic_name = admin_topic.get('name')
                        if topic_name in topic_stats_dict:
                            stats = topic_stats_dict[topic_name]
                            # Обновляем статистику, сохраняя значения из админ-панели если они больше
                            admin_topic['tasks'] = max(admin_topic.get('tasks', 0), stats['tasks_count'])
                            # Обновляем элементы на основе статистики
                            if stats['materials_count'] > 0:
                                admin_topic['elements'] = max(admin_topic.get('elements', 0), stats['materials_count'])
            
            content_structure = admin_content
        # Если нет данных, возвращаем базовую структуру на основе известных материалов
        elif not content_structure:
            content_structure = [
                {
                    "id": 1,
                    "subject": "Математика",
                    "sections": [
                        {
                            "id": 11,
                            "name": "Алгебра",
                            "topics": [
                                {"id": 111, "name": "Уравнения", "elements": 12, "tasks": 0},
                                {"id": 112, "name": "Функции", "elements": 8, "tasks": 0},
                                {"id": 113, "name": "Неравенства", "elements": 6, "tasks": 0}
                            ]
                        },
                        {
                            "id": 12,
                            "name": "Геометрия",
                            "topics": [
                                {"id": 121, "name": "Треугольники", "elements": 10, "tasks": 0},
                                {"id": 122, "name": "Окружности", "elements": 7, "tasks": 0}
                            ]
                        }
                    ]
                }
            ]
        
        return {
            "structure": content_structure,
            "total_subjects": len(content_structure),
            "total_sections": sum(len(s["sections"]) for s in content_structure),
            "total_topics": sum(len(sec["topics"]) for s in content_structure for sec in s["sections"])
        }
    except Exception as e:
        print(f"Error in get_content_structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== ADMIN USER MANAGEMENT ==========

class UserCreateRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str  # student, teacher, admin
    class_id: Optional[str] = None
    phone: Optional[str] = None
    parent_fio: Optional[str] = None
    parent_phone: Optional[str] = None


# Данные для сидирования БД (то же, что в scripts/seed_db.py)
_SEED_STUDENT_NAMES = [
    "Иванов Алексей", "Петрова Мария", "Сидоров Дмитрий", "Козлова Анна",
    "Новиков Иван", "Морозова Елена", "Волков Павел", "Соколова Ольга",
    "Лебедев Сергей", "Кузнецова Татьяна", "Попов Николай", "Васильева Ирина",
    "Федоров Андрей", "Михайлова Наталья", "Андреев Александр", "Егорова Светлана",
]
_SEED_PARENT_NAMES = [
    "Иванов Иван Петрович", "Петрова Ольга Сергеевна", "Сидоров Петр Иванович",
    "Козлова Елена Викторовна", "Новиков Дмитрий Александрович", "Морозова Анна Дмитриевна",
    "Волков Сергей Николаевич", "Соколова Мария Павловна", "Лебедев Андрей Иванович",
    "Кузнецова Татьяна Сергеевна", "Попов Николай Владимирович", "Васильева Ирина Андреевна",
    "Федоров Александр Петрович", "Михайлова Наталья Олеговна", "Андреев Павел Сергеевич",
    "Егорова Светлана Дмитриевна",
]
_SEED_PHONES = [
    "+7 916 111-22-33", "+7 926 222-33-44", "+7 903 333-44-55", "+7 905 444-55-66",
    "+7 495 555-66-77", "+7 499 666-77-88", "+7 916 777-88-99", "+7 926 888-99-00",
    "+7 903 999-00-11", "+7 905 100-11-22", "+7 495 200-22-33", "+7 499 300-33-44",
    "+7 916 400-44-55", "+7 926 500-55-66", "+7 903 600-66-77", "+7 905 700-77-88",
]
_SEED_CLASSES = ["10А", "10Б", "11А", "9А", "9Б"]
_SEED_TEACHER_NAMES = [
    "Смирнова Елена Викторовна", "Кузнецов Михаил Сергеевич", "Павлова Анна Александровна",
    "Семенов Игорь Николаевич", "Голубева Ольга Дмитриевна",
]


@router.post("/admin/seed", response_model=Dict[str, Any])
async def admin_seed_db(current_user: dict = Depends(get_current_user)):
    """
    Заполнить БД тестовыми учениками и учителями (только для админа).
    Вызывайте этот endpoint один раз после деплоя на Railway — пользователи создадутся
    в вашей Railway Postgres. В ответе вернётся список email и паролей.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    import random
    import string
    from utils.auth_service import auth_service
    from models.auth import UserRole

    def _random_password():
        return "".join(random.choices(string.ascii_letters + string.digits, k=10))

    credentials = []
    base_student = 100
    base_teacher = 50

    for i, name in enumerate(_SEED_STUDENT_NAMES):
        email = f"student{base_student + i + 1}@adapted.local"
        password = _random_password()
        class_id = _SEED_CLASSES[i % len(_SEED_CLASSES)]
        parent_fio = _SEED_PARENT_NAMES[i % len(_SEED_PARENT_NAMES)]
        parent_phone = _SEED_PHONES[i % len(_SEED_PHONES)]
        user = auth_service.register_user(
            email=email,
            password=password,
            full_name=name,
            role=UserRole.STUDENT,
            class_id=class_id,
            phone=_SEED_PHONES[(i + 1) % len(_SEED_PHONES)],
            parent_fio=parent_fio,
            parent_phone=parent_phone,
        )
        if user:
            credentials.append({
                "role": "Ученик",
                "name": name,
                "email": email,
                "password": password,
                "class_id": class_id,
                "parent_fio": parent_fio,
                "parent_phone": parent_phone,
            })

    for i, name in enumerate(_SEED_TEACHER_NAMES):
        email = f"teacher{base_teacher + i + 1}@adapted.local"
        password = _random_password()
        user = auth_service.register_user(
            email=email,
            password=password,
            full_name=name,
            role=UserRole.TEACHER,
            class_id=None,
            phone=_SEED_PHONES[(i + 5) % len(_SEED_PHONES)],
        )
        if user:
            credentials.append({
                "role": "Учитель",
                "name": name,
                "email": email,
                "password": password,
                "class_id": None,
                "parent_fio": None,
                "parent_phone": None,
            })

    return {
        "message": "База заполнена. Ниже список созданных учётных записей (уже существующие email пропущены).",
        "created": len(credentials),
        "credentials": credentials,
    }


@router.post("/admin/users", response_model=Dict[str, Any])
async def create_user(user_data: UserCreateRequest, db: Session = Depends(get_db)):
    """Создать нового пользователя (админ)"""
    try:
        from utils.auth_service import auth_service
        from models.auth import UserRole
        
        # Проверяем, существует ли пользователь
        all_users = auth_service.get_all_users()
        for user in all_users:
            if user.get('email') == user_data.email:
                raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
        
        # Создаем пользователя
        role = UserRole(user_data.role) if user_data.role in ['student', 'teacher', 'admin'] else UserRole.STUDENT
        user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=role,
            class_id=user_data.class_id,
            phone=user_data.phone,
            parent_fio=user_data.parent_fio,
            parent_phone=user_data.parent_phone
        )
        
        if not user:
            raise HTTPException(status_code=500, detail="Не удалось создать пользователя")
        
        return {
            "id": user.user_id,
            "name": user.full_name,
            "email": user.email,
            "role": user.role.value,
            "status": "active" if user.is_active else "inactive"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/users/{user_id}", response_model=Dict[str, Any])
async def update_admin_user(user_id: str, updates: Dict[str, Any], db: Session = Depends(get_db)):
    """Обновить данные пользователя (админ)"""
    try:
        from utils.auth_service import auth_service
        from utils.db import get_db as get_db_session
        from models.user_db import User as UserDB
        
        # Пробуем обновить в БД
        if has_db():
            db_session = get_db_session()
            if db_session:
                try:
                    user_db = db_session.query(UserDB).filter(UserDB.user_id == user_id).first()
                    if not user_db:
                        raise HTTPException(status_code=404, detail="Пользователь не найден")
                    
                    if 'full_name' in updates:
                        user_db.full_name = updates['full_name']
                    if 'email' in updates:
                        user_db.email = updates['email']
                    if 'role' in updates:
                        user_db.role = updates['role']
                    if 'class_id' in updates:
                        user_db.class_id = updates['class_id']
                    if 'phone' in updates:
                        user_db.phone = updates['phone']
                    if 'parent_fio' in updates:
                        user_db.parent_fio = updates['parent_fio']
                    if 'parent_phone' in updates:
                        user_db.parent_phone = updates['parent_phone']
                    if 'is_active' in updates:
                        user_db.is_active = updates['is_active']
                    
                    db_session.commit()
                    
                    return {
                        "id": user_db.user_id,
                        "name": user_db.full_name,
                        "email": user_db.email,
                        "role": user_db.role,
                        "status": "active" if user_db.is_active else "inactive"
                    }
                except HTTPException:
                    raise
                except Exception as e:
                    db_session.rollback()
                    print(f"Error updating user in DB: {e}")
                finally:
                    db_session.close()
        
        # Fallback на persistent_storage
        from utils.persistent_storage import persistent_storage
        users = persistent_storage.get("users", {})
        if user_id not in users:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        user = users[user_id]
        for key, value in updates.items():
            if key in ['full_name', 'email', 'role', 'class_id', 'phone', 'parent_fio', 'parent_phone', 'is_active']:
                user[key] = value
        
        persistent_storage.set("users", users)
        
        return {
            "id": user_id,
            "name": user.get('full_name', ''),
            "email": user.get('email', ''),
            "role": user.get('role', 'student'),
            "status": "active" if user.get('is_active', True) else "inactive"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_admin_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/users/{user_id}/password", response_model=Dict[str, Any])
async def set_user_password_admin(user_id: str, body: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Сменить пароль пользователя (только админ; админ может менять и свой пароль)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может менять пароли")
    try:
        new_password = (body.get("new_password") or "").strip()
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="Пароль должен быть не короче 6 символов")
        from utils.auth_service import auth_service
        ok = auth_service.set_user_password(user_id, new_password)
        if not ok:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return {"message": "Пароль успешно изменён"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in set_user_password_admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/users/{user_id}", response_model=Dict[str, Any])
async def delete_admin_user(user_id: str, db: Session = Depends(get_db)):
    """Удалить пользователя (админ)"""
    try:
        from utils.db import get_db as get_db_session
        from models.user_db import User as UserDB
        
        # Пробуем удалить из БД
        if has_db():
            db_session = get_db_session()
            if db_session:
                try:
                    user_db = db_session.query(UserDB).filter(UserDB.user_id == user_id).first()
                    if not user_db:
                        raise HTTPException(status_code=404, detail="Пользователь не найден")
                    
                    # Не удаляем, а деактивируем
                    user_db.is_active = False
                    db_session.commit()
                    
                    return {
                        "id": user_id,
                        "message": "Пользователь деактивирован"
                    }
                except HTTPException:
                    raise
                except Exception as e:
                    db_session.rollback()
                    print(f"Error deleting user from DB: {e}")
                finally:
                    db_session.close()
        
        # Fallback на persistent_storage
        from utils.persistent_storage import persistent_storage
        users = persistent_storage.get("users", {})
        if user_id not in users:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Деактивируем вместо удаления
        users[user_id]['is_active'] = False
        persistent_storage.set("users", users)
        
        return {
            "id": user_id,
            "message": "Пользователь деактивирован"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_admin_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== ADMIN CONTENT MANAGEMENT ==========

class ContentSubjectCreate(BaseModel):
    subject: str


class ContentSectionCreate(BaseModel):
    subject_id: int
    name: str


class ContentTopicCreate(BaseModel):
    section_id: int
    name: str


@router.post("/admin/content/subject", response_model=Dict[str, Any])
async def create_subject(data: ContentSubjectCreate, db: Session = Depends(get_db)):
    """Создать новый предмет"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        # Генерируем ID
        max_id = max([s.get('id', 0) for s in content_structure], default=0)
        new_id = max_id + 1
        
        new_subject = {
            "id": new_id,
            "subject": data.subject,
            "sections": []
        }
        
        content_structure.append(new_subject)
        persistent_storage.set("admin_content_structure", content_structure)
        
        return new_subject
    except Exception as e:
        print(f"Error in create_subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/content/subject/{subject_id}", response_model=Dict[str, Any])
async def update_subject(subject_id: int, data: Dict[str, Any], db: Session = Depends(get_db)):
    """Обновить предмет"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        subject = next((s for s in content_structure if s.get('id') == subject_id), None)
        if not subject:
            raise HTTPException(status_code=404, detail="Предмет не найден")
        
        if 'subject' in data:
            subject['subject'] = data['subject']
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return subject
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/content/subject/{subject_id}", response_model=Dict[str, Any])
async def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    """Удалить предмет"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        subject = next((s for s in content_structure if s.get('id') == subject_id), None)
        if not subject:
            raise HTTPException(status_code=404, detail="Предмет не найден")
        
        content_structure = [s for s in content_structure if s.get('id') != subject_id]
        persistent_storage.set("admin_content_structure", content_structure)
        
        return {"message": "Предмет удален", "id": subject_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/content/section", response_model=Dict[str, Any])
async def create_section(data: ContentSectionCreate, db: Session = Depends(get_db)):
    """Создать новый раздел"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        subject = next((s for s in content_structure if s.get('id') == data.subject_id), None)
        if not subject:
            raise HTTPException(status_code=404, detail="Предмет не найден")
        
        # Генерируем ID
        max_id = max([sec.get('id', 0) for sec in subject.get('sections', [])], default=0)
        new_id = max(max_id + 1, data.subject_id * 10 + len(subject.get('sections', [])) + 1)
        
        new_section = {
            "id": new_id,
            "name": data.name,
            "topics": []
        }
        
        if 'sections' not in subject:
            subject['sections'] = []
        subject['sections'].append(new_section)
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return new_section
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_section: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/content/section/{section_id}", response_model=Dict[str, Any])
async def update_section(section_id: int, data: Dict[str, Any], db: Session = Depends(get_db)):
    """Обновить раздел"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        section = None
        for subject in content_structure:
            for sec in subject.get('sections', []):
                if sec.get('id') == section_id:
                    section = sec
                    break
            if section:
                break
        
        if not section:
            raise HTTPException(status_code=404, detail="Раздел не найден")
        
        if 'name' in data:
            section['name'] = data['name']
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return section
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_section: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/content/section/{section_id}", response_model=Dict[str, Any])
async def delete_section(section_id: int, db: Session = Depends(get_db)):
    """Удалить раздел"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        for subject in content_structure:
            subject['sections'] = [sec for sec in subject.get('sections', []) if sec.get('id') != section_id]
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return {"message": "Раздел удален", "id": section_id}
    except Exception as e:
        print(f"Error in delete_section: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/content/topic", response_model=Dict[str, Any])
async def create_topic(data: ContentTopicCreate, db: Session = Depends(get_db)):
    """Создать новую тему"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        section = None
        for subject in content_structure:
            for sec in subject.get('sections', []):
                if sec.get('id') == data.section_id:
                    section = sec
                    break
            if section:
                break
        
        if not section:
            raise HTTPException(status_code=404, detail="Раздел не найден")
        
        # Генерируем ID
        max_id = max([t.get('id', 0) for t in section.get('topics', [])], default=0)
        new_id = max(max_id + 1, data.section_id * 10 + len(section.get('topics', [])) + 1)
        
        new_topic = {
            "id": new_id,
            "name": data.name,
            "elements": 0,
            "tasks": 0
        }
        
        if 'topics' not in section:
            section['topics'] = []
        section['topics'].append(new_topic)
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return new_topic
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/content/topic/{topic_id}", response_model=Dict[str, Any])
async def update_topic(topic_id: int, data: Dict[str, Any], db: Session = Depends(get_db)):
    """Обновить тему"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        topic = None
        for subject in content_structure:
            for section in subject.get('sections', []):
                for top in section.get('topics', []):
                    if top.get('id') == topic_id:
                        topic = top
                        break
                if topic:
                    break
            if topic:
                break
        
        if not topic:
            raise HTTPException(status_code=404, detail="Тема не найдена")
        
        if 'name' in data:
            topic['name'] = data['name']
        if 'elements' in data:
            topic['elements'] = data['elements']
        if 'tasks' in data:
            topic['tasks'] = data['tasks']
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return topic
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/content/topic/{topic_id}", response_model=Dict[str, Any])
async def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Удалить тему"""
    try:
        from utils.persistent_storage import persistent_storage
        
        content_structure = persistent_storage.get("admin_content_structure", [])
        
        for subject in content_structure:
            for section in subject.get('sections', []):
                section['topics'] = [t for t in section.get('topics', []) if t.get('id') != topic_id]
        
        persistent_storage.set("admin_content_structure", content_structure)
        
        return {"message": "Тема удалена", "id": topic_id}
    except Exception as e:
        print(f"Error in delete_topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TopicTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


@router.post("/admin/content/topic/{topic_id}/task", response_model=Dict[str, Any])
async def add_topic_task(topic_id: int, data: TopicTaskCreate, db: Session = Depends(get_db)):
    """Добавить задание к теме"""
    try:
        from utils.persistent_storage import persistent_storage
        
        key = "admin_topic_tasks"
        tasks_by_topic = persistent_storage.get(key, {})
        topic_key = f"topic_{topic_id}"
        tasks = list(tasks_by_topic.get(topic_key, []))
        new_id = max([t.get("id", 0) for t in tasks], default=0) + 1
        tasks.append({
            "id": new_id,
            "title": data.title,
            "description": data.description or "",
        })
        tasks_by_topic[topic_key] = tasks
        persistent_storage.set(key, tasks_by_topic)
        
        # Обновить счётчик заданий в структуре контента
        content_structure = persistent_storage.get("admin_content_structure", [])
        for subject in content_structure:
            for section in subject.get("sections", []):
                for topic in section.get("topics", []):
                    if topic.get("id") == topic_id:
                        topic["tasks"] = topic.get("tasks", 0) + 1
                        break
        persistent_storage.set("admin_content_structure", content_structure)
        
        return {"message": "Задание добавлено", "id": new_id, "topic_id": topic_id}
    except Exception as e:
        print(f"Error in add_topic_task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== ADMIN SYSTEM SETTINGS ==========

class SystemSettings(BaseModel):
    adaptation_strategy: Optional[str] = "balanced"
    target_mastery_percent: Optional[int] = 80
    attempts_before_strategy_change: Optional[int] = 3
    gigachat_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_index: Optional[str] = None


@router.post("/admin/settings", response_model=Dict[str, Any])
async def save_system_settings(settings: SystemSettings, db: Session = Depends(get_db)):
    """Сохранить настройки системы"""
    try:
        from utils.persistent_storage import persistent_storage
        
        current_settings = persistent_storage.get("admin_system_settings", {})
        
        settings_dict = settings.dict(exclude_none=True)
        current_settings.update(settings_dict)
        
        persistent_storage.set("admin_system_settings", current_settings)
        
        return {
            "message": "Настройки сохранены",
            "settings": current_settings
        }
    except Exception as e:
        print(f"Error in save_system_settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/settings", response_model=Dict[str, Any])
async def get_system_settings(db: Session = Depends(get_db)):
    """Получить настройки системы"""
    try:
        from utils.persistent_storage import persistent_storage
        
        settings = persistent_storage.get("admin_system_settings", {
            "adaptation_strategy": "balanced",
            "target_mastery_percent": 80,
            "attempts_before_strategy_change": 3,
            "gigachat_api_key": "",
            "pinecone_api_key": "",
            "pinecone_index": ""
        })
        return {**{
            "adaptation_strategy": "balanced",
            "target_mastery_percent": 80,
            "attempts_before_strategy_change": 3,
            "gigachat_api_key": "",
            "pinecone_api_key": "",
            "pinecone_index": ""
        }, **settings}
    except Exception as e:
        print(f"Error in get_system_settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/materials/upload", response_model=Dict[str, Any])
async def upload_materials(
    title: str,
    content: str,
    topic: Optional[str] = None,
    subject: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Загрузить образовательный материал"""
    try:
        from models.document import Document
        from utils.db import get_db as get_db_session
        
        if has_db():
            db_session = get_db_session()
            if db_session:
                try:
                    doc = Document(
                        title=title,
                        content=content
                    )
                    db_session.add(doc)
                    db_session.commit()
                    db_session.refresh(doc)
                    
                    return {
                        "id": doc.id,
                        "title": doc.title,
                        "message": "Материал успешно загружен"
                    }
                except Exception as e:
                    db_session.rollback()
                    print(f"Error uploading material to DB: {e}")
                finally:
                    db_session.close()
        
        # Fallback на persistent_storage
        from utils.persistent_storage import persistent_storage
        
        materials = persistent_storage.get("admin_materials", [])
        new_id = len(materials) + 1
        
        new_material = {
            "id": new_id,
            "title": title,
            "content": content,
            "topic": topic,
            "subject": subject,
            "created_at": datetime.now().isoformat()
        }
        
        materials.append(new_material)
        persistent_storage.set("admin_materials", materials)
        
        return {
            "id": new_id,
            "title": title,
            "message": "Материал успешно загружен"
        }
    except Exception as e:
        print(f"Error in upload_materials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

