"""
API маршруты для RAG: индексирование тем/учебника и классификация темы вопроса.
Управляющие операции доступны только учителю/админу.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from routes.auth import require_roles, get_current_user
from services.rag import get_rag_service, DEFAULT_MATH_TAXONOMY

router = APIRouter()


class TaxonomyItem(BaseModel):
    topic: str
    text: Optional[str] = None


class IngestTopicsRequest(BaseModel):
    # Если items не переданы — засеваем дефолтную школьную математику.
    items: Optional[List[TaxonomyItem]] = None


class IngestTextRequest(BaseModel):
    title: str
    content: str
    topic_hint: Optional[str] = None


@router.get("/rag/status", response_model=Dict[str, Any])
async def rag_status(_staff: dict = Depends(require_roles("teacher", "admin"))):
    rag = get_rag_service()
    return {
        "embeddings_available": rag.embeddings_available(),
        "embeddings_model": rag.embeddings_model,
        "indexed_chunks": rag.count(),
        "sources": rag.list_sources(),
    }


@router.delete("/rag/source", response_model=Dict[str, Any])
async def rag_delete_source(
    source: str,
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    """Удаляет все фрагменты одного источника (для перезаливки учебника без дублей)."""
    deleted = get_rag_service().delete_source(source)
    return {"deleted": deleted, "source": source}


@router.delete("/rag/all", response_model=Dict[str, Any])
async def rag_clear_all(_staff: dict = Depends(require_roles("teacher", "admin"))):
    """Полностью очищает индекс базы знаний."""
    deleted = get_rag_service().clear_all()
    return {"deleted": deleted}


@router.post("/rag/ingest-topics", response_model=Dict[str, Any])
async def rag_ingest_topics(
    req: IngestTopicsRequest,
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    rag = get_rag_service()
    if not rag.embeddings_available():
        raise HTTPException(status_code=503, detail="Эмбеддинги недоступны: проверьте PROXYAPI_KEY.")
    items = None
    if req.items:
        items = [{"topic": it.topic, "text": it.text or it.topic} for it in req.items]
    added = rag.ingest_taxonomy(items)
    if added == 0:
        raise HTTPException(status_code=500, detail="Не удалось проиндексировать темы.")
    return {"added": added, "source": "taxonomy"}


@router.post("/rag/ingest-text", response_model=Dict[str, Any])
async def rag_ingest_text(
    req: IngestTextRequest,
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    rag = get_rag_service()
    if not rag.embeddings_available():
        raise HTTPException(status_code=503, detail="Эмбеддинги недоступны: проверьте PROXYAPI_KEY.")
    added = rag.ingest_textbook(req.title, req.content, topic_hint=req.topic_hint)
    if added == 0:
        raise HTTPException(status_code=500, detail="Не удалось проиндексировать текст.")
    return {"added": added, "source": req.title}


@router.post("/rag/ingest-pdf", response_model=Dict[str, Any])
async def rag_ingest_pdf(
    file: UploadFile = File(...),
    topic_hint: Optional[str] = Form(None),
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    rag = get_rag_service()
    if not rag.embeddings_available():
        raise HTTPException(status_code=503, detail="Эмбеддинги недоступны: проверьте PROXYAPI_KEY.")
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Ожидается PDF файл")
    try:
        from pypdf import PdfReader
        import io

        raw = await file.read()
        reader = PdfReader(io.BytesIO(raw))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка разбора PDF: {e}")
    added = rag.ingest_textbook(file.filename, text, topic_hint=topic_hint)
    if added == 0:
        raise HTTPException(status_code=500, detail="Не удалось проиндексировать PDF (пустой текст?).")
    return {"added": added, "source": file.filename}


@router.get("/rag/classify", response_model=Dict[str, Any])
async def rag_classify(
    question: str,
    current_user: dict = Depends(get_current_user),
):
    """Отладочный/служебный эндпоинт: к какой теме относится вопрос."""
    rag = get_rag_service()
    matches = rag.search(question, top_k=3)
    best = matches[0] if matches else None
    return {
        "question": question,
        "best_topic": best["topic"] if best else None,
        "best_score": best["score"] if best else None,
        "matches": matches,
    }
