from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import json

from services.assistant import get_assistant_service
from services.student_analytics import get_analytics_service
from utils.persistent_storage import persistent_storage
from utils.db import has_db, get_db

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
async def assistant_chat(req: ChatRequest):
	try:
		assistant_service = get_assistant_service()
		analytics_service = get_analytics_service()
		messages = [m.dict() for m in req.messages]
		
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
		
		if req.user_id:
			# Получаем профиль когнитивный для слабых мест
			from utils.orchestrator_singleton import get_orchestrator

			profile = get_orchestrator().profiler.get_profile(req.user_id)
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
			assistant_service.update_personality_from_chat(req.user_id, messages)
			
			# Обрабатываем сообщение через адаптивного педагога-аналитика
			if last_user_message:
				analytics_result = analytics_service.process_chat_message(
					user_id=req.user_id,
					message=last_user_message,
					cognitive_profile=cognitive_profile
				)
		
		if req.mode == "hint" and req.context:
			task_text = str(req.context.get("task", ""))
			student_level = str(req.context.get("level", "")) or None
			text = assistant_service.hint(task_text=task_text, student_level=student_level)
			
			# Записываем запрос подсказки
			if req.user_id:
				analytics_service.record_hint_request(req.user_id)
		else:
			text = assistant_service.chat(
				messages=messages,
				user_id=req.user_id,
				user_name=req.user_name,
				student_weaknesses=student_weaknesses,
				context=req.context,
			)
		
		response = {"message": text}
		
		# Добавляем информацию о профиле личности если есть
		if req.user_id:
			personality_profile = assistant_service.get_personality_profile(req.user_id)
			if personality_profile:
				response["personality_insights"] = {
					"communication_style": personality_profile.communication_style.dict(),
					"traits": {k: v.score for k, v in personality_profile.traits.items()},
					"mentioned_weaknesses": personality_profile.mentioned_weaknesses
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
