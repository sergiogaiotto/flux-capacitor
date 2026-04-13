"""Rotas de gestão dos system prompts."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.api.deps import require_api_key
from app.core import prompts as reg

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptUpdate(BaseModel):
    content: str = Field(..., min_length=10)


@router.get("")
async def list_all(_=Depends(require_api_key)):
    return reg.list_prompts()


@router.get("/{key}")
async def get_one(key: str, _=Depends(require_api_key)):
    items = {p["key"]: p for p in reg.list_prompts()}
    if key not in items:
        raise HTTPException(404, "Prompt desconhecido")
    return items[key]


@router.patch("/{key}")
async def update(key: str, payload: PromptUpdate, _=Depends(require_api_key)):
    try:
        reg.set_prompt(key, payload.content)
    except KeyError:
        raise HTTPException(404, "Prompt desconhecido")
    return {"ok": True, "key": key}


@router.post("/{key}/reset")
async def reset(key: str, _=Depends(require_api_key)):
    try:
        content = reg.reset_prompt(key)
    except KeyError:
        raise HTTPException(404, "Prompt desconhecido")
    return {"ok": True, "key": key, "content": content}
