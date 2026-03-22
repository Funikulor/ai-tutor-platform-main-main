"""
API маршруты библиотеки материалов
"""
from pathlib import Path
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from utils.persistent_storage import persistent_storage

router = APIRouter()


def _default_materials_path() -> Path:
    backend_dir = Path(__file__).resolve().parent.parent
    return backend_dir / "data" / "library_materials.json"


def _load_default_materials() -> List[Dict[str, Any]]:
    file_path = _default_materials_path()
    if not file_path.exists():
        return []
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _ensure_materials() -> List[Dict[str, Any]]:
    materials = persistent_storage.get("library_materials", [])
    if isinstance(materials, list) and materials:
        return materials

    defaults = _load_default_materials()
    persistent_storage.set("library_materials", defaults)
    return defaults


def _material_matches(
    m: Dict[str, Any],
    subject: Optional[str],
    material_type: Optional[str],
    query_lc: Optional[str],
) -> bool:
    if subject and subject != "all" and m.get("subject") != subject:
        return False
    if material_type and material_type != "all" and m.get("type") != material_type:
        return False
    if query_lc:
        if query_lc in str(m.get("title", "")).lower():
            return True
        if query_lc in str(m.get("description", "")).lower():
            return True
        if query_lc in str(m.get("topic", "")).lower():
            return True
        return False
    return True


@router.get("/materials", response_model=List[Dict[str, Any]])
async def list_materials(
    subject: Optional[str] = None,
    material_type: Optional[str] = None,
    q: Optional[str] = None,
):
    try:
        materials = _ensure_materials()
        query_lc = q.lower().strip() if q else None
        return [m for m in materials if _material_matches(m, subject, material_type, query_lc)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

