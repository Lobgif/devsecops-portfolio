"""Endpoint synchrone de modération (appel direct avant publication)."""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from agoraci.common import limiter

from .moderator import analyze

router = APIRouter(prefix="/api/moderation", tags=["moderation"])


class CheckRequest(BaseModel):
    text: str


@router.post("/check")
@limiter.limit("30/minute")
async def check(request: Request, payload: CheckRequest) -> dict:
    return await analyze(payload.text)
