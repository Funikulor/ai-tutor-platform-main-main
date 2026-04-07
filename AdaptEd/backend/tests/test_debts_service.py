from datetime import datetime, timedelta
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from models.debts import StudentDebt
from services.debts_service import DebtsService
from utils.db import Base


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    local_session = sessionmaker(bind=engine)
    return local_session()


def test_debt_lifecycle_with_remedial_progress():
    db = _make_session()
    service = DebtsService()

    debt = service.upsert_topic_debt(
        db=db,
        user_id="student-1",
        topic="Дроби",
        source_type="test",
        source_id="10",
        created_by="teacher-1",
        due_date=datetime.utcnow() + timedelta(days=3),
    )
    assignment = service.create_remedial_assignment(
        db=db,
        debt_id=debt.id,
        user_id="student-1",
        kind="adaptive_task",
        payload={"topic": "Дроби"},
        created_by="teacher-1",
        attempts_required=2,
    )
    db.commit()

    touched = service.mark_assignment_progress(
        db=db,
        user_id="student-1",
        kind="adaptive_task",
        ref_value="Дроби",
        progress_delta=60.0,
    )
    assert assignment.debt_id in touched
    service.recalculate_debt_from_assignments(db, debt.id)
    db.commit()

    reloaded = db.get(StudentDebt, debt.id)
    assert reloaded is not None
    assert float(reloaded.progress) >= 60.0
    assert reloaded.status in ("open", "in_progress", "resolved")


def test_resolve_topic_debt_by_success():
    db = _make_session()
    service = DebtsService()
    debt = service.upsert_topic_debt(db=db, user_id="student-2", topic="Алгебра")
    db.commit()

    service.resolve_or_progress_topic_debts(db=db, user_id="student-2", topic="Алгебра", delta=120.0)
    db.commit()

    reloaded = db.get(StudentDebt, debt.id)
    assert reloaded is not None
    assert reloaded.status == "resolved"
    assert float(reloaded.progress) == 100.0
