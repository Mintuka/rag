import asyncio
import logging
import uuid
from pathlib import Path

from app.config import settings
from app.services.rag_pipeline import (
    is_rag_supported,
    load_or_ingest_index,
    merge_indices,
    rag_query,
)

logger = logging.getLogger(__name__)


async def generate_response(user_message: str, file_context: str = "") -> str:
    context = f"\n\nAttached file context:\n{file_context}" if file_context else ""

    if settings.openai_api_key:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. Be concise and helpful.",
                    },
                    {"role": "user", "content": user_message + context},
                ],
            )
            return response.choices[0].message.content or "I couldn't generate a response."
        except Exception as exc:
            logger.exception("OpenAI API call failed")
            return f"Sorry, I couldn't reach the AI service: {exc}"

    preview = file_context[:200] + "..." if len(file_context) > 200 else file_context
    file_note = f"\n\nI received your file with content preview:\n{preview}" if preview else ""
    return (
        f"I received your message: \"{user_message}\".{file_note}\n\n"
        "This is a demo response. Set OPENAI_API_KEY in your environment for real AI responses."
    )


def read_text_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")[:4000]
    except Exception:
        return "[Binary or unreadable file]"


async def generate_response_with_files(
    user_message: str,
    files: list[tuple[uuid.UUID, Path, str]],
) -> str:
    """
    Answer using RAG when indexed files are attached; fall back to prompt stuffing.
    files: list of (file_id, disk_path, original_name)
    """
    if settings.openai_api_key and files:
        indices = []
        for file_id, file_path, original_name in files:
            if not file_path.exists():
                continue
            if is_rag_supported(original_name):
                index = await asyncio.to_thread(load_or_ingest_index, file_path, file_id)
                if index and index.chunks:
                    indices.append(index)

        if indices:
            merged = merge_indices(indices)
            return await asyncio.to_thread(rag_query, merged, user_message)

    file_context = ""
    for _, file_path, original_name in files:
        if file_path.exists():
            file_context += f"\n--- {original_name} ---\n{read_text_file(file_path)}"

    return await generate_response(user_message, file_context)
