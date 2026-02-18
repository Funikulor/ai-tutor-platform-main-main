from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import json

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.test import Test, TestQuestion, TestSubmission
from utils.db import get_db, has_db
from services.assistant import get_assistant_service

router = APIRouter()


class ManualQuestion(BaseModel):
	question: str
	options: List[str]
	correct_index: int
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


class TestSubmitRequest(BaseModel):
	user_id: str
	answers: List[int]  # индексы ответов по порядку вопросов


def _assistant():
	return get_assistant_service()


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
		data["questions"] = [
			{
				"id": q.id,
				"question": q.question,
				"options": q.options,
				"correct_index": q.correct_index,
				"explanation": q.explanation,
			}
			for q in test.questions
		]
	return data


@router.post("/tests/manual", response_model=Dict[str, Any])
async def create_manual_test(payload: ManualTestCreate, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	if not payload.questions:
		raise HTTPException(status_code=400, detail="Questions are required")

	test = Test(
		title=payload.title,
		topic=payload.topic,
		difficulty=payload.difficulty,
		source="manual",
		creator_id=payload.creator_id,
		created_at=datetime.utcnow(),
	)
	db.add(test)
	db.flush()

	for q in payload.questions:
		if q.correct_index < 0 or q.correct_index >= len(q.options):
			raise HTTPException(status_code=400, detail="correct_index is out of range")
		db.add(
			TestQuestion(
				test_id=test.id,
				question=q.question,
				options=q.options,
				correct_index=q.correct_index,
				explanation=q.explanation,
			)
		)

	db.commit()
	db.refresh(test)
	return {"test": _serialize_test(test, include_questions=True)}


@router.post("/tests/generate", response_model=Dict[str, Any])
async def generate_test(request: Request, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	try:
		payload = await request.json()
	except Exception:
		payload = None

	if payload is None:
		raise HTTPException(status_code=400, detail="Укажите тему для генерации теста (topic)")

	if not isinstance(payload, dict):
		raise HTTPException(status_code=400, detail="Некорректный формат запроса")

	topic = (payload.get("topic") or "").strip()
	difficulty = payload.get("difficulty") or "medium"
	question_count = payload.get("question_count") or 5
	creator_id = payload.get("creator_id")

	if not topic:
		raise HTTPException(status_code=400, detail="Укажите тему для генерации теста (topic)")

	assist = _assistant()
	print(f"[Tests] generate start topic='{topic}' diff='{difficulty}' count={question_count} creator={creator_id} db={getattr(getattr(db, 'bind', None), 'url', None)}")
	prompt = f"""Создай тест по теме "{topic}".
Сложность: {difficulty}.
Количество вопросов: {question_count}.

Формат ответа строго JSON:
{{
  "title": "...",
  "topic": "...",
  "difficulty": "...",
  "questions": [
    {{
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_index": 0,
      "explanation": "краткое объяснение"
    }}
  ]
}}
"""
	raw = assist._generate(prompt, max_new_tokens=800)
	print(f"[Tests] raw response len={len(raw)}")

	# Пытаемся вытащить JSON
	json_match = re.search(r"\{.*\}", raw, re.DOTALL)
	if not json_match:
		print("[Tests] JSON not found in raw response")
		raise HTTPException(status_code=500, detail="Failed to parse generated test")
	try:
		data = json.loads(json_match.group())
	except Exception as e:
		print(f"[Tests] JSON parse error: {e}")
		raise HTTPException(status_code=500, detail="Failed to parse generated test JSON")

	questions = data.get("questions") or []
	if not questions:
		print("[Tests] No questions in generated test")
		raise HTTPException(status_code=500, detail="No questions in generated test")

	title = data.get("title") or f"Тест по теме {topic}"
	topic = data.get("topic") or topic
	diff = data.get("difficulty") or difficulty
	print(f"[Tests] parsed title='{title}' topic='{topic}' diff='{diff}' questions={len(questions)}")

	test = Test(
		title=title,
		topic=topic,
		difficulty=diff,
		source="ai",
		creator_id=creator_id,
		created_at=datetime.utcnow(),
	)
	db.add(test)
	db.flush()

	for q in questions:
		opts = q.get("options") or []
		# поддерживаем оба ключа: correct_index и correct_answer
		correct_index = q.get("correct_index")
		if correct_index is None:
			correct_index = q.get("correct_answer", 0)
		if not isinstance(correct_index, int):
			correct_index = 0
		db.add(
			TestQuestion(
				test_id=test.id,
				question=q.get("question", ""),
				options=opts,
				correct_index=correct_index,
				explanation=q.get("explanation"),
			)
		)

	try:
		db.commit()
	except Exception:
		db.rollback()
		raise
	db.refresh(test)
	print(f"[Tests] saved test id={test.id} title={title} questions={len(questions)} topic={topic}")
	return {"test": _serialize_test(test, include_questions=True)}


@router.get("/tests", response_model=List[Dict[str, Any]])
async def list_tests(topic: Optional[str] = None, creator_id: Optional[str] = None, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	stmt = select(Test)
	if topic:
		stmt = stmt.where(Test.topic == topic)
	if creator_id:
		stmt = stmt.where(Test.creator_id == creator_id)
	rows = db.execute(stmt).scalars().all()
	return [_serialize_test(t, include_questions=False) for t in rows]


@router.get("/tests/{test_id}", response_model=Dict[str, Any])
async def get_test(test_id: int, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	return _serialize_test(test, include_questions=True)


@router.put("/tests/{test_id}", response_model=Dict[str, Any])
async def update_test(test_id: int, payload: ManualTestUpdate, db: Session = Depends(get_db)):
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

	# Если переданы вопросы — перезаписываем
	if payload.questions is not None:
		# удалить старые
		for q in list(test.questions):
			db.delete(q)
		db.flush()
		for q in payload.questions:
			if q.correct_index < 0 or q.correct_index >= len(q.options):
				raise HTTPException(status_code=400, detail="correct_index is out of range")
			db.add(
				TestQuestion(
					test_id=test.id,
					question=q.question,
					options=q.options,
					correct_index=q.correct_index,
					explanation=q.explanation,
				)
			)

	db.commit()
	db.refresh(test)
	return _serialize_test(test, include_questions=True)


@router.delete("/tests/{test_id}", response_model=Dict[str, Any])
async def delete_test(test_id: int, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	db.delete(test)
	db.commit()
	return {"ok": True}


@router.post("/tests/{test_id}/submit", response_model=Dict[str, Any])
async def submit_test(test_id: int, payload: TestSubmitRequest, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	questions = test.questions
	if len(payload.answers) != len(questions):
		raise HTTPException(status_code=400, detail="Answers count mismatch")

	correct = 0
	for ans, q in zip(payload.answers, questions):
		if ans == q.correct_index:
			correct += 1
	score_pct = int(round(100 * correct / max(1, len(questions))))

	feedback = None
	try:
		assist = _assistant()
		qtext = "\n".join([f"Вопрос: {q.question}\nТвой ответ: {a}, правильный: {q.correct_index}" for q, a in zip(questions, payload.answers)])
		prompt = f"Оцени результаты теста. Правильных ответов: {correct} из {len(questions)} ({score_pct}%). Дай 2-3 рекомендации кратко. \n{qtext}"
		feedback = assist._generate(prompt, max_new_tokens=200)
	except Exception:
		feedback = None

	sub = TestSubmission(
		test_id=test_id,
		user_id=payload.user_id,
		answers=payload.answers,
		score=score_pct,
		feedback=feedback,
		created_at=datetime.utcnow(),
	)
	db.add(sub)
	db.commit()
	db.refresh(sub)

	return {
		"score": score_pct,
		"correct": correct,
		"total": len(questions),
		"feedback": feedback,
		"submission_id": sub.id,
	}


