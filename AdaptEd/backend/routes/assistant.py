from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.assistant import get_assistant_service
from services.student_analytics import get_analytics_service
from utils.persistent_storage import persistent_storage
from utils.db import has_db, get_db
from utils.auth_service import auth_service, role_to_str
from utils.orchestrator_singleton import get_orchestrator
from routes.auth import get_current_user, assert_can_view_user_data
from models.homework import Homework
from models.test import TestSubmission, Test

router = APIRouter()


class ChatMessage(BaseModel):
	role: str
	content: str


class ChatRequest(BaseModel):
	messages: List[ChatMessage]
	mode: Optional[str] = "general"  # general | hint
	context: Optional[Dict[str, Any]] = None
	user_id: Optional[str] = None  # ID ученика для персонализации
	user_name: Optional[str] = None  # Имя ученика
	viewer_role: Optional[str] = None  # student | teacher | admin
	target_user_id: Optional[str] = None  # Ученик, о котором спрашивает учитель


class QuickReplyOption(BaseModel):
	text: str


class MotivationRequest(BaseModel):
	topic: str
	student_name: Optional[str] = None
	deadline: Optional[str] = None


class HintRequest(BaseModel):
	task_text: str
	student_level: Optional[str] = None


class DocumentUpload(BaseModel):
	title: str
	content: str  # plain text for now; could be extracted from PDF elsewhere


class TestResultRequest(BaseModel):
	"""Запрос для обработки результата теста"""
	user_id: str
	subject: str
	accuracy: float  # 0-100
	errors: List[str] = []
	time_spent_seconds: Optional[float] = None


class TaskAttemptRequest(BaseModel):
	"""Запрос для обработки попытки выполнения задания"""
	user_id: str
	is_correct: bool
	error_type: Optional[str] = None
	time_spent_seconds: Optional[float] = None


class ChatSessionCreateRequest(BaseModel):
	user_id: str
	title: Optional[str] = None


class ChatSessionRenameRequest(BaseModel):
	title: str


class ChatSessionMessagesUpdateRequest(BaseModel):
	messages: List[Dict[str, Any]]


def _parse_iso_dt(value: Any) -> datetime:
	if isinstance(value, datetime):
		return value
	if isinstance(value, str) and value.strip():
		raw = value.strip()
		try:
			parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
			if parsed.tzinfo is not None:
				return parsed.replace(tzinfo=None)
			return parsed
		except Exception:
			pass
	return datetime.utcnow()


def _safe_parse_messages(raw: Any) -> List[Dict[str, Any]]:
	if isinstance(raw, list):
		return raw
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, list) else []
		except Exception:
			return []
	return []


def _normalize_viewer_role(requested_role: Optional[str], current_user: Dict[str, Any]) -> str:
	actual_role = role_to_str(current_user.get("role"))
	requested = (requested_role or actual_role or "student").lower()
	if actual_role == "admin" and requested in {"student", "teacher", "admin"}:
		return requested
	return actual_role


def _analytics_to_lines(analytics: Any) -> List[str]:
	if not isinstance(analytics, dict):
		return []

	lines: List[str] = []
	struggling_topics = analytics.get("struggling_topics")
	if isinstance(struggling_topics, list) and struggling_topics:
		formatted = []
		for item in struggling_topics[:5]:
			if isinstance(item, dict):
				name = item.get("topic") or item.get("name")
				value = item.get("score") or item.get("mastery")
				if name and value is not None:
					formatted.append(f"{name} ({value})")
				elif name:
					formatted.append(str(name))
			elif item:
				formatted.append(str(item))
		if formatted:
			lines.append("Проблемные темы по аналитике: " + ", ".join(formatted))

	recommendations = analytics.get("recommendations")
	if isinstance(recommendations, list) and recommendations:
		formatted = []
		for item in recommendations[:3]:
			if isinstance(item, dict):
				text = item.get("title") or item.get("action") or item.get("recommendation")
				if text:
					formatted.append(str(text))
			elif item:
				formatted.append(str(item))
		if formatted:
			lines.append("Текущие рекомендации аналитики: " + "; ".join(formatted))

	return lines


def _build_teacher_student_context(target_user_id: str, db: Optional[Session]) -> str:
	student = auth_service.get_user_by_id(target_user_id)
	if not student:
		return "Данные по ученику не найдены."

	profile = get_orchestrator().profiler.get_profile(target_user_id)
	analytics = get_analytics_service().get_analytics(target_user_id)
	lines = [
		f"Ученик: {student.get('full_name') or student.get('email') or target_user_id}.",
		f"Класс: {student.get('class_id') or 'не указан'}.",
	]

	if profile:
		lines.append(
			f"Профиль: точность {round(float(getattr(profile, 'accuracy_rate', 0.0) or 0.0), 1)}%, "
			f"баллы {int(getattr(profile, 'points', 0) or 0)}, "
			f"уровень {int(getattr(profile, 'level', 1) or 1)}."
		)
		topic_mastery = getattr(profile, "topic_mastery", {}) or {}
		if topic_mastery:
			weak_topics = sorted(
				[(topic, mastery) for topic, mastery in topic_mastery.items()],
				key=lambda item: float(item[1]),
			)
			if weak_topics:
				lines.append(
					"Слабые темы: "
					+ ", ".join(f"{topic} ({round(float(mastery) * 100)}%)" for topic, mastery in weak_topics[:5])
				)
			strong_topics = sorted(
				[(topic, mastery) for topic, mastery in topic_mastery.items()],
				key=lambda item: float(item[1]),
				reverse=True,
			)
			if strong_topics:
				lines.append(
					"Сильные темы: "
					+ ", ".join(f"{topic} ({round(float(mastery) * 100)}%)" for topic, mastery in strong_topics[:3])
				)

	lines.extend(_analytics_to_lines(analytics))

	if has_db() and db is not None:
		submissions = (
			db.execute(
				select(TestSubmission)
				.where(TestSubmission.user_id == target_user_id)
				.order_by(TestSubmission.created_at.desc())
			)
			.scalars()
			.all()
		)
		recent_submissions = submissions[:5]
		if recent_submissions:
			scores = [float(sub.score or 0.0) for sub in recent_submissions]
			lines.append(
				f"Последние тесты: {len(recent_submissions)} попыток, средний результат {round(sum(scores) / max(1, len(scores)), 1)}%."
			)
			detailed_scores = []
			for sub in recent_submissions[:3]:
				test_title = "Тест"
				if sub.test_id:
					test_obj = db.get(Test, sub.test_id)
					if test_obj and (test_obj.title or test_obj.topic):
						test_title = test_obj.title or test_obj.topic
				detailed_scores.append(
					f"{test_title}: {sub.correct_count or 0}/{sub.total_questions or 0} ({sub.score or 0}%)"
				)
			if detailed_scores:
				lines.append("Последние результаты: " + "; ".join(detailed_scores))

		homeworks = (
			db.execute(
				select(Homework)
				.where(Homework.assigned_to == target_user_id)
				.order_by(Homework.created_at.desc())
			)
			.scalars()
			.all()
		)
		active_homeworks = [hw for hw in homeworks if hw.status in {"new", "in_progress"}]
		if active_homeworks:
			now = datetime.utcnow()
			overdue = [
				hw for hw in active_homeworks
				if hw.due_date and hw.due_date < now
			]
			lines.append(
				f"Активные назначения: {len(active_homeworks)}, просроченные: {len(overdue)}."
			)
			for hw in active_homeworks[:5]:
				deadline = hw.due_date.strftime("%d.%m.%Y") if hw.due_date else "без дедлайна"
				lines.append(
					f"- {hw.title}: статус {hw.status}, дедлайн {deadline}, тип {hw.assignment_type or hw.kind or 'задание'}."
				)

	return "\n".join(lines)


def _build_teacher_class_context(db: Optional[Session]) -> str:
	students = [u for u in auth_service.get_all_users() if role_to_str(u.get("role")) == "student"]
	if not students:
		return "В системе пока нет учеников."

	lines = [f"В системе учеников: {len(students)}."]
	snapshot = []
	for student in students:
		user_id = str(student.get("user_id", "")).strip()
		if not user_id:
			continue
		profile = get_orchestrator().profiler.get_profile(user_id)
		accuracy = round(float(getattr(profile, "accuracy_rate", 0.0) or 0.0), 1) if profile else 0.0
		weakest_topic = None
		if profile and getattr(profile, "topic_mastery", None):
			weakest_topic = min(profile.topic_mastery.items(), key=lambda item: float(item[1]))
		snapshot.append({
			"name": student.get("full_name") or student.get("email") or user_id,
			"accuracy": accuracy,
			"weakest_topic": weakest_topic,
		})

	snapshot.sort(key=lambda item: item["accuracy"])
	if snapshot:
		lines.append("Ученики, которым сейчас нужна помощь:")
		for item in snapshot[:5]:
			weakest = item["weakest_topic"]
			weak_text = (
				f", слабая тема {weakest[0]} ({round(float(weakest[1]) * 100)}%)"
				if weakest else ""
			)
			lines.append(f"- {item['name']}: точность {item['accuracy']}%{weak_text}.")

	if has_db() and db is not None:
		now = datetime.utcnow()
		active_homeworks = (
			db.execute(
				select(Homework)
				.where(Homework.status.in_(["new", "in_progress"]))
				.order_by(Homework.due_date.asc())
			)
			.scalars()
			.all()
		)
		overdue = [hw for hw in active_homeworks if hw.due_date and hw.due_date < now]
		if active_homeworks:
			lines.append(
				f"По всему классу активных домашних заданий и тестов: {len(active_homeworks)}, из них просроченных: {len(overdue)}."
			)

	return "\n".join(lines)


def _build_quick_replies(
	viewer_role: str,
	assistant_text: str,
	last_user_message: Optional[str],
	target_user_name: Optional[str] = None,
) -> List[Dict[str, str]]:
	text = (assistant_text or "").lower()
	last_user = (last_user_message or "").lower()

	if viewer_role == "teacher":
		name = target_user_name or "ученика"
		if target_user_name:
			return [
				{"text": f"Какие темы {name} нужно повторить в первую очередь?"},
				{"text": f"Какой короткий тест лучше дать {name} следующим?"},
				{"text": f"Составь план работы с {name} на неделю."},
				{"text": f"Какие задания сейчас висят у {name}?"},
			]
		return [
			{"text": "У кого сейчас самые большие пробелы?"},
			{"text": "Какие темы проседают у класса чаще всего?"},
			{"text": "Какой тест лучше дать классу следующим?"},
			{"text": "Составь краткий план работы с группой на неделю."},
		]

	if any(phrase in text for phrase in ["увлеч", "интерес", "нравится делать", "любишь"]):
		return [
			{"text": "Люблю игры"},
			{"text": "Люблю спорт"},
			{"text": "Люблю музыку"},
			{"text": "Люблю рисовать"},
			{"text": "Мне нравится программирование"},
		]

	if any(phrase in text for phrase in ["что было сложно", "что сложнее", "что не получается", "что вызывает трудности"]):
		return [
			{"text": "Сложно понять условие"},
			{"text": "Путаюсь в формулах"},
			{"text": "Не знаю, с чего начать"},
			{"text": "Считаю медленно"},
		]

	if any(phrase in last_user for phrase in ["не понимаю", "сложно", "трудно", "не получается"]):
		return [
			{"text": "Объясни совсем простыми словами"},
			{"text": "Покажи похожий пример"},
			{"text": "Дай маленькую подсказку"},
			{"text": "Задай мне наводящий вопрос"},
		]

	if "?" in assistant_text or len(assistant_text) > 260:
		return [
			{"text": "Понял, идем дальше"},
			{"text": "Можно короче"},
			{"text": "Покажи пример"},
			{"text": "Дай задание для тренировки"},
		]

	return []


def _db_get_user_chats(user_id: str) -> Optional[List[Dict[str, Any]]]:
	if not has_db():
		return None
	sess = get_db()
	if sess is None:
		return None
	try:
		from models.chat import ChatSession  # type: ignore
		rows = (
			sess.query(ChatSession)
			.filter(ChatSession.user_id == user_id)
			.order_by(ChatSession.updated_at.desc())
			.all()
		)
		return [
			{
				"id": row.id,
				"title": row.title or "Новый чат",
				"created_at": row.created_at.isoformat() if row.created_at else None,
				"updated_at": row.updated_at.isoformat() if row.updated_at else None,
				"messages": _safe_parse_messages(row.messages_json),
			}
			for row in rows
		]
	finally:
		try:
			sess.close()
		except Exception:
			pass


def _db_migrate_user_chats_from_storage(user_id: str):
	"""
	One-time migration for a user:
	- if DB has no chats for user and persistent_storage has chats, copy them to DB
	- then remove migrated user chats from persistent_storage
	"""
	if not has_db():
		return
	store = _chat_store()
	legacy_chats = store.get(user_id, [])
	if not isinstance(legacy_chats, list) or len(legacy_chats) == 0:
		return

	sess = get_db()
	if sess is None:
		return
	try:
		from models.chat import ChatSession  # type: ignore
		db_count = sess.query(ChatSession).filter(ChatSession.user_id == user_id).count()
		if db_count > 0:
			return

		for chat in legacy_chats:
			row = ChatSession(
				id=str(chat.get("id") or str(uuid4())),
				user_id=user_id,
				title=str(chat.get("title") or "Новый чат"),
				messages_json=json.dumps(_safe_parse_messages(chat.get("messages")), ensure_ascii=False),
				created_at=_parse_iso_dt(chat.get("created_at")),
				updated_at=_parse_iso_dt(chat.get("updated_at")),
			)
			sess.add(row)
		sess.commit()

		# Remove migrated user chats from JSON storage to avoid split-brain state.
		store.pop(user_id, None)
		_save_chat_store(store)
	except Exception:
		sess.rollback()
	finally:
		try:
			sess.close()
		except Exception:
			pass


def _db_create_chat(user_id: str, chat_id: str, title: str) -> Optional[Dict[str, Any]]:
	if not has_db():
		return None
	sess = get_db()
	if sess is None:
		return None
	try:
		from models.chat import ChatSession  # type: ignore
		now = datetime.utcnow()
		row = ChatSession(
			id=chat_id,
			user_id=user_id,
			title=title,
			messages_json="[]",
			created_at=now,
			updated_at=now,
		)
		sess.add(row)
		sess.commit()
		return {
			"id": row.id,
			"title": row.title,
			"created_at": row.created_at.isoformat() if row.created_at else None,
			"updated_at": row.updated_at.isoformat() if row.updated_at else None,
			"messages": [],
		}
	except Exception:
		sess.rollback()
		return None
	finally:
		try:
			sess.close()
		except Exception:
			pass


def _db_update_chat_title(user_id: str, chat_id: str, title: str) -> Optional[Dict[str, Any]]:
	if not has_db():
		return None
	sess = get_db()
	if sess is None:
		return None
	try:
		from models.chat import ChatSession  # type: ignore
		row = sess.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.id == chat_id).first()
		if not row:
			return None
		row.title = title
		row.updated_at = datetime.utcnow()
		sess.commit()
		return {
			"id": row.id,
			"title": row.title,
			"created_at": row.created_at.isoformat() if row.created_at else None,
			"updated_at": row.updated_at.isoformat() if row.updated_at else None,
			"messages": _safe_parse_messages(row.messages_json),
		}
	except Exception:
		sess.rollback()
		return None
	finally:
		try:
			sess.close()
		except Exception:
			pass


def _db_delete_chat(user_id: str, chat_id: str) -> Optional[bool]:
	if not has_db():
		return None
	sess = get_db()
	if sess is None:
		return None
	try:
		from models.chat import ChatSession  # type: ignore
		row = sess.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.id == chat_id).first()
		if not row:
			return False
		sess.delete(row)
		sess.commit()
		return True
	except Exception:
		sess.rollback()
		return False
	finally:
		try:
			sess.close()
		except Exception:
			pass


def _db_save_chat_messages(user_id: str, chat_id: str, messages: List[Dict[str, Any]], generated_title: Optional[str]) -> Optional[Dict[str, Any]]:
	if not has_db():
		return None
	sess = get_db()
	if sess is None:
		return None
	try:
		from models.chat import ChatSession  # type: ignore
		row = sess.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.id == chat_id).first()
		if not row:
			return None
		row.messages_json = json.dumps(messages, ensure_ascii=False)
		if generated_title and (row.title in (None, "", "Новый чат")):
			row.title = generated_title
		row.updated_at = datetime.utcnow()
		sess.commit()
		return {
			"id": row.id,
			"title": row.title,
			"created_at": row.created_at.isoformat() if row.created_at else None,
			"updated_at": row.updated_at.isoformat() if row.updated_at else None,
			"messages": messages,
		}
	except Exception:
		sess.rollback()
		return None
	finally:
		try:
			sess.close()
		except Exception:
			pass


def _chat_store() -> Dict[str, List[Dict[str, Any]]]:
	store = persistent_storage.get("chat_sessions", {})
	if not isinstance(store, dict):
		store = {}
	return store


def _save_chat_store(store: Dict[str, List[Dict[str, Any]]]):
	persistent_storage.set("chat_sessions", store)


def _get_user_chats(user_id: str) -> List[Dict[str, Any]]:
	_db_migrate_user_chats_from_storage(user_id)
	db_chats = _db_get_user_chats(user_id)
	if db_chats is not None:
		return db_chats
	store = _chat_store()
	chats = store.get(user_id, [])
	if not isinstance(chats, list):
		return []
	return chats


def _find_chat(user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
	chats = _get_user_chats(user_id)
	for chat in chats:
		if chat.get("id") == chat_id:
			return chat
	return None


def _generate_chat_title(first_message: str) -> str:
	text = (first_message or "").strip()
	if not text:
		return "Новый чат"
	try:
		assistant_service = get_assistant_service()
		prompt = (
			"Сгенерируй короткое название чата (2-6 слов) по сообщению ученика. "
			"Верни только название без кавычек и без точки.\n"
			f"Сообщение: {text}"
		)
		raw = assistant_service._generate(prompt, max_new_tokens=32).strip()
		candidate = raw.split("\n")[0].strip().strip('"').strip("'")
		if candidate:
			return candidate[:80]
	except Exception:
		pass
	return text[:60] + ("..." if len(text) > 60 else "")


@router.get("/assistant/chats/{user_id}", response_model=List[Dict[str, Any]])
async def list_chats(user_id: str):
	try:
		chats = _get_user_chats(user_id)
		ordered = sorted(chats, key=lambda c: c.get("updated_at", ""), reverse=True)
		return [
			{
				"id": chat.get("id"),
				"title": chat.get("title", "Новый чат"),
				"created_at": chat.get("created_at"),
				"updated_at": chat.get("updated_at"),
				"message_count": len(chat.get("messages", [])),
			}
			for chat in ordered
		]
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/chats", response_model=Dict[str, Any])
async def create_chat(req: ChatSessionCreateRequest):
	try:
		chat_id = str(uuid4())
		db_chat = _db_create_chat(req.user_id, chat_id, req.title or "Новый чат")
		if db_chat is not None:
			return db_chat

		store = _chat_store()
		if req.user_id not in store:
			store[req.user_id] = []
		now = datetime.utcnow().isoformat()
		chat = {
			"id": chat_id,
			"title": req.title or "Новый чат",
			"created_at": now,
			"updated_at": now,
			"messages": [],
		}
		store[req.user_id].append(chat)
		_save_chat_store(store)
		return chat
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/chats/{user_id}/{chat_id}", response_model=Dict[str, Any])
async def get_chat(user_id: str, chat_id: str):
	try:
		chat = _find_chat(user_id, chat_id)
		if not chat:
			raise HTTPException(status_code=404, detail="Chat not found")
		return chat
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.put("/assistant/chats/{user_id}/{chat_id}", response_model=Dict[str, Any])
async def rename_chat(user_id: str, chat_id: str, req: ChatSessionRenameRequest):
	try:
		db_chat = _db_update_chat_title(user_id, chat_id, req.title.strip() or "Новый чат")
		if db_chat is not None:
			return db_chat

		store = _chat_store()
		chats = store.get(user_id, [])
		for chat in chats:
			if chat.get("id") == chat_id:
				chat["title"] = req.title.strip() or "Новый чат"
				chat["updated_at"] = datetime.utcnow().isoformat()
				_save_chat_store(store)
				return chat
		raise HTTPException(status_code=404, detail="Chat not found")
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assistant/chats/{user_id}/{chat_id}", response_model=Dict[str, Any])
async def delete_chat(user_id: str, chat_id: str):
	try:
		db_result = _db_delete_chat(user_id, chat_id)
		if db_result is True:
			return {"ok": True}
		if db_result is False:
			raise HTTPException(status_code=404, detail="Chat not found")

		store = _chat_store()
		chats = store.get(user_id, [])
		next_chats = [chat for chat in chats if chat.get("id") != chat_id]
		if len(next_chats) == len(chats):
			raise HTTPException(status_code=404, detail="Chat not found")
		store[user_id] = next_chats
		_save_chat_store(store)
		return {"ok": True}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.put("/assistant/chats/{user_id}/{chat_id}/messages", response_model=Dict[str, Any])
async def save_chat_messages(user_id: str, chat_id: str, req: ChatSessionMessagesUpdateRequest):
	try:
		generated_title = None
		first_user = next((m for m in req.messages if m.get("sender") == "user"), None)
		if first_user and first_user.get("text"):
			generated_title = _generate_chat_title(str(first_user.get("text")))

		db_chat = _db_save_chat_messages(user_id, chat_id, req.messages, generated_title)
		if db_chat is not None:
			return db_chat

		store = _chat_store()
		chats = store.get(user_id, [])
		for chat in chats:
			if chat.get("id") == chat_id:
				chat["messages"] = req.messages
				chat["updated_at"] = datetime.utcnow().isoformat()
				if chat.get("title") in (None, "", "Новый чат") and generated_title:
					chat["title"] = generated_title
				_save_chat_store(store)
				return chat
		raise HTTPException(status_code=404, detail="Chat not found")
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/chat", response_model=Dict[str, Any])
async def assistant_chat(
	req: ChatRequest,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	try:
		assistant_service = get_assistant_service()
		analytics_service = get_analytics_service()
		messages = [m.dict() for m in req.messages]
		viewer_role = _normalize_viewer_role(req.viewer_role, current_user)
		chat_user_id = str(current_user.get("user_id", "") or "")
		
		# Получаем последнее сообщение пользователя для анализа
		last_user_message = None
		for msg in reversed(messages):
			if msg.get("role") == "user":
				last_user_message = msg.get("content", "")
				break
		
		# Получаем слабые места ученика если есть user_id
		student_weaknesses = None
		cognitive_profile = None
		analytics_result = None
		teacher_target_name = None
		teacher_system_prompt = None
		teacher_context_payload = None
		
		if viewer_role == "teacher":
			target_user_id = req.target_user_id
			if target_user_id:
				assert_can_view_user_data(current_user, target_user_id)
				target_user = auth_service.get_user_by_id(target_user_id)
				teacher_target_name = (
					target_user.get("full_name") if target_user else None
				)
				teacher_context_payload = _build_teacher_student_context(target_user_id, db)
			else:
				teacher_context_payload = _build_teacher_class_context(db)

			teacher_system_prompt = (
				"Ты AI-ассистент для учителя. Отвечай как помощник педагога, а не как ученик. "
				"Анализируй пробелы, выделяй риски, предлагай темы для повторения, короткие тесты, домашние задания "
				"и конкретные педагогические действия. Если данных мало, прямо скажи об этом и предложи, что посмотреть дальше. "
				"Отвечай структурировано, по делу, без ролевой игры от лица ученика.\n\n"
				f"Контекст учителя:\n{teacher_context_payload or 'Нет дополнительных данных.'}"
			)
		elif chat_user_id:
			# Получаем профиль когнитивный для слабых мест
			profile = get_orchestrator().profiler.get_profile(chat_user_id)
			cognitive_profile = profile
			if profile:
				# Извлекаем слабые места из профиля
				weaknesses = []
				# Самые частые ошибки
				if profile.error_frequency:
					top_errors = sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
					weaknesses.extend([
						str(err[0].value) if hasattr(err[0], "value") else str(err[0])
						for err in top_errors
					])
				# Низкая точность по темам
				for topic, mastery in profile.topic_mastery.items():
					if mastery < 0.5:
						weaknesses.append(topic)
				student_weaknesses = weaknesses if weaknesses else None
			
			# Обновляем профиль личности на основе диалога
			assistant_service.update_personality_from_chat(chat_user_id, messages)
			
			# Обрабатываем сообщение через адаптивного педагога-аналитика
			if last_user_message:
				analytics_result = analytics_service.process_chat_message(
					user_id=chat_user_id,
					message=last_user_message,
					cognitive_profile=cognitive_profile
				)
		
		if req.mode == "hint" and req.context:
			task_text = str(req.context.get("task", ""))
			student_level = str(req.context.get("level", "")) or None
			text = assistant_service.hint(task_text=task_text, student_level=student_level)
			
			# Записываем запрос подсказки
			if chat_user_id and viewer_role != "teacher":
				analytics_service.record_hint_request(chat_user_id)
		else:
			text = assistant_service.chat(
				messages=messages,
				system_prompt=teacher_system_prompt,
				user_id=chat_user_id if viewer_role != "teacher" else None,
				user_name=req.user_name if viewer_role != "teacher" else teacher_target_name,
				student_weaknesses=student_weaknesses if viewer_role != "teacher" else None,
				context=req.context,
			)
		
		response = {
			"message": text,
			"viewer_role": viewer_role,
			"target_user_id": req.target_user_id,
			"quick_replies": _build_quick_replies(
				viewer_role=viewer_role,
				assistant_text=text,
				last_user_message=last_user_message,
				target_user_name=teacher_target_name,
			),
		}
		
		# Добавляем информацию о профиле личности если есть
		if chat_user_id and viewer_role != "teacher":
			personality_profile = assistant_service.get_personality_profile(chat_user_id)
			if personality_profile:
				response["personality_insights"] = {
					"communication_style": personality_profile.communication_style.dict(),
					"traits": {k: v.score for k, v in personality_profile.traits.items()},
					"mentioned_weaknesses": personality_profile.mentioned_weaknesses,
					"interests": personality_profile.interests,
				}
			
			# Добавляем сообщение об этике если это первое взаимодействие
			if analytics_result and analytics_result.get("ethics_message"):
				response["ethics_message"] = analytics_result["ethics_message"]
		
		return response
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/motivation", response_model=Dict[str, str])
async def assistant_motivation(req: MotivationRequest):
	try:
		assistant_service = get_assistant_service()
		text = assistant_service.motivational_message(
			topic=req.topic,
			student_name=req.student_name,
			deadline=req.deadline,
		)
		return {"message": text}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/hint", response_model=Dict[str, str])
async def assistant_hint(req: HintRequest):
	try:
		assistant_service = get_assistant_service()
		analytics_service = get_analytics_service()
		text = assistant_service.hint(task_text=req.task_text, student_level=req.student_level)
		
		# Записываем запрос подсказки (если есть user_id в контексте)
		# В реальном приложении user_id должен передаваться в запросе
		# Пока оставляем как есть
		
		return {"message": text}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/documents/upload", response_model=Dict[str, str])
async def upload_document(doc: DocumentUpload):
	try:
		assistant_service = get_assistant_service()
		assistant_service.add_document(title=doc.title, content=doc.content)
		return {"status": "ok", "title": doc.title}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/documents/upload-pdf", response_model=Dict[str, str])
async def upload_document_pdf(file: UploadFile = File(...), title: Optional[str] = None):
	"""Accepts a PDF, extracts text, and stores it as a document."""
	try:
		if not file.filename.lower().endswith(".pdf"):
			raise HTTPException(status_code=400, detail="Ожидается PDF файл")
		content_bytes = await file.read()
		try:
			from pypdf import PdfReader  # lightweight PDF text extract
			import io
			reader = PdfReader(io.BytesIO(content_bytes))
			texts = []
			for page in reader.pages:
				texts.append(page.extract_text() or "")
			full_text = "\n\n".join(texts)
		except Exception as e:
			raise HTTPException(status_code=500, detail=f"Ошибка разбора PDF: {e}")
		assistant_service = get_assistant_service()
		assistant_service.add_document(title=title or file.filename, content=full_text)
		return {"status": "ok", "title": title or file.filename}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/analytics/{user_id}", response_model=Dict[str, Any])
async def get_student_analytics(user_id: str):
	"""Получить аналитические данные об ученике"""
	try:
		analytics_service = get_analytics_service()
		analytics_data = analytics_service.get_analytics(user_id)
		return analytics_data
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/analytics/test-result", response_model=Dict[str, Any])
async def process_test_result(req: TestResultRequest):
	"""Обработать результат теста и обновить аналитику"""
	try:
		analytics_service = get_analytics_service()
		
		# Получаем cognitive profile для синхронизации
		cognitive_profile = None
		if req.user_id:
			from utils.orchestrator_singleton import get_orchestrator

			cognitive_profile = get_orchestrator().profiler.get_profile(req.user_id)
		
		test_result = {
			"subject": req.subject,
			"accuracy": req.accuracy,
			"errors": req.errors,
			"time_spent_seconds": req.time_spent_seconds
		}
		
		result = analytics_service.process_test_result(
			user_id=req.user_id,
			test_result=test_result,
			cognitive_profile=cognitive_profile
		)
		
		return result
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/analytics/task-attempt", response_model=Dict[str, Any])
async def process_task_attempt(req: TaskAttemptRequest):
	"""Обработать попытку выполнения задания и обновить аналитику"""
	try:
		analytics_service = get_analytics_service()
		
		# Получаем cognitive profile для синхронизации
		cognitive_profile = None
		if req.user_id:
			from utils.orchestrator_singleton import get_orchestrator

			cognitive_profile = get_orchestrator().profiler.get_profile(req.user_id)
		
		task_attempt = {
			"is_correct": req.is_correct,
			"error_type": req.error_type,
			"time_spent_seconds": req.time_spent_seconds
		}
		
		result = analytics_service.process_task_attempt(
			user_id=req.user_id,
			task_attempt=task_attempt,
			cognitive_profile=cognitive_profile
		)
		
		return result
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
