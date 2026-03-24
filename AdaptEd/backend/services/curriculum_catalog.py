"""
Каталог учебных тем для админки: чтение/запись в БД, миграция из data.json, сид по умолчанию.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.curriculum import (
    CurriculumSection,
    CurriculumSubject,
    CurriculumTopic,
    CurriculumTopicTask,
)

CURRICULUM_DEFAULT_SEED: List[Dict[str, Any]] = [
    {
        "subject": "Математика",
        "sections": [
            {
                "name": "Алгебра",
                "topics": [
                    {"name": "Уравнения", "elements": 12, "tasks": 0},
                    {"name": "Функции", "elements": 8, "tasks": 0},
                    {"name": "Неравенства", "elements": 6, "tasks": 0},
                ],
            },
            {
                "name": "Геометрия",
                "topics": [
                    {"name": "Треугольники", "elements": 10, "tasks": 0},
                    {"name": "Окружности", "elements": 7, "tasks": 0},
                ],
            },
        ],
    },
]


def _topic_to_dict(t: CurriculumTopic) -> Dict[str, Any]:
    return {
        "id": t.id,
        "name": t.name,
        "elements": t.elements_count,
        "tasks": t.tasks_count,
        "description": t.description or "",
        "teacher_notes": t.teacher_notes or "",
        "grade_hint": t.grade_hint or "",
        "library_material_ids": list(t.library_material_ids or []),
        "library_course_ids": list(t.library_course_ids or []),
    }


def subject_to_dict(db: Session, subject_id: int) -> Dict[str, Any]:
    row = find_subject(db, subject_id)
    if not row:
        return {}
    secs = []
    for sec in row.sections:
        secs.append(
            {
                "id": sec.id,
                "name": sec.name,
                "topics": [_topic_to_dict(t) for t in sec.topics],
            }
        )
    return {"id": row.id, "subject": row.title, "sections": secs}


def section_to_dict(sec: CurriculumSection) -> Dict[str, Any]:
    return {
        "id": sec.id,
        "name": sec.name,
        "topics": [_topic_to_dict(t) for t in sec.topics],
    }


def structure_to_nested_list(db: Session) -> List[Dict[str, Any]]:
    subjects = (
        db.query(CurriculumSubject).order_by(CurriculumSubject.sort_order, CurriculumSubject.id).all()
    )
    return [subject_to_dict(db, s.id) for s in subjects]


def migrate_from_persistent_storage(db: Session, persistent_storage) -> None:
    if db.query(CurriculumSubject).first() is not None:
        return
    raw = persistent_storage.get("admin_content_structure")
    if not raw:
        return
    for s_idx, subj in enumerate(raw):
        title = (subj.get("subject") or "Без названия").strip() or "Без названия"
        cs = CurriculumSubject(title=title, sort_order=s_idx)
        db.add(cs)
        db.flush()
        for sec_idx, sec in enumerate(subj.get("sections") or []):
            sec_name = (sec.get("name") or "Раздел").strip() or "Раздел"
            cs_sec = CurriculumSection(subject_id=cs.id, name=sec_name, sort_order=sec_idx)
            db.add(cs_sec)
            db.flush()
            for t_idx, top in enumerate(sec.get("topics") or []):
                lm = top.get("library_material_ids")
                lc = top.get("library_course_ids")
                db.add(
                    CurriculumTopic(
                        section_id=cs_sec.id,
                        name=(top.get("name") or "Тема").strip() or "Тема",
                        description=str(top.get("description") or "")[:20000],
                        teacher_notes=str(top.get("teacher_notes") or "")[:20000],
                        grade_hint=str(top.get("grade_hint") or "")[:128],
                        elements_count=max(0, int(top.get("elements") or 0)),
                        tasks_count=max(0, int(top.get("tasks") or 0)),
                        sort_order=t_idx,
                        library_material_ids=list(lm) if isinstance(lm, list) else None,
                        library_course_ids=list(lc) if isinstance(lc, list) else None,
                    )
                )
    db.commit()


def seed_default_if_empty(db: Session) -> None:
    if db.query(CurriculumSubject).first() is not None:
        return
    for s_idx, subj in enumerate(CURRICULUM_DEFAULT_SEED):
        cs = CurriculumSubject(title=subj["subject"], sort_order=s_idx)
        db.add(cs)
        db.flush()
        for sec_idx, sec in enumerate(subj["sections"]):
            cs_sec = CurriculumSection(subject_id=cs.id, name=sec["name"], sort_order=sec_idx)
            db.add(cs_sec)
            db.flush()
            for t_idx, top in enumerate(sec["topics"]):
                db.add(
                    CurriculumTopic(
                        section_id=cs_sec.id,
                        name=top["name"],
                        description="",
                        teacher_notes="",
                        grade_hint="",
                        elements_count=max(0, int(top.get("elements", 0))),
                        tasks_count=max(0, int(top.get("tasks", 0))),
                        sort_order=t_idx,
                    )
                )
    db.commit()


def ensure_catalog_ready(db: Session, persistent_storage) -> None:
    migrate_from_persistent_storage(db, persistent_storage)
    seed_default_if_empty(db)


def get_topic_by_id(db: Session, topic_id: int) -> Optional[CurriculumTopic]:
    return db.get(CurriculumTopic, topic_id)


def find_section(db: Session, section_id: int) -> Optional[CurriculumSection]:
    return db.get(CurriculumSection, section_id)


def find_subject(db: Session, subject_id: int) -> Optional[CurriculumSubject]:
    return db.get(CurriculumSubject, subject_id)


def create_subject_db(db: Session, title: str) -> Dict[str, Any]:
    n = db.query(func.max(CurriculumSubject.sort_order)).scalar()
    sort_order = (n if n is not None else -1) + 1
    row = CurriculumSubject(title=title.strip(), sort_order=sort_order)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "subject": row.title, "sections": []}


def update_subject_db(db: Session, subject_id: int, title: str) -> Optional[Dict[str, Any]]:
    row = find_subject(db, subject_id)
    if not row:
        return None
    row.title = title.strip()
    db.commit()
    db.refresh(row)
    return subject_to_dict(db, subject_id)


def delete_subject_db(db: Session, subject_id: int) -> bool:
    row = find_subject(db, subject_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def create_section_db(db: Session, subject_id: int, name: str) -> Optional[Dict[str, Any]]:
    sub = find_subject(db, subject_id)
    if not sub:
        return None
    n = (
        db.query(func.max(CurriculumSection.sort_order))
        .filter(CurriculumSection.subject_id == subject_id)
        .scalar()
    )
    sort_order = (n if n is not None else -1) + 1
    sec = CurriculumSection(subject_id=subject_id, name=name.strip(), sort_order=sort_order)
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return {"id": sec.id, "name": sec.name, "topics": []}


def update_section_db(db: Session, section_id: int, name: str) -> Optional[Dict[str, Any]]:
    sec = find_section(db, section_id)
    if not sec:
        return None
    sec.name = name.strip()
    db.commit()
    db.refresh(sec)
    return section_to_dict(sec)


def delete_section_db(db: Session, section_id: int) -> bool:
    sec = find_section(db, section_id)
    if not sec:
        return False
    db.delete(sec)
    db.commit()
    return True


def create_topic_db(
    db: Session,
    section_id: int,
    name: str,
    description: str = "",
    teacher_notes: str = "",
    grade_hint: str = "",
    elements: int = 0,
) -> Optional[Dict[str, Any]]:
    sec = find_section(db, section_id)
    if not sec:
        return None
    n = (
        db.query(func.max(CurriculumTopic.sort_order))
        .filter(CurriculumTopic.section_id == section_id)
        .scalar()
    )
    sort_order = (n if n is not None else -1) + 1
    t = CurriculumTopic(
        section_id=section_id,
        name=name.strip(),
        description=description.strip()[:20000],
        teacher_notes=teacher_notes.strip()[:20000],
        grade_hint=grade_hint.strip()[:128],
        elements_count=max(0, int(elements)),
        tasks_count=0,
        sort_order=sort_order,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _topic_to_dict(t)


def update_topic_db(db: Session, topic_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    t = get_topic_by_id(db, topic_id)
    if not t:
        return None
    if data.get("name") is not None:
        t.name = str(data["name"]).strip()
    if data.get("elements") is not None:
        t.elements_count = max(0, int(data["elements"]))
    if data.get("tasks") is not None:
        t.tasks_count = max(0, int(data["tasks"]))
    if data.get("description") is not None:
        t.description = str(data["description"]).strip()[:20000]
    if data.get("teacher_notes") is not None:
        t.teacher_notes = str(data["teacher_notes"]).strip()[:20000]
    if data.get("grade_hint") is not None:
        t.grade_hint = str(data["grade_hint"]).strip()[:128]
    if data.get("library_material_ids") is not None:
        t.library_material_ids = list(data["library_material_ids"])
    if data.get("library_course_ids") is not None:
        t.library_course_ids = list(data["library_course_ids"])
    db.commit()
    db.refresh(t)
    return _topic_to_dict(t)


def set_topic_library_links(
    db: Session,
    topic_id: int,
    material_ids: Optional[List[str]] = None,
    course_ids: Optional[List[str]] = None,
) -> bool:
    t = get_topic_by_id(db, topic_id)
    if not t:
        return False
    if material_ids is not None:
        t.library_material_ids = [str(x).strip() for x in material_ids if str(x).strip()]
    if course_ids is not None:
        t.library_course_ids = [str(x).strip() for x in course_ids if str(x).strip()]
    db.commit()
    db.refresh(t)
    return True


def delete_topic_db(db: Session, topic_id: int) -> bool:
    t = get_topic_by_id(db, topic_id)
    if not t:
        return False
    db.delete(t)
    db.commit()
    return True


def list_topic_tasks_db(db: Session, topic_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.query(CurriculumTopicTask)
        .filter(CurriculumTopicTask.topic_id == topic_id)
        .order_by(CurriculumTopicTask.id)
        .all()
    )
    return [{"id": r.id, "title": r.title, "description": r.description or ""} for r in rows]


def add_topic_task_db(db: Session, topic_id: int, title: str, description: str = "") -> Optional[Tuple[int, int]]:
    t = get_topic_by_id(db, topic_id)
    if not t:
        return None
    task = CurriculumTopicTask(
        topic_id=topic_id,
        title=title.strip()[:512],
        description=(description or "").strip()[:20000],
    )
    db.add(task)
    t.tasks_count = max(0, t.tasks_count) + 1
    db.commit()
    db.refresh(task)
    return task.id, t.tasks_count


def delete_topic_task_db(db: Session, topic_id: int, task_id: int) -> bool:
    task = db.get(CurriculumTopicTask, task_id)
    if not task or task.topic_id != topic_id:
        return False
    t = get_topic_by_id(db, topic_id)
    db.delete(task)
    if t:
        t.tasks_count = max(0, t.tasks_count - 1)
    db.commit()
    return True
