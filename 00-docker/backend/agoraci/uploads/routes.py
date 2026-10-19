"""Upload d'images publiques (avatars, images de posts) vers MinIO."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from agoraci.common.auth_deps import CurrentUser, get_current_user
from agoraci.common.storage import upload_public

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}
MAX_BYTES = 5 * 1024 * 1024  # 5 Mo


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    prefix: str = Form("uploads"),
    _: CurrentUser = Depends(get_current_user),
):
    ext = ALLOWED.get(file.content_type or "")
    if not ext:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Format non supporté (png, jpg, webp, gif).")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image trop lourde (max 5 Mo).")
    folder = "avatars" if prefix == "avatars" else "uploads"
    url = await run_in_threadpool(
        upload_public, data, prefix=folder, ext=ext, content_type=file.content_type
    )
    return {"url": url}
