import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

_client = None


def get_openai_client() -> Optional[OpenAI]:
    global _client
    if not OPENAI_API_KEY:
        return None
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


async def chat_complete(
    messages: list,
    model: str = "gpt-5.4-mini-2026-03-17",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    client = get_openai_client()
    if not client:
        raise Exception("OPENAI_API_KEY not configured")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
