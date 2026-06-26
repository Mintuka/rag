import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import UploadedFile, User
from app.schemas import FileResponse
from app.services.rag_pipeline import ingest_and_save, is_rag_supported

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = upload_dir / stored_name
    with open(file_path, "wb") as f:
        f.write(content)

    uploaded = UploadedFile(
        user_id=current_user.id,
        conversation_id=conversation_id,
        filename=stored_name,
        original_name=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
    )
    db.add(uploaded)
    await db.commit()
    await db.refresh(uploaded)

    if settings.openai_api_key and is_rag_supported(file.filename):
        await asyncio.to_thread(ingest_and_save, file_path, uploaded.id)

    return FileResponse.model_validate(uploaded)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    result = await db.execute(
        select(UploadedFile).where(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
    )
    uploaded = result.scalar_one_or_none()
    if uploaded is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse.model_validate(uploaded)
