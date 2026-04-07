from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.debts import StudentDebt
from models.homework import Homework
from models.test import TestSubmission
from routes.auth import assert_can_view_user_data, get_current_user, require_roles
from services.debts_service import get_debts_service
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


def _student_rating_row(db: Session, student: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(student.get("user_id", ""))
    profile = get_orchestrator().profiler.get_profile(user_id)
    profile_accuracy = float(getattr(profile, "accuracy_rate", 0.0) or 0.0)

    submissions = db.execute(select(TestSubmission).where(TestSubmission.user_id == user_id)).scalars().all()
    test_scores = [float(s.score or 0.0) for s in submissions]
    test_score = sum(test_scores) / len(test_scores) if test_scores else profile_accuracy

    homeworks = db.execute(select(Homework).where(Homework.assigned_to == user_id)).scalars().all()
    due_homeworks = [h for h in homeworks if h.due_date]
    on_time_count = 0
    for hw in due_homeworks:
        if hw.status in ("submitted", "checked"):
            on_time_count += 1
    homework_score = (on_time_count / len(due_homeworks) * 100.0) if due_homeworks else 100.0

    debts = db.query(StudentDebt).filter(StudentDebt.user_id == user_id).all()
    if debts:
        resolved = sum(1 for d in debts if d.status == "resolved")
        avg_progress = sum(float(d.progress or 0.0) for d in debts) / len(debts)
        debt_score = (resolved / len(debts) * 60.0) + (avg_progress * 0.4)
    else:
        debt_score = 100.0

    total = round((test_score * 0.45) + (homework_score * 0.25) + (debt_score * 0.30), 1)
    status = "опережает" if total >= 80 else ("в норме" if total >= 60 else "риски отставания")
    return {
        "user_id": user_id,
        "student": student.get("full_name") or student.get("email") or user_id,
        "test_score": round(test_score, 1),
        "homework_score": round(homework_score, 1),
        "debt_score": round(debt_score, 1),
        "rating": total,
        "status": status,
        "debts_total": len(debts),
        "debts_open": sum(1 for d in debts if d.status != "resolved"),
    }


def _sync_overdue_homework_debts(db: Session, user_id: str) -> None:
    debt_service = get_debts_service()
    now = datetime.utcnow()
    rows = (
        db.query(Homework)
        .filter(
            Homework.assigned_to == user_id,
            Homework.due_date.isnot(None),
            Homework.due_date < now,
            Homework.status.in_(["new", "in_progress"]),
        )
        .all()
    )
    for hw in rows:
        debt_service.upsert_topic_debt(
            db=db,
            user_id=user_id,
            topic=(hw.subject or hw.adaptive_topic or hw.title or "Домашние задания"),
            source_type="homework",
            source_id=str(hw.id),
            created_by=hw.created_by or "system",
            priority=1,
            notes=f"Просрочено задание: {hw.title}",
            due_date=hw.due_date,
        )


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
    for student in students:
        uid = str(student.get("user_id", ""))
        if uid:
            _sync_overdue_homework_debts(db, uid)
    db.commit()

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
    debts = db.query(StudentDebt).filter(StudentDebt.user_id == user_id).order_by(StudentDebt.created_at.desc()).all()
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
    _sync_overdue_homework_debts(db, user_id)
    db.commit()

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
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "analytics": analytics,
        "debts": [_serialize_debt(d) for d in debts],
        "recent_test_submissions": [
            {
                "id": sub.id,
                "score": sub.score,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "correct_count": sub.correct_count,
                "total_questions": sub.total_questions,
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
        "rating": rating_snapshot,
    }


@router.get("/teacher/students/{user_id}/debts")
async def get_teacher_student_debts(
    user_id: str,
    include_resolved: bool = True,
    db: Session = Depends(get_db),
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    service = get_debts_service()
    debts = service.list_debts(db, user_id=user_id, include_resolved=include_resolved)
    return {"user_id": user_id, "debts": [_serialize_debt(d) for d in debts]}


@router.post("/teacher/students/{user_id}/debts/assign-remedial")
async def assign_remedial(
    user_id: str,
    body: AssignRemedialBody,
    db: Session = Depends(get_db),
    staff: dict = Depends(require_roles("teacher", "admin")),
):
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    service = get_debts_service()
    teacher_id = str(staff.get("user_id", "teacher"))
    debt = db.get(StudentDebt, body.debt_id) if body.debt_id else None
    if debt is None:
        debt = service.upsert_topic_debt(
            db=db,
            user_id=user_id,
            topic=body.topic,
            source_type="manual",
            created_by=teacher_id,
            priority=1,
            notes=body.notes,
            due_date=body.due_date,
        )
    assignment = service.create_remedial_assignment(
        db=db,
        debt_id=debt.id,
        user_id=user_id,
        kind=body.kind,
        payload=body.payload or {"topic": body.topic},
        created_by=teacher_id,
        attempts_required=body.attempts_required,
        due_date=body.due_date,
    )
    db.commit()
    return {
        "ok": True,
        "debt": _serialize_debt(debt),
        "assignment": {
            "id": assignment.id,
            "kind": assignment.kind,
            "payload": assignment.payload,
            "attempts_required": assignment.attempts_required,
            "status": assignment.status,
        },
    }


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
    if body.debt_id:
        try:
            get_debts_service().create_remedial_assignment(
                db=db,
                debt_id=body.debt_id,
                user_id=user_id,
                kind=body.kind,
                payload={
                    "material_id": body.material_id,
                    "course_id": body.course_id,
                    "topic": body.topic,
                    "homework_id": None,
                },
                created_by=teacher_id,
                attempts_required=1,
                due_date=body.due_date,
            )
        except Exception as e:
            print(f"Error creating remedial assignment from library assignment: {e}")
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
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    user_id = str(current_user.get("user_id", ""))
    assert_can_view_user_data(current_user, user_id)
    service = get_debts_service()
    debts = service.list_debts(db, user_id=user_id, include_resolved=True)
    return {"user_id": user_id, "debts": [_serialize_debt(d) for d in debts]}


@router.post("/student/debts/{debt_id}/progress")
async def mark_student_debt_progress(
    debt_id: int,
    progress_delta: float = 25.0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not has_db() or db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    user_id = str(current_user.get("user_id", ""))
    debt = db.get(StudentDebt, debt_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    assert_can_view_user_data(current_user, debt.user_id)
    debt.progress = max(0.0, min(100.0, float(debt.progress or 0.0) + progress_delta))
    debt.status = "resolved" if debt.progress >= 100.0 else "in_progress"
    debt.updated_at = datetime.utcnow()
    if debt.status == "resolved":
        debt.resolved_at = datetime.utcnow()
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return {"ok": True, "debt": _serialize_debt(debt)}
