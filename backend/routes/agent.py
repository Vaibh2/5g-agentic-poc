from fastapi import APIRouter
from pydantic import BaseModel
from services.chat_service import ChatService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    return await ChatService.handle_message(request.message)


@router.get("/chat/memory")
def get_memory():
    return ChatService.get_memory()


@router.post("/chat/clear")
def clear_memory():
    return ChatService.clear_memory()
