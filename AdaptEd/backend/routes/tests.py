from datetime import datetime
import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from utils.orchestrator_singleton import get_orchestrator
from models.homework import Homework, HomeworkSubmission
from models.test import Test, TestQuestion, TestSubmission
from services.assistant import get_assistant_service
from services.student_analytics import get_analytics_service
from utils.answer_parse import numeric_answers_equal
from utils.db import get_db, has_db
from routes.auth import get_current_user, require_roles, assert_can_view_user_data
from utils.auth_service import role_to_str

router = APIRouter()


class ManualQuestion(BaseModel):
	question: str
	options: List[str]
	correct_index: int = 0
	question_type: Optional[str] = "single"
	correct_answer: Optional[Any] = None
	explanation: Optional[str] = None


class ManualTestCreate(BaseModel):
	title: str
	topic: Optional[str] = None
	difficulty: Optional[str] = None
	creator_id: Optional[str] = None
	questions: List[ManualQuestion]


class ManualTestUpdate(BaseModel):
	title: Optional[str] = None
	topic: Optional[str] = None
	difficulty: Optional[str] = None
	questions: Optional[List[ManualQuestion]] = None


class GeneratedTestRequest(BaseModel):
	topic: Optional[str] = None
	difficulty: Optional[str] = "medium"
	question_count: Optional[int] = 5
	creator_id: Optional[str] = None
	user_id: Optional[str] = None
	subject: Optional[str] = None
	grade: Optional[str] = None
	include_explanations: Optional[bool] = True


class SubmittedAnswer(BaseModel):
	question_id: Optional[int] = None
	selected_option_indexes: Optional[List[int]] = None
	answer_text: Optional[str] = None
	answer_number: Optional[float] = None
	student_explanation: Optional[str] = None


class TestSubmitRequest(BaseModel):
	user_id: str
	answers: List[SubmittedAnswer]
	homework_id: Optional[int] = None
	time_spent_seconds: Optional[float] = None


class TestAssignRequest(BaseModel):
	test_id: int
	student_ids: List[str]
	assignment_type: Optional[str] = "homework"  # homework | control | quiz
	due_date: Optional[datetime] = None
	created_by: Optional[str] = None


def _assistant():
	return get_assistant_service()


def _normalize_question_type(question_type: Optional[str]) -> str:
	if question_type in {"single", "multiple", "text", "numeric"}:
		return question_type
	return "single"


def _derive_correct_answer(question: ManualQuestion) -> Any:
	qtype = _normalize_question_type(question.question_type)
	if question.correct_answer is not None:
		return question.correct_answer
	if qtype in {"single", "multiple"}:
		return [question.correct_index]
	if qtype == "numeric":
		if question.options:
			try:
				return float(question.options[0])
			except Exception:
				return question.options[0]
		return None
	if question.options:
		return question.options[0]
	return None


def _question_correct_value(question: TestQuestion) -> Any:
	if question.correct_answer is not None:
		return question.correct_answer
	qtype = _normalize_question_type(question.question_type)
	if qtype in {"single", "multiple"}:
		return [question.correct_index]
	if qtype == "numeric":
		if question.options:
			try:
				return float(question.options[0])
			except Exception:
				return question.options[0]
		return None
	if question.options:
		return question.options[0]
	return None


def _question_correct_display(question: TestQuestion) -> str:
	qtype = _normalize_question_type(question.question_type)
	correct_value = _question_correct_value(question)
	if qtype in {"single", "multiple"}:
		indexes = correct_value if isinstance(correct_value, list) else [question.correct_index]
		options = question.options or []
		values = [options[idx] for idx in indexes if isinstance(idx, int) and 0 <= idx < len(options)]
		return ", ".join(values) if values else ""
	return str(correct_value or "")


def _serialize_test(test: Test, include_questions: bool = False) -> Dict[str, Any]:
	data = {
		"id": test.id,
		"title": test.title,
		"topic": test.topic,
		"difficulty": test.difficulty,
		"source": test.source,
		"creator_id": test.creator_id,
		"created_at": test.created_at.isoformat() if test.created_at else None,
	}
	if include_questions:
		questions = sorted(test.questions, key=lambda q: q.id or 0)
		data["questions"] = [
			{
				"id": q.id,
				"question": q.question,
				"options": q.options or [],
				"correct_index": q.correct_index,
				"question_type": _normalize_question_type(q.question_type),
				"correct_answer": _question_correct_value(q),
				"explanation": q.explanation,
			}
			for q in questions
		]
	return data


def _serialize_submission(submission: TestSubmission, test: Optional[Test] = None) -> Dict[str, Any]:
	data = {
		"id": submission.id,
		"test_id": submission.test_id,
		"homework_id": submission.homework_id,
		"user_id": submission.user_id,
		"answers": submission.answers or [],
		"question_results": submission.question_results or [],
		"correct_count": submission.correct_count,
		"total_questions": submission.total_questions,
		"summary": submission.summary,
		"score": submission.score,
		"feedback": submission.feedback,
		"created_at": submission.created_at.isoformat() if submission.created_at else None,
	}
	if test is not None:
		data["test"] = _serialize_test(test, include_questions=True)
	return data


def _evaluate_question(question: TestQuestion, submitted: SubmittedAnswer) -> Dict[str, Any]:
	qtype = _normalize_question_type(question.question_type)
	options = question.options or []
	selected_indexes = [idx for idx in (submitted.selected_option_indexes or []) if isinstance(idx, int)]
	selected_texts = [options[idx] for idx in selected_indexes if 0 <= idx < len(options)]
	student_text = (submitted.answer_text or "").strip()
	student_number = submitted.answer_number
	student_explanation = (submitted.student_explanation or "").strip()
	correct_value = _question_correct_value(question)
	is_correct = False

	if qtype == "single":
		correct_indexes = correct_value if isinstance(correct_value, list) else [question.correct_index]
		is_correct = len(selected_indexes) == 1 and len(correct_indexes) == 1 and selected_indexes[0] == correct_indexes[0]
	elif qtype == "multiple":
		correct_indexes = correct_value if isinstance(correct_value, list) else [question.correct_index]
		is_correct = set(selected_indexes) == set(idx for idx in correct_indexes if isinstance(idx, int))
	elif qtype == "numeric":
		correct_text = str(correct_value if correct_value is not None else "")
		user_numeric_text = str(student_number) if student_number is not None else student_text
		is_correct = numeric_answers_equal(user_numeric_text, correct_text)
	elif qtype == "text":
		expected = str(correct_value or "").strip().lower()
		is_correct = bool(student_text) and student_text.strip().lower() == expected

	student_answer_value: Any
	if qtype in {"single", "multiple"}:
		student_answer_value = selected_indexes
	elif qtype == "numeric":
		student_answer_value = student_number if student_number is not None else student_text
	else:
		student_answer_value = student_text

	return {
		"question_id": question.id,
		"question": question.question,
		"question_type": qtype,
		"selected_option_indexes": selected_indexes,
		"selected_option_texts": selected_texts,
		"student_answer": student_answer_value,
		"student_explanation": student_explanation,
		"is_correct": is_correct,
		"correct_answer": correct_value,
		"correct_answer_text": _question_correct_display(question),
		"question_explanation": question.explanation,
	}


def _build_generation_prompt(payload: GeneratedTestRequest) -> str:
	weak_topics_text = ""
	if payload.user_id:
		try:
			profile = get_orchestrator().profiler.get_profile(payload.user_id)
			if profile and profile.topic_mastery:
				weak_topics = [
					topic
					for topic, mastery in sorted(profile.topic_mastery.items(), key=lambda item: item[1])
					if mastery < 0.7
				][:5]
				if weak_topics:
					weak_topics_text = (
						"\nПерсонализация: смести акцент теста на слабые темы ученика: "
						+ ", ".join(weak_topics)
						+ "."
					)
		except Exception:
			pass

	include_explanations = "да" if payload.include_explanations else "нет"
	subject = payload.subject or "не указан"
	grade = payload.grade or "не указан"
	return f"""Создай тест для школьника.
Тема: {payload.topic}.
Предмет: {subject}.
Класс: {grade}.
Сложность: {payload.difficulty or 'medium'}.
Количество вопросов: {payload.question_count or 5}.
Нужно ли добавлять объяснения: {include_explanations}.{weak_topics_text}

Верни строго JSON без пояснений:
{{
  "title": "...",
  "topic": "...",
  "difficulty": "...",
  "questions": [
    {{
      "question": "...",
      "question_type": "single",
      "options": ["...", "...", "...", "..."],
      "correct_index": 0,
      "explanation": "краткое объяснение правильного ответа"
    }}
  ]
}}
Используй в основном формат single choice c 4 вариантами, чтобы тест можно было быстро назначать как домашнее задание.
"""


def _extract_generated_payload(raw: str) -> Dict[str, Any]:
	json_match = re.search(r"\{.*\}", raw, re.DOTALL)
	if not json_match:
		raise HTTPException(status_code=500, detail="Failed to parse generated test")
	try:
		return json.loads(json_match.group())
	except Exception:
		raise HTTPException(status_code=500, detail="Failed to parse generated test JSON")


def _create_question_record(db: Session, test_id: int, question: ManualQuestion):
	options = question.options or []
	if question.correct_index < 0 or (options and question.correct_index >= len(options)):
		raise HTTPException(status_code=400, detail="correct_index is out of range")
	db.add(
		TestQuestion(
			test_id=test_id,
			question=question.question,
			options=options,
			correct_index=question.correct_index,
			question_type=_normalize_question_type(question.question_type),
			correct_answer=_derive_correct_answer(question),
			explanation=question.explanation,
		)
	)


@router.post("/tests/manual", response_model=Dict[str, Any])
async def create_manual_test(
	payload: ManualTestCreate,
	db: Session = Depends(get_db),
	current_user: dict = Depends(require_roles("teacher", "admin")),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	if not payload.questions:
		raise HTTPException(status_code=400, detail="Questions are required")

	creator_id = payload.creator_id or str(current_user.get("user_id", ""))
	test = Test(
		title=payload.title,
		topic=payload.topic,
		difficulty=payload.difficulty,
		source="manual",
		creator_id=creator_id,
		created_at=datetime.utcnow(),
	)
	db.add(test)
	db.flush()

	for question in payload.questions:
		_create_question_record(db, test.id, question)

	db.commit()
	db.refresh(test)
	return {"test": _serialize_test(test, include_questions=True)}


@router.post("/tests/generate", response_model=Dict[str, Any])
async def generate_test(
	payload: GeneratedTestRequest,
	db: Session = Depends(get_db),
	current_user: dict = Depends(require_roles("teacher", "admin")),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	if not (payload.topic or "").strip():
		raise HTTPException(status_code=400, detail="Укажите тему для генерации теста (topic)")

	creator_id = payload.creator_id or str(current_user.get("user_id", ""))
	raw = _assistant()._generate(_build_generation_prompt(payload), max_new_tokens=1000)
	data = _extract_generated_payload(raw)
	questions = data.get("questions") or []
	if not questions:
		raise HTTPException(status_code=500, detail="No questions in generated test")

	test = Test(
		title=data.get("title") or f"Тест по теме {payload.topic}",
		topic=data.get("topic") or payload.topic,
		difficulty=data.get("difficulty") or payload.difficulty,
		source="ai",
		creator_id=creator_id,
		created_at=datetime.utcnow(),
	)
	db.add(test)
	db.flush()

	for generated_question in questions:
		options = generated_question.get("options") or []
		correct_index = generated_question.get("correct_index")
		if not isinstance(correct_index, int):
			correct_index = 0
		model = ManualQuestion(
			question=generated_question.get("question", ""),
			options=options,
			correct_index=correct_index,
			question_type=generated_question.get("question_type") or "single",
			correct_answer=generated_question.get("correct_answer"),
			explanation=generated_question.get("explanation"),
		)
		_create_question_record(db, test.id, model)

	db.commit()
	db.refresh(test)
	return {"test": _serialize_test(test, include_questions=True)}


@router.get("/tests", response_model=List[Dict[str, Any]])
async def list_tests(
	topic: Optional[str] = None,
	creator_id: Optional[str] = None,
	db: Session = Depends(get_db),
	_user: dict = Depends(get_current_user),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	stmt = select(Test).order_by(Test.created_at.desc())
	if topic:
		stmt = stmt.where(Test.topic == topic)
	if creator_id:
		stmt = stmt.where(Test.creator_id == creator_id)
	rows = db.execute(stmt).scalars().all()
	return [_serialize_test(test, include_questions=False) for test in rows]


@router.get("/tests/{test_id}", response_model=Dict[str, Any])
async def get_test(test_id: int, db: Session = Depends(get_db), _user: dict = Depends(get_current_user)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	return _serialize_test(test, include_questions=True)


@router.put("/tests/{test_id}", response_model=Dict[str, Any])
async def update_test(
	test_id: int,
	payload: ManualTestUpdate,
	db: Session = Depends(get_db),
	_staff: dict = Depends(require_roles("teacher", "admin")),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	if payload.title is not None:
		test.title = payload.title
	if payload.topic is not None:
		test.topic = payload.topic
	if payload.difficulty is not None:
		test.difficulty = payload.difficulty

	if payload.questions is not None:
		for question in list(test.questions):
			db.delete(question)
		db.flush()
		for question in payload.questions:
			_create_question_record(db, test.id, question)

	db.commit()
	db.refresh(test)
	return {"test": _serialize_test(test, include_questions=True)}


@router.delete("/tests/{test_id}", response_model=Dict[str, Any])
async def delete_test(test_id: int, db: Session = Depends(get_db), _staff: dict = Depends(require_roles("teacher", "admin"))):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	db.delete(test)
	db.commit()
	return {"ok": True}


@router.post("/tests/{test_id}/submit", response_model=Dict[str, Any])
async def submit_test(
	test_id: int,
	payload: TestSubmitRequest,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	role = role_to_str(current_user.get("role"))
	if role not in ("teacher", "admin"):
		assert_can_view_user_data(current_user, str(payload.user_id))
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	questions = sorted(test.questions, key=lambda question: question.id or 0)
	if len(payload.answers) != len(questions):
		raise HTTPException(status_code=400, detail="Answers count mismatch")

	homework: Optional[Homework] = None
	if payload.homework_id is not None:
		homework = db.get(Homework, payload.homework_id)
		if not homework:
			raise HTTPException(status_code=404, detail="Homework not found")
		if homework.assigned_to != payload.user_id:
			raise HTTPException(status_code=403, detail="Homework is assigned to another student")
		if homework.test_id and homework.test_id != test_id:
			raise HTTPException(status_code=400, detail="Homework is linked to another test")

	question_results = [_evaluate_question(question, answer) for question, answer in zip(questions, payload.answers)]
	correct_count = sum(1 for item in question_results if item.get("is_correct"))
	total_questions = len(question_results)
	score_pct = int(round(100 * correct_count / max(1, total_questions)))
	wrong_results = [item for item in question_results if not item.get("is_correct")]

	feedback = None
	summary = None
	try:
		assistant = _assistant()
		wrong_lines = "\n".join(
			f"- {item['question']} | ответ ученика: {item.get('student_answer')} | правильный: {item.get('correct_answer_text')}"
			for item in wrong_results[:5]
		)
		prompt = (
			f"Ученик выполнил тест '{test.title}'. "
			f"Результат: {correct_count} из {total_questions} ({score_pct}%).\n"
			"Дай короткий разбор, что получилось, что повторить и как двигаться дальше.\n"
			f"Ошибки:\n{wrong_lines or '- Ошибок нет'}"
		)
		feedback = assistant._generate(prompt, max_new_tokens=220)
		summary = feedback
	except Exception:
		feedback = None
		summary = None

	submission = TestSubmission(
		test_id=test_id,
		homework_id=payload.homework_id,
		user_id=payload.user_id,
		answers=[answer.dict() for answer in payload.answers],
		question_results=question_results,
		correct_count=correct_count,
		total_questions=total_questions,
		summary=summary,
		score=score_pct,
		feedback=feedback,
		created_at=datetime.utcnow(),
	)
	db.add(submission)
	db.flush()

	if homework is not None:
		homework_submission = HomeworkSubmission(
			homework_id=homework.id,
			user_id=payload.user_id,
			test_submission_id=submission.id,
			score=float(score_pct),
			feedback=feedback,
			created_at=datetime.utcnow(),
		)
		db.add(homework_submission)
		homework.status = "submitted"
		db.add(homework)

	try:
		analytics_service = get_analytics_service()
		cognitive_profile = get_orchestrator().profiler.get_profile(payload.user_id)
		analytics_service.process_test_result(
			user_id=payload.user_id,
			test_result={
				"subject": test.topic or test.title,
				"accuracy": score_pct,
				"errors": [item["question"] for item in wrong_results],
				"time_spent_seconds": payload.time_spent_seconds,
			},
			cognitive_profile=cognitive_profile,
		)
	except Exception:
		pass

	try:
		orchestrator = get_orchestrator()
		for idx, item in enumerate(question_results):
			orchestrator.process_task_submission(
				user_id=payload.user_id,
				task_id=item.get("question_id") or idx + 1,
				question=item.get("question") or "",
				user_answer=str(item.get("student_answer") or ""),
				correct_answer=str(item.get("correct_answer_text") or ""),
				topic=test.topic or test.title,
			)
	except Exception:
		pass

	db.commit()
	db.refresh(submission)

	return {
		"submission_id": submission.id,
		"homework_id": payload.homework_id,
		"score": score_pct,
		"correct": correct_count,
		"total": total_questions,
		"summary": summary,
		"feedback": feedback,
		"question_results": question_results,
	}


@router.get("/tests/submissions/{submission_id}", response_model=Dict[str, Any])
async def get_test_submission_detail(
	submission_id: int,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	submission = db.get(TestSubmission, submission_id)
	if not submission:
		raise HTTPException(status_code=404, detail="Submission not found")
	assert_can_view_user_data(current_user, str(submission.user_id))
	test = db.get(Test, submission.test_id)
	return _serialize_submission(submission, test=test)


@router.get("/tests/{test_id}/submissions", response_model=List[Dict[str, Any]])
async def list_test_submissions(
	test_id: int,
	db: Session = Depends(get_db),
	_staff: dict = Depends(require_roles("teacher", "admin")),
):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	stmt = select(TestSubmission).where(TestSubmission.test_id == test_id).order_by(TestSubmission.created_at.desc())
	rows = db.execute(stmt).scalars().all()
	return [
		{
			"id": row.id,
			"user_id": row.user_id,
			"homework_id": row.homework_id,
			"score": row.score,
			"correct_count": row.correct_count,
			"total_questions": row.total_questions,
			"summary": row.summary,
			"feedback": row.feedback,
			"created_at": row.created_at.isoformat() if row.created_at else None,
		}
		for row in rows
	]


@router.post("/tests/assign", response_model=Dict[str, Any])
async def assign_test_to_students(
	payload: TestAssignRequest,
	db: Session = Depends(get_db),
	_staff: dict = Depends(require_roles("teacher", "admin")),
):
	if not payload.student_ids:
		raise HTTPException(status_code=400, detail="student_ids is required")

	assignment_type = (payload.assignment_type or "homework").lower()
	if assignment_type not in {"homework", "control", "quiz"}:
		raise HTTPException(status_code=400, detail="assignment_type must be one of: homework, control, quiz")

	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")

	test = db.get(Test, payload.test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	created_homeworks: List[Homework] = []
	assignment_label_map = {
		"homework": "ДЗ",
		"control": "КР",
		"quiz": "Проверочная",
	}
	assignment_label = assignment_label_map.get(assignment_type, "ДЗ")

	for student_id in payload.student_ids:
		homework = Homework(
			title=f"{assignment_label}: {test.title}",
			description=f"Назначенный тест по теме: {test.topic or test.title}",
			subject=test.topic or "Тест",
			due_date=payload.due_date,
			kind="test",
			test_id=test.id,
			assignment_type=assignment_type,
			status="new",
			assigned_to=student_id,
			created_by=payload.created_by or test.creator_id,
		)
		db.add(homework)
		created_homeworks.append(homework)

	db.commit()
	for homework in created_homeworks:
		db.refresh(homework)

	return {
		"success": True,
		"assigned_count": len(created_homeworks),
		"homeworks": [
			{
				"id": homework.id,
				"assigned_to": homework.assigned_to,
				"title": homework.title,
				"test_id": homework.test_id,
				"assignment_type": homework.assignment_type,
				"due_date": homework.due_date.isoformat() if homework.due_date else None,
			}
			for homework in created_homeworks
		],
	}


