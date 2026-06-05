"""
API маршруты для RAG: индексирование тем/учебника и классификация темы вопроса.
Управляющие операции доступны только учителю/админу.
"""
import re
import threading
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from routes.auth import require_roles, get_current_user
from services.rag import get_rag_service, DEFAULT_MATH_TAXONOMY

router = APIRouter()

# Фоновые задачи индексации (PDF может обрабатываться несколько минут).
_ingest_jobs: Dict[str, Dict[str, Any]] = {}
_ingest_jobs_lock = threading.Lock()


def _set_ingest_job(source: str, payload: Dict[str, Any]) -> None:
    with _ingest_jobs_lock:
        _ingest_jobs[source] = payload


def _get_ingest_job(source: str) -> Optional[Dict[str, Any]]:
    with _ingest_jobs_lock:
        job = _ingest_jobs.get(source)
        return dict(job) if job else None


def _run_ingest_job(source: str, text: str, topic_hint: Optional[str]) -> None:
    rag = get_rag_service()
    try:
        added, err = rag.ingest_textbook(source, text, topic_hint=topic_hint)
        if added == 0:
            _set_ingest_job(
                source,
                {
                    "status": "error",
                    "source": source,
                    "added": 0,
                    "error": err or "Не удалось проиндексировать PDF.",
                },
            )
            return
        _set_ingest_job(
            source,
            {
                "status": "done",
                "source": source,
                "added": added,
                "auto_topics": bool(not topic_hint),
                "topic_breakdown": rag.topic_breakdown(source),
            },
        )
    except Exception as e:
        _set_ingest_job(
            source,
            {
                "status": "error",
                "source": source,
                "added": 0,
                "error": str(e),
            },
        )


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
        "topics": rag.list_topics(),
        "topic_groups": rag.list_topic_groups(),
    }


@router.delete("/rag/source", response_model=Dict[str, Any])
async def rag_delete_source(
    source: str,
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    """Удаляет все фрагменты одного источника (для перезаливки учебника без дублей)."""
    deleted = get_rag_service().delete_source(source)
    return {"deleted": deleted, "source": source}


@router.delete("/rag/topic", response_model=Dict[str, Any])
async def rag_delete_topic(
    topic: str,
    source: Optional[str] = None,
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    """Удаляет все фрагменты темы (опционально — в пределах одного источника)."""
    deleted = get_rag_service().delete_topic(topic, source=source)
    return {"deleted": deleted, "topic": topic, "source": source}


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
    added, err = rag.ingest_textbook(req.title, req.content, topic_hint=req.topic_hint)
    if added == 0:
        raise HTTPException(status_code=500, detail=err or "Не удалось проиндексировать текст.")
    return {
        "added": added,
        "source": req.title,
        "auto_topics": bool(not req.topic_hint),
        "topic_breakdown": rag.topic_breakdown(req.title),
    }


@router.get("/rag/ingest-job", response_model=Dict[str, Any])
async def rag_ingest_job(
    source: str,
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    """Статус фоновой индексации PDF (после POST /rag/ingest-pdf)."""
    job = _get_ingest_job(source)
    if not job:
        raise HTTPException(status_code=404, detail="Задача индексации не найдена")
    return job


@router.post("/rag/ingest-pdf", response_model=Dict[str, Any])
async def rag_ingest_pdf(
    file: UploadFile = File(...),
    topic_hint: Optional[str] = Form(None),
    _staff: dict = Depends(require_roles("teacher", "admin")),
):
    rag = get_rag_service()
    if not rag.embeddings_available():
        raise HTTPException(status_code=503, detail="Эмбеддинги недоступны: проверьте PROXYAPI_KEY.")
    filename = (file.filename or "upload.pdf").strip()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Ожидается PDF файл")
    try:
        from pypdf import PdfReader
        import io

        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Файл пустой")
        reader = PdfReader(io.BytesIO(raw))
        pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
        text = "\n\n".join(t for t in pages_text if t)
        pages_with_text = sum(1 for t in pages_text if t)
        total_pages = len(reader.pages)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка разбора PDF: {e}")

    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail=(
                "PDF не содержит извлекаемого текста (возможно, это скан без OCR). "
                f"Страниц с текстом: {pages_with_text} из {total_pages}. "
                "Попробуйте другой PDF или вставьте текст вручную через «Добавить текст»."
            ),
        )

    # Безопасное имя источника для БД (кириллица в filename допустима, но убираем путь).
    source = re.sub(r"[^\w.\- ()\u0400-\u04FF]", "_", filename.split("/")[-1].split("\\")[-1])[:200]

    existing = _get_ingest_job(source)
    if existing and existing.get("status") == "processing":
        raise HTTPException(status_code=409, detail="Индексация этого файла уже выполняется")

    _set_ingest_job(
        source,
        {
            "status": "processing",
            "source": source,
            "added": 0,
            "pages_with_text": pages_with_text,
            "total_pages": total_pages,
            "auto_topics": bool(not topic_hint),
        },
    )
    thread = threading.Thread(
        target=_run_ingest_job,
        args=(source, text, topic_hint),
        daemon=True,
    )
    thread.start()

    return {
        "status": "processing",
        "added": 0,
        "source": source,
        "pages_with_text": pages_with_text,
        "total_pages": total_pages,
        "auto_topics": bool(not topic_hint),
        "message": "PDF принят, индексация идёт в фоне. Опросите /rag/ingest-job или дождитесь завершения в UI.",
    }


@router.get("/rag/classify", response_model=Dict[str, Any])
async def rag_classify(
    question: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Отладка определения темы: показывает ИТОГ (как в адаптивных заданиях)
    и отдельно — ближайшие фрагменты RAG для справки.
    """
    from routes.agents import (
        _detect_strong_symbolic_topic,
        _detect_topic_by_keywords,
        resolve_specific_topic,
    )

    rag = get_rag_service()
    matches = rag.search(question, top_k=3)

    # Какой шаг сработал в гибридной цепочке (символы → ключевые слова → RAG → fallback)
    method = "fallback"
    method_label = "Тема по умолчанию (ни один метод не сработал)"
    symbolic = _detect_strong_symbolic_topic(question)
    if symbolic:
        method = "symbolic"
        method_label = "Символьный признак в условии (x^2, √, |…|, система)"
        resolved_topic = symbolic
    else:
        keywords = _detect_topic_by_keywords(question)
        if keywords:
            method = "keywords"
            method_label = "Ключевые слова в тексте задачи"
            resolved_topic = keywords
        else:
            rag_match = rag.classify_topic(question)
            if rag_match and rag_match.get("topic"):
                method = "rag"
                score_pct = int(round(float(rag_match.get("score", 0)) * 100))
                method_label = f"Семантический поиск по базе знаний (близость {score_pct}%)"
                resolved_topic = rag_match["topic"]
            else:
                resolved_topic = resolve_specific_topic(question, "общая математика")

    return {
        "question": question,
        # Итог — именно это попадёт в профиль ученика при сдаче задания
        "resolved_topic": resolved_topic,
        "method": method,
        "method_label": method_label,
        # Сырые совпадения RAG (куски учебника/тем); topic может быть именем PDF, если не указали раздел при загрузке
        "matches": matches,
        "matches_note": (
            "Ниже — ближайшие фрагменты учебника в индексе. "
            "Тема фрагмента — название параграфа/§ из книги. "
            "Итоговая тема выше может определяться правилами (x^2 → квадратные), если они сработали раньше RAG."
        ),
    }
