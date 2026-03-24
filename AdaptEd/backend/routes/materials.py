"""
API маршруты библиотеки материалов и мини-курсов
"""
from pathlib import Path
import hashlib
import json
import secrets
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from routes.auth import assert_can_view_user_data, get_current_user, require_roles
from utils.answer_parse import numeric_answers_equal
from utils.db import get_db, has_db
from utils.orchestrator_singleton import get_orchestrator
from utils.persistent_storage import persistent_storage

router = APIRouter()


def _default_materials_path() -> Path:
    backend_dir = Path(__file__).resolve().parent.parent
    return backend_dir / "data" / "library_materials.json"


def _load_default_materials() -> List[Dict[str, Any]]:
    file_path = _default_materials_path()
    if not file_path.exists():
        return []
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _ensure_materials() -> List[Dict[str, Any]]:
    materials = persistent_storage.get("library_materials", [])
    if isinstance(materials, list) and materials:
        return materials

    defaults = _load_default_materials()
    persistent_storage.set("library_materials", defaults)
    return defaults


def _material_matches(
    m: Dict[str, Any],
    subject: Optional[str],
    material_type: Optional[str],
    query_lc: Optional[str],
) -> bool:
    if subject and subject != "all" and m.get("subject") != subject:
        return False
    if material_type and material_type != "all" and m.get("type") != material_type:
        return False
    if query_lc:
        if query_lc in str(m.get("title", "")).lower():
            return True
        if query_lc in str(m.get("description", "")).lower():
            return True
        if query_lc in str(m.get("topic", "")).lower():
            return True
        return False
    return True


@router.get("/materials", response_model=List[Dict[str, Any]])
async def list_materials(
    subject: Optional[str] = None,
    material_type: Optional[str] = None,
    q: Optional[str] = None,
):
    try:
        materials = _ensure_materials()
        query_lc = q.lower().strip() if q else None
        return [m for m in materials if _material_matches(m, subject, material_type, query_lc)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Мини-курсы (полные данные с ответами только на сервере) ---

def _courses_path() -> Path:
    backend_dir = Path(__file__).resolve().parent.parent
    return backend_dir / "data" / "library_courses.json"


def _course_parts_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "course_parts"


def _hydrate_lesson(les: Dict[str, Any]) -> Dict[str, Any]:
    """Подставляет текст урока из .md, если задано поле content_file."""
    out = dict(les)
    ref = out.get("content_file")
    if ref:
        path = _course_parts_dir() / f"{ref}.md"
        if path.is_file():
            out["content"] = path.read_text(encoding="utf-8")
        else:
            out.setdefault("content", "")
    return out


def _hydrate_course(course: Dict[str, Any]) -> Dict[str, Any]:
    c = dict(course)
    c["lessons"] = [_hydrate_lesson(l) for l in (course.get("lessons") or [])]
    return c


def _load_courses_raw() -> List[Dict[str, Any]]:
    """Курсы из JSON-файла + курсы, созданные в админке (admin_library_courses в data.json)."""
    p = _courses_path()
    data: List[Dict[str, Any]] = []
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                data = raw
        except Exception:
            pass
    by_id: Dict[str, Dict[str, Any]] = {}
    for c in data:
        cid = c.get("id")
        if cid:
            by_id[str(cid)] = _hydrate_course(c)
    extra = persistent_storage.get("admin_library_courses", [])
    if isinstance(extra, list):
        for c in extra:
            cid = c.get("id")
            if cid:
                by_id[str(cid)] = _hydrate_course(c)
    return list(by_id.values())


def _material_card(m: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": m.get("id"),
        "title": m.get("title", ""),
        "description": m.get("description", ""),
        "subject": m.get("subject", ""),
        "topic": m.get("topic", ""),
        "type": m.get("type", "article"),
        "difficulty": m.get("difficulty", "beginner"),
        "duration": m.get("duration"),
        "rating": m.get("rating", 4.5),
    }


def _checkpoint_task_id(course_id: str, lesson_id: str) -> int:
    h = hashlib.md5(f"{course_id}:{lesson_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 999_999_999 + 1


def _public_checkpoint(ch: Dict[str, Any]) -> Dict[str, Any]:
    """Без правильных ответов — только то, что нужно для отображения."""
    if not ch:
        return {}
    t = ch.get("type", "single_choice")
    out: Dict[str, Any] = {"question": ch.get("question", ""), "type": t}
    if t == "single_choice":
        out["options"] = list(ch.get("options") or [])
    return out


def _course_to_public(course: Dict[str, Any]) -> Dict[str, Any]:
    lessons_out = []
    for les in course.get("lessons") or []:
        lessons_out.append(
            {
                "id": les.get("id"),
                "title": les.get("title", ""),
                "content": les.get("content", ""),
                "checkpoint": _public_checkpoint(les.get("checkpoint") or {}),
            }
        )
    return {
        "id": course.get("id"),
        "title": course.get("title", ""),
        "description": course.get("description", ""),
        "subject": course.get("subject", ""),
        "topic": course.get("topic", ""),
        "difficulty": course.get("difficulty", "beginner"),
        "estimated_minutes": course.get("estimated_minutes"),
        "lessons": lessons_out,
    }


def _find_lesson(
    courses: List[Dict[str, Any]], course_id: str, lesson_id: str
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    for c in courses:
        if c.get("id") != course_id:
            continue
        for les in c.get("lessons") or []:
            if les.get("id") == lesson_id:
                return c, les
    return None, None


def _validate_checkpoint_answer(lesson: Dict[str, Any], answer: str) -> bool:
    ch = lesson.get("checkpoint") or {}
    t = ch.get("type", "single_choice")
    raw = (answer or "").strip()

    if t == "single_choice":
        try:
            idx = int(raw)
        except ValueError:
            return False
        return idx == int(ch.get("correct_index", -999))

    if t == "numeric":
        ca = str(ch.get("correct_answer", "")).strip()
        if numeric_answers_equal(raw, ca):
            return True
        return raw.replace(" ", "").lower() == ca.replace(" ", "").lower()

    if t == "short_text":
        a = raw.lower()
        for opt in ch.get("acceptable_answers") or []:
            if a == str(opt).strip().lower():
                return True
        return False

    return False


@router.get("/library/courses", response_model=List[Dict[str, Any]])
async def list_library_courses():
    """Список мини-курсов для библиотеки (без секретных полей проверки)."""
    try:
        return [_course_to_public(c) for c in _load_courses_raw()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/courses/{course_id}", response_model=Dict[str, Any])
async def get_library_course(course_id: str):
    """Один курс целиком (публичные поля уроков и вопросов)."""
    for c in _load_courses_raw():
        if c.get("id") == course_id:
            return _course_to_public(c)
    raise HTTPException(status_code=404, detail="Курс не найден")


class LibraryCheckpointSubmit(BaseModel):
    course_id: str = Field(..., min_length=1)
    lesson_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    answer: str = Field(..., description="Индекс варианта для single_choice, число или дробь для numeric, текст для short_text")


@router.post("/library/checkpoint")
async def submit_library_checkpoint(
    body: LibraryCheckpointSubmit,
    current_user: dict = Depends(get_current_user),
):
    """
    Проверка контрольного вопроса после шага курса.
    Учитывает ответ в когнитивном профиле (как решение задания) для графа знаний и статистики.
    """
    assert_can_view_user_data(current_user, body.user_id)

    courses = _load_courses_raw()
    course, lesson = _find_lesson(courses, body.course_id, body.lesson_id)
    if not course or not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    ch = lesson.get("checkpoint") or {}
    if not ch.get("question"):
        raise HTTPException(status_code=400, detail="У этого урока нет контрольного вопроса")

    ok = _validate_checkpoint_answer(lesson, body.answer)
    topic = (course.get("topic") or course.get("title") or "Библиотека")[:200]
    qtext = str(ch.get("question", ""))[:500]

    ua = body.answer.strip()
    # orchestrator вычисляет is_correct по совпадению с correct_answer
    ca = ua if ok else ("\u200b" + ua if ua else "\u200bwrong")

    orch = get_orchestrator()
    orch.process_task_submission(
        user_id=body.user_id,
        task_id=_checkpoint_task_id(body.course_id, body.lesson_id),
        question=f"[Курс: {course.get('title', '')}] {qtext}",
        user_answer=ua,
        correct_answer=ca,
        topic=topic,
        time_spent_seconds=None,
    )

    feedback = (
        "Верно! Можно переходить к следующему шагу."
        if ok
        else "Пока неверно. Перечитайте шаг и попробуйте снова — в обучении нормально ошибаться."
    )

    return {
        "is_correct": ok,
        "feedback": feedback,
        "topic": topic,
    }


# --- Программа: каталог тем → материалы и курсы в библиотеке ---


@router.get("/library/curriculum-overview", response_model=Dict[str, Any])
async def library_curriculum_overview(db: Session = Depends(get_db)):
    """
    Дерево программы для ученика: предмет → раздел → тема → привязанные материалы и мини-курсы.
    """
    try:
        if not has_db() or db is None:
            return {"subjects": []}

        from models.curriculum import CurriculumSection, CurriculumSubject
        from services.curriculum_catalog import ensure_catalog_ready

        ensure_catalog_ready(db, persistent_storage)
        materials = _ensure_materials()
        mat_by_id = {str(m["id"]): m for m in materials if m.get("id")}
        courses_by_id = {str(c["id"]): c for c in _load_courses_raw() if c.get("id")}

        subjects_out: List[Dict[str, Any]] = []
        q = (
            db.query(CurriculumSubject)
            .options(
                joinedload(CurriculumSubject.sections).joinedload(CurriculumSection.topics)
            )
            .order_by(CurriculumSubject.sort_order, CurriculumSubject.id)
        )

        for subj in q:
            sec_list: List[Dict[str, Any]] = []
            for sec in subj.sections:
                topics_out: List[Dict[str, Any]] = []
                for top in sec.topics:
                    mids = list(top.library_material_ids or [])
                    cids = list(top.library_course_ids or [])
                    mats = [
                        _material_card(mat_by_id[sk])
                        for mid in mids
                        if (sk := str(mid)) in mat_by_id
                    ]
                    crs = [
                        _course_to_public(courses_by_id[sk])
                        for cid in cids
                        if (sk := str(cid)) in courses_by_id
                    ]
                    if not mats and not crs:
                        continue
                    topics_out.append(
                        {
                            "id": top.id,
                            "name": top.name,
                            "description": (top.description or "")[:2000],
                            "grade_hint": top.grade_hint or "",
                            "materials": mats,
                            "courses": crs,
                        }
                    )
                if topics_out:
                    sec_list.append({"id": sec.id, "name": sec.name, "topics": topics_out})
            if sec_list:
                subjects_out.append({"id": subj.id, "subject": subj.title, "sections": sec_list})

        return {"subjects": subjects_out}
    except Exception as e:
        print(f"Error in library_curriculum_overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/library/picker", response_model=Dict[str, Any])
async def admin_library_picker(_admin: dict = Depends(require_roles("admin"))):
    """Справочник id для привязки к теме каталога."""
    mats = _ensure_materials()
    courses = _load_courses_raw()
    return {
        "materials": [
            {
                "id": m["id"],
                "title": m.get("title", ""),
                "topic": m.get("topic", ""),
                "subject": m.get("subject", ""),
                "type": m.get("type", "article"),
            }
            for m in mats
            if m.get("id")
        ],
        "courses": [
            {
                "id": c["id"],
                "title": c.get("title", ""),
                "topic": c.get("topic", ""),
                "subject": c.get("subject", ""),
            }
            for c in courses
            if c.get("id")
        ],
    }


class AdminLibraryMaterialCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    content: str = ""
    subject: str = "Математика"
    topic: str = ""
    type: str = "article"
    difficulty: str = "beginner"
    duration: str = "15 мин"


@router.post("/admin/library/materials", response_model=Dict[str, Any])
async def admin_create_library_material(
    body: AdminLibraryMaterialCreate,
    _admin: dict = Depends(require_roles("admin")),
):
    """Добавить статью/карточку в библиотеку (в data.json)."""
    try:
        materials = list(_ensure_materials())
        new_id = f"mat-{secrets.token_hex(5)}"
        row = {
            "id": new_id,
            "type": body.type if body.type in ("article", "video", "pdf") else "article",
            "title": body.title.strip(),
            "description": (body.description or "").strip(),
            "subject": (body.subject or "Математика").strip(),
            "topic": (body.topic or body.title[:80]).strip(),
            "difficulty": body.difficulty
            if body.difficulty in ("beginner", "intermediate", "advanced")
            else "beginner",
            "duration": (body.duration or "").strip() or "15 мин",
            "rating": 5.0,
            "content": body.content or "",
        }
        materials.append(row)
        persistent_storage.set("library_materials", materials)
        return {"id": new_id, "material": row}
    except Exception as e:
        print(f"Error in admin_create_library_material: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/library/courses", response_model=Dict[str, Any])
async def admin_upsert_library_course(
    course: Dict[str, Any],
    _admin: dict = Depends(require_roles("admin")),
):
    """
    Создать или обновить мини-курс (полная структура как в library_courses.json).
    Хранится в admin_library_courses; id должен быть уникальным.
    """
    cid = (course.get("id") or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="Поле id обязательно")
    if not course.get("title"):
        raise HTTPException(status_code=400, detail="Укажите title")
    lessons = course.get("lessons")
    if not isinstance(lessons, list) or len(lessons) < 1:
        raise HTTPException(status_code=400, detail="Добавьте хотя бы один урок")

    stored = list(persistent_storage.get("admin_library_courses", []) or [])
    stored = [c for c in stored if str(c.get("id")) != cid]
    stored.append(course)
    persistent_storage.set("admin_library_courses", stored)
    return {"message": "Курс сохранён", "id": cid}


@router.delete("/admin/library/courses/{course_id}", response_model=Dict[str, Any])
async def admin_delete_library_course(
    course_id: str,
    _admin: dict = Depends(require_roles("admin")),
):
    """Удалить только курс из admin_library_courses (штатные JSON-файлы не трогаем)."""
    stored = list(persistent_storage.get("admin_library_courses", []) or [])
    new_list = [c for c in stored if str(c.get("id")) != course_id]
    if len(new_list) == len(stored):
        raise HTTPException(status_code=404, detail="Курс не найден среди созданных в админке")
    persistent_storage.set("admin_library_courses", new_list)
    return {"message": "Курс удалён", "id": course_id}

