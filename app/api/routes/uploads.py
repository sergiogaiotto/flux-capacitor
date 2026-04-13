"""Upload de arquivos de contexto para apresentações."""
from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import require_api_key
from app.config import settings
from app.database.connection import sync_engine
from app.database.models import Attachment
from app.services.extractor import extract, guess_mime, is_image

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_ROOT = Path(settings.UPLOAD_DIR)
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

MAX_SIZE = 20 * 1024 * 1024  # 20MB por arquivo
ALLOWED_EXTS = {
    ".md", ".txt", ".csv", ".pdf", ".docx", ".xlsx",
    ".png", ".jpg", ".jpeg", ".webp", ".gif",
}


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip() or "file"


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), _=Depends(require_api_key)):
    """Recebe um arquivo, extrai conteúdo e retorna o attachment_id."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(415, f"Tipo não suportado: {ext}. Aceitos: {sorted(ALLOWED_EXTS)}")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "Arquivo maior que 20MB")

    import uuid
    att_id = str(uuid.uuid4())
    folder = UPLOAD_ROOT / att_id
    folder.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(file.filename or f"file{ext}")
    dest = folder / safe
    dest.write_bytes(data)

    mime = file.content_type or guess_mime(safe)
    kind, text = extract(dest, mime)

    with Session(sync_engine) as s:
        att = Attachment(
            id=att_id,
            filename=safe,
            mime_type=mime,
            size_bytes=len(data),
            kind=kind,
            storage_path=f"{att_id}/{safe}",
            extracted_text=text or None,
        )
        s.add(att)
        s.commit()

    return {
        "id": att_id,
        "filename": safe,
        "mime_type": mime,
        "kind": kind,
        "size_bytes": len(data),
        "url": f"/uploads/{att_id}/{safe}",
        "has_text": bool(text),
        "text_preview": (text[:200] + "…") if text and len(text) > 200 else (text or ""),
    }


@router.get("/{att_id}/{filename}")
async def serve(att_id: str, filename: str):
    """Serve o arquivo bruto (usado para embutir imagens nos slides)."""
    # público para permitir uso em <img> / Marp bg
    path = UPLOAD_ROOT / att_id / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Arquivo não encontrado")
    # proteção contra path traversal
    try:
        path.resolve().relative_to(UPLOAD_ROOT.resolve())
    except ValueError:
        raise HTTPException(400, "Caminho inválido")
    with Session(sync_engine) as s:
        att = s.get(Attachment, att_id)
    mime = att.mime_type if att else guess_mime(filename)
    return FileResponse(str(path), media_type=mime)


@router.delete("/{att_id}")
async def delete(att_id: str, _=Depends(require_api_key)):
    with Session(sync_engine) as s:
        att = s.get(Attachment, att_id)
        if not att:
            raise HTTPException(404, "Não encontrado")
        s.delete(att)
        s.commit()
    folder = UPLOAD_ROOT / att_id
    if folder.exists():
        for f in folder.iterdir():
            f.unlink(missing_ok=True)
        folder.rmdir()
    return {"ok": True}
