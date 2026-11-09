from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(default="local-user", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=10000)

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    retrieved_memories: list[str] = []

class MemoryCreate(BaseModel):
    user_id: str = "local-user"
    content: str = Field(min_length=3, max_length=2000)
    category: str = "general"
    importance: int = Field(default=3, ge=1, le=5)

class MemoryItem(BaseModel):
    id: int
    user_id: str
    content: str
    category: str
    importance: int
    created_at: str
