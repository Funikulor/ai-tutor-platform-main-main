from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from services.assistant import get_assistant_service

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


@router.post("/assistant/chat", response_model=Dict[str, Any])
async def assistant_chat(req: ChatRequest):
	try:
		assistant_service = get_assistant_service()
		messages = [m.dict() for m in req.messages]
		
		# Получаем слабые места ученика если есть user_id
		student_weaknesses = None
		if req.user_id:
			# Получаем профиль когнитивный для слабых мест
			from agents.orchestrator import AgentOrchestrator
			orchestrator = AgentOrchestrator()
			profile = orchestrator.profiler.get_profile(req.user_id)
			if profile:
				# Извлекаем слабые места из профиля
				weaknesses = []
				# Самые частые ошибки
				if profile.error_frequency:
					top_errors = sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
					weaknesses.extend([str(err[0].value) for err in top_errors])
				# Низкая точность по темам
				for topic, mastery in profile.topic_mastery.items():
					if mastery < 0.5:
						weaknesses.append(topic)
				student_weaknesses = weaknesses if weaknesses else None
			
			# Обновляем профиль личности на основе диалога
			assistant_service.update_personality_from_chat(req.user_id, messages)
		
		if req.mode == "hint" and req.context:
			task_text = str(req.context.get("task", ""))
			student_level = str(req.context.get("level", "")) or None
			text = assistant_service.hint(task_text=task_text, student_level=student_level)
		else:
			text = assistant_service.chat(
				messages=messages,
				user_id=req.user_id,
				user_name=req.user_name,
				student_weaknesses=student_weaknesses
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
		text = assistant_service.hint(task_text=req.task_text, student_level=req.student_level)
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
