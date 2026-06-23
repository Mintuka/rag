from pathlib import Path

from app.config import settings


async def generate_response(user_message: str, file_context: str = "") -> str:
    context = f"\n\nAttached file context:\n{file_context}" if file_context else ""

    if settings.openai_api_key:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
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
        except Exception:
            pass

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
