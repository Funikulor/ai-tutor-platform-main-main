from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.debts import StudentDebt
from models.homework import Homework
from models.test import TestSubmission, Test
from routes.auth import assert_can_view_user_data, get_current_user, require_roles
from services.student_analytics import get_analytics_service
from utils.auth_service import auth_service
from utils.db import get_db, has_db
from utils.orchestrator_singleton import get_orchestrator

router = APIRouter()


class AssignRemedialBody(BaseModel):
    topic: str
    kind: str = Field(..., description="adaptive_task | material | course")
    attempts_required: int = 2
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    debt_id: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class AssignLibraryBody(BaseModel):
    kind: str = Field(..., description="material | course")
    material_id: Optional[str] = None
    course_id: Optional[str] = None
    title: Optional[str] = None
    topic: Optional[str] = None
    due_date: Optional[datetime] = None
    debt_id: Optional[int] = None


def _serialize_debt(debt: StudentDebt) -> Dict[str, Any]:
    return {
        "id": debt.id,
        "user_id": debt.user_id,
        "topic": debt.topic,
        "source_type": debt.source_type,
        "source_id": debt.source_id,
        "status": debt.status,
        "priority": debt.priority,
        "progress": round(float(debt.progress or 0.0), 1),
        "due_date": debt.due_date.isoformat() if debt.due_date else None,
        "target_accuracy": debt.target_accuracy,
        "created_by": debt.created_by,
        "notes": debt.notes,
        "created_at": debt.created_at.isoformat() if debt.created_at else None,
        "updated_at": debt.updated_at.isoformat() if debt.updated_at else None,
        "resolved_at": debt.resolved_at.isoformat() if debt.resolved_at else None,
    }


def _extract_submission_points(submission: TestSubmission) -> Dict[str, int]:
    question_results = submission.question_results or []
    if question_results:
        earned = sum(int(item.get("earned_points", 0) or 0) for item in question_results)
        maximum = sum(int(item.get("max_points", 0) or 0) for item in question_results)
        if maximum > 0:
            return {"earned": earned, "max": maximum}
    return {
        "earned": int(getattr(submission, "correct_count", 0) or 0),
        "max": int(getattr(submission, "total_questions", 0) or 0),
    }


def _student_rating_row(db: Session, student: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(student.get("user_id", ""))
    profile = get_orchestrator().profiler.get_profile(user_id)
    submissions = db.execute(select(TestSubmission).where(TestSubmission.user_id == user_id)).scalars().all()
    earned_points = 0
    max_points = 0
    for submission in submissions:
        points = _extract_submission_points(submission)
        earned_points += points["earned"]
        max_points += points["max"]
    point_ratio = round((earned_points / max_points) * 100.0, 1) if max_points else round(float(getattr(profile, "accuracy_rate", 0.0) or 0.0), 1)

    homeworks = db.execute(select(Homework).where(Homework.assigned_to == user_id)).scalars().all()
    active_homeworks = [h for h in homeworks if h.status in ("new", "in_progress")]
    overdue_homeworks = [
        h for h in active_homeworks
        if h.due_date and h.due_date < datetime.utcnow()
    ]
    completed_homeworks = [h for h in homeworks if h.status in ("submitted", "checked")]
    homework_completion = round((len(completed_homeworks) / len(homeworks) * 100.0), 1) if homeworks else 0.0

    status = "опережает" if point_ratio >= 80 else ("в норме" if point_ratio >= 60 else "риски отставания")
    return {
        "user_id": user_id,
        "student": student.get("full_name") or student.get("email") or user_id,
        "earned_points": earned_points,
        "max_points": max_points,
        "score": point_ratio,
        "homework_completion": homework_completion,
        "rating": point_ratio,
        "status": status,
        "active_assignments": len(active_homeworks),
        "overdue_assignments": len(overdue_homeworks),
    }


def _sync_overdue_homework_debts(db: Session, user_id: str) -> None:
    return None


@router.get("/teacher/class-rating")
async def get_teacher_class_rating(
    class_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    students = [u for u in auth_service.get_all_users() if u.get("role") == "student"]
    if class_id:
        students = [u for u in students if u.get("class_id") == class_id]

    rows = [_student_rating_row(db, student) for student in students if student.get("user_id")]
    rows.sort(key=lambda x: x["rating"], reverse=True)
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
    return {"rows": rows, "class_id": class_id or "all"}


@router.get("/teacher/student-card/{user_id}")
async def get_teacher_student_card(
    user_id: str,
    db: Session = Depends(get_db),
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    student = auth_service.get_user_by_id(user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    profile = get_orchestrator().profiler.get_profile(user_id)
    analytics = get_analytics_service().get_analytics(user_id)
    submissions = (
        db.execute(select(TestSubmission).where(TestSubmission.user_id == user_id).order_by(TestSubmission.created_at.desc()))
        .scalars()
        .all()
    )
    homeworks = (
        db.execute(select(Homework).where(Homework.assigned_to == user_id).order_by(Homework.created_at.desc()))
        .scalars()
        .all()
    )

    strengths = []
    weaknesses = []
    if profile and profile.topic_mastery:
        for topic, mastery in profile.topic_mastery.items():
            if mastery >= 0.75:
                strengths.append({"topic": topic, "mastery": round(float(mastery) * 100, 1)})
            elif mastery < 0.5:
                weaknesses.append({"topic": topic, "mastery": round(float(mastery) * 100, 1)})
    strengths = sorted(strengths, key=lambda x: x["mastery"], reverse=True)[:6]
    weaknesses = sorted(weaknesses, key=lambda x: x["mastery"])[:6]

    rating_snapshot = _student_rating_row(db, student)
    active_test_assignments = []
    for hw in homeworks:
        if hw.test_id is None or hw.status not in ("new", "in_progress", "submitted", "checked"):
            continue
        test = db.get(Test, hw.test_id) if hw.test_id else None
        active_test_assignments.append({
            "homework_id": hw.id,
            "test_id": hw.test_id,
            "title": hw.title,
            "status": hw.status,
            "assignment_type": hw.assignment_type,
            "due_date": hw.due_date.isoformat() if hw.due_date else None,
            "test_title": test.title if test else hw.title,
            "max_points": sum(
                int((question.correct_answer or {}).get("points", 1))
                if isinstance(question.correct_answer, dict) else 1
                for question in (test.questions if test else [])
            ),
        })

    return {
        "student": {
            "user_id": user_id,
            "full_name": student.get("full_name"),
            "email": student.get("email"),
            "class_id": student.get("class_id"),
        },
        "stats": {
            "points": getattr(profile, "points", 0) if profile else 0,
            "level": getattr(profile, "level", 1) if profile else 1,
            "accuracy_rate": round(float(getattr(profile, "accuracy_rate", 0.0) or 0.0), 1) if profile else 0.0,
            "total_tasks": getattr(profile, "total_tasks_completed", 0) if profile else 0,
            "correct_tasks": getattr(profile, "correct_tasks_count", 0) if profile else 0,
            "earned_points": rating_snapshot["earned_points"],
            "max_points": rating_snapshot["max_points"],
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "analytics": analytics,
        "recent_test_submissions": [
            {
                "id": sub.id,
                "score": sub.score,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "correct_count": sub.correct_count,
                "total_questions": sub.total_questions,
                "earned_points": _extract_submission_points(sub)["earned"],
                "max_points": _extract_submission_points(sub)["max"],
            }
            for sub in submissions[:10]
        ],
        "recent_homeworks": [
            {
                "id": hw.id,
                "title": hw.title,
                "status": hw.status,
                "kind": hw.kind,
                "assignment_type": hw.assignment_type,
                "due_date": hw.due_date.isoformat() if hw.due_date else None,
            }
            for hw in homeworks[:10]
        ],
        "active_test_assignments": active_test_assignments[:10],
        "rating": rating_snapshot,
    }


@router.get("/teacher/students/{user_id}/debts")
async def get_teacher_student_debts(
    user_id: str,
    include_resolved: bool = True,
    db: Session = Depends(get_db),
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    return {"user_id": user_id, "debts": []}


@router.post("/teacher/students/{user_id}/debts/assign-remedial")
async def assign_remedial(
    user_id: str,
    body: AssignRemedialBody,
    db: Session = Depends(get_db),
    staff: dict = Depends(require_roles("teacher", "admin")),
):
    raise HTTPException(status_code=410, detail="Механика долгов отключена")


@router.post("/teacher/students/{user_id}/assign-library")
async def assign_library_to_student(
    user_id: str,
    body: AssignLibraryBody,
    db: Session = Depends(get_db),
    staff: dict = Depends(require_roles("teacher", "admin")),
):
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    if body.kind not in {"material", "course"}:
        raise HTTPException(status_code=400, detail="kind must be material or course")

    teacher_id = str(staff.get("user_id", "teacher"))
    title = body.title or ("Прочитать материал" if body.kind == "material" else "Пройти курс")
    hw = Homework(
        title=title,
        description=f"Назначение из библиотеки: {body.topic or ''}".strip(),
        subject=body.topic or "Библиотека",
        due_date=body.due_date,
        kind=body.kind,
        test_id=None,
        material_id=body.material_id if body.kind == "material" else None,
        course_id=body.course_id if body.kind == "course" else None,
        adaptive_topic=body.topic,
        debt_id=body.debt_id,
        completion_required=1.0,
        assignment_type="remedial",
        status="new",
        assigned_to=user_id,
        created_by=teacher_id,
    )
    db.add(hw)
    db.commit()
    db.refresh(hw)
    return {
        "ok": True,
        "homework_id": hw.id,
        "kind": hw.kind,
        "material_id": hw.material_id,
        "course_id": hw.course_id,
    }


@router.get("/student/debts")
async def get_student_debts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("user_id", ""))
    assert_can_view_user_data(current_user, user_id)
    return {"user_id": user_id, "debts": []}


@router.post("/student/debts/{debt_id}/progress")
async def mark_student_debt_progress(
    debt_id: int,
    progress_delta: float = 25.0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    raise HTTPException(status_code=410, detail="Механика долгов отключена")
