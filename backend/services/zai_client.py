import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from zai import ZaiClient

ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")

_client = None


def get_zai_client() -> Optional[ZaiClient]:
    global _client
    if not ZAI_API_KEY:
        return None
    if _client is None:
        _client = ZaiClient(api_key=ZAI_API_KEY)
    return _client


async def chat_complete(
    messages: list,
    model: str = "glm-4",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    client = get_zai_client()
    if not client:
        raise Exception("ZAI_API_KEY not configured")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content