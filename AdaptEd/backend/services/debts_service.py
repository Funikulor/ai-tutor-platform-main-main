from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.debts import RemedialAssignment, StudentDebt


class DebtsService:
    def list_debts(self, db: Session, user_id: str, include_resolved: bool = True) -> List[StudentDebt]:
        query = db.query(StudentDebt).filter(StudentDebt.user_id == user_id)
        if not include_resolved:
            query = query.filter(StudentDebt.status != "resolved")
        return query.order_by(StudentDebt.priority.asc(), StudentDebt.created_at.desc()).all()

    def upsert_topic_debt(
        self,
        db: Session,
        user_id: str,
        topic: str,
        source_type: str = "topic_gap",
        source_id: Optional[str] = None,
        created_by: Optional[str] = "system",
        priority: int = 2,
        notes: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> StudentDebt:
        normalized_topic = (topic or "Неуточненная тема").strip()[:255]
        existing = (
            db.query(StudentDebt)
            .filter(
                StudentDebt.user_id == user_id,
                StudentDebt.topic == normalized_topic,
                StudentDebt.status.in_(["open", "in_progress"]),
            )
            .order_by(StudentDebt.updated_at.desc())
            .first()
        )
        if existing:
            existing.priority = min(existing.priority, priority)
            existing.source_type = source_type or existing.source_type
            if source_id:
                existing.source_id = source_id
            if notes:
                existing.notes = notes
            if due_date:
                existing.due_date = due_date
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            return existing

        debt = StudentDebt(
            user_id=user_id,
            topic=normalized_topic,
            source_type=source_type,
            source_id=source_id,
            status="open",
            priority=priority,
            progress=0.0,
            created_by=created_by,
            notes=notes,
            due_date=due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(debt)
        db.flush()
        return debt

    def resolve_or_progress_topic_debts(self, db: Session, user_id: str, topic: str, delta: float) -> None:
        normalized_topic = (topic or "").strip()
        if not normalized_topic:
            return
        rows = (
            db.query(StudentDebt)
            .filter(
                StudentDebt.user_id == user_id,
                StudentDebt.topic == normalized_topic,
                StudentDebt.status.in_(["open", "in_progress"]),
            )
            .all()
        )
        for debt in rows:
            debt.progress = max(0.0, min(100.0, float(debt.progress or 0.0) + delta))
            debt.status = "resolved" if debt.progress >= 100.0 else "in_progress"
            if debt.status == "resolved":
                debt.resolved_at = datetime.utcnow()
            debt.updated_at = datetime.utcnow()
            db.add(debt)

    def create_remedial_assignment(
        self,
        db: Session,
        debt_id: int,
        user_id: str,
        kind: str,
        payload: Dict[str, Any],
        created_by: Optional[str],
        attempts_required: int = 1,
        due_date: Optional[datetime] = None,
    ) -> RemedialAssignment:
        assignment = RemedialAssignment(
            debt_id=debt_id,
            user_id=user_id,
            kind=kind,
            payload=payload,
            attempts_required=max(1, attempts_required),
            attempts_done=0,
            progress=0.0,
            status="assigned",
            created_by=created_by,
            due_date=due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(assignment)
        db.flush()
        return assignment

    def mark_assignment_progress(
        self,
        db: Session,
        user_id: str,
        kind: str,
        ref_value: str,
        progress_delta: float = 34.0,
    ) -> List[int]:
        ref_value = (ref_value or "").strip()
        if not ref_value:
            return []
        open_assignments = (
            db.query(RemedialAssignment)
            .filter(
                RemedialAssignment.user_id == user_id,
                RemedialAssignment.kind == kind,
                RemedialAssignment.status.in_(["assigned", "in_progress"]),
            )
            .all()
        )
        touched_debts: List[int] = []
        for assignment in open_assignments:
            payload = assignment.payload or {}
            payload_ref = str(payload.get("material_id") or payload.get("course_id") or payload.get("topic") or "").strip()
            if payload_ref != ref_value:
                continue
            assignment.attempts_done = int(assignment.attempts_done or 0) + 1
            assignment.progress = max(0.0, min(100.0, float(assignment.progress or 0.0) + progress_delta))
            assignment.status = "completed" if assignment.progress >= 100.0 else "in_progress"
            if assignment.status == "completed":
                assignment.completed_at = datetime.utcnow()
            assignment.updated_at = datetime.utcnow()
            db.add(assignment)
            touched_debts.append(assignment.debt_id)
        return touched_debts

    def recalculate_debt_from_assignments(self, db: Session, debt_id: int) -> Optional[StudentDebt]:
        debt = db.get(StudentDebt, debt_id)
        if not debt:
            return None
        assignments = (
            db.query(RemedialAssignment)
            .filter(RemedialAssignment.debt_id == debt_id)
            .order_by(RemedialAssignment.created_at.asc())
            .all()
        )
        if not assignments:
            return debt
        avg_progress = sum(float(a.progress or 0.0) for a in assignments) / max(1, len(assignments))
        debt.progress = max(float(debt.progress or 0.0), avg_progress)
        if debt.progress >= 100.0:
            debt.status = "resolved"
            debt.resolved_at = debt.resolved_at or datetime.utcnow()
        else:
            debt.status = "in_progress" if debt.progress > 0 else "open"
        debt.updated_at = datetime.utcnow()
        db.add(debt)
        return debt


_debts_service: Optional[DebtsService] = None


def get_debts_service() -> DebtsService:
    global _debts_service
    if _debts_service is None:
        _debts_service = DebtsService()
    return _debts_service
