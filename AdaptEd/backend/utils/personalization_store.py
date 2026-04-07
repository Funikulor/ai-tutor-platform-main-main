from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from utils.db import get_db, has_db
def _require_db():
    if not has_db():
        raise RuntimeError("DATABASE_URL не настроен: доступна только онлайн БД.")
    sess = get_db()
    if sess is None:
        raise RuntimeError("Не удалось создать сессию БД.")
    return sess


def _normalize_payload(payload: Any) -> Dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def load_cognitive_profiles() -> Dict[str, Dict[str, Any]]:
    from models.personalization_db import CognitiveProfileRecord  # type: ignore

    sess = _require_db()
    try:
        rows = sess.query(CognitiveProfileRecord).all()
        return {r.user_id: _normalize_payload(r.payload) for r in rows}
    finally:
        sess.close()


def save_cognitive_profile(user_id: str, payload: Dict[str, Any]) -> None:
    from models.personalization_db import CognitiveProfileRecord  # type: ignore

    sess = _require_db()
    try:
        row = sess.query(CognitiveProfileRecord).filter_by(user_id=user_id).first()
        if row:
            row.payload = payload
            row.updated_at = datetime.utcnow()
        else:
            row = CognitiveProfileRecord(user_id=user_id, payload=payload, updated_at=datetime.utcnow())
            sess.add(row)
        sess.commit()
    finally:
        sess.close()


def load_student_analytics() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, bool]]:
    from models.personalization_db import StudentAnalyticsRecord  # type: ignore

    sess = _require_db()
    try:
        rows = sess.query(StudentAnalyticsRecord).all()
        analytics = {r.user_id: _normalize_payload(r.payload) for r in rows}
        ethics = {r.user_id: bool(r.ethics_message_shown) for r in rows}
        return analytics, ethics
    finally:
        sess.close()


def save_student_analytics(user_id: str, payload: Dict[str, Any], ethics_shown: Optional[bool] = None) -> None:
    from models.personalization_db import StudentAnalyticsRecord  # type: ignore

    sess = _require_db()
    try:
        row = sess.query(StudentAnalyticsRecord).filter_by(user_id=user_id).first()
        if row:
            row.payload = payload
            if ethics_shown is not None:
                row.ethics_message_shown = bool(ethics_shown)
            row.updated_at = datetime.utcnow()
        else:
            row = StudentAnalyticsRecord(
                user_id=user_id,
                payload=payload,
                ethics_message_shown=bool(ethics_shown),
                updated_at=datetime.utcnow(),
            )
            sess.add(row)
        sess.commit()
    finally:
        sess.close()


def load_personality_profiles() -> Dict[str, Dict[str, Any]]:
    from models.personalization_db import PersonalityProfileRecord  # type: ignore

    sess = _require_db()
    try:
        rows = sess.query(PersonalityProfileRecord).all()
        return {r.user_id: _normalize_payload(r.payload) for r in rows}
    finally:
        sess.close()


def save_personality_profile(user_id: str, payload: Dict[str, Any]) -> None:
    from models.personalization_db import PersonalityProfileRecord  # type: ignore

    sess = _require_db()
    try:
        row = sess.query(PersonalityProfileRecord).filter_by(user_id=user_id).first()
        if row:
            row.payload = payload
            row.updated_at = datetime.utcnow()
        else:
            row = PersonalityProfileRecord(user_id=user_id, payload=payload, updated_at=datetime.utcnow())
            sess.add(row)
        sess.commit()
    finally:
        sess.close()
