from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest,ChatResponse,MemoryCreate,MemoryItem
from backend.services.agent import chat
from backend.memory.long_term import save_memory,get_user_memories,remove_memory,remove_all_memories
from backend.memory.retrieval import index_memory,search_memories,remove_index_entry,remove_user_index
from backend.memory.short_term import reset_conversation

router = APIRouter()

@router.post("/chat",response_model=ChatResponse)
def chat_route(payload: ChatRequest):
    try:
        answer,used = chat(payload.session_id,payload.user_id,payload.message)
        return ChatResponse(session_id=payload.session_id,answer=answer,retrieved_memories=used)
    except Exception as exc:
        raise HTTPException(status_code=500,detail=str(exc)) from exc

@router.post("/memories",response_model=MemoryItem)
def create_memory(payload: MemoryCreate):
    memory_id = save_memory(payload.user_id,payload.content,payload.category,payload.importance)
    index_memory(memory_id,payload.user_id,payload.content)
    return next(item for item in get_user_memories(payload.user_id) if item["id"] == memory_id)

@router.get("/memories",response_model=list[MemoryItem])
def list_memory(user_id: str = "local-user"):
    return get_user_memories(user_id)

@router.get("/memories/search")
def search_memory(query: str,user_id: str = "local-user",limit: int = 5):
    return {"results":search_memories(user_id,query,max(1,min(limit,20)))}

@router.delete("/memories/{memory_id}")
def delete_one(memory_id: int,user_id: str = "local-user"):
    deleted = remove_memory(memory_id,user_id)
    if deleted:
        remove_index_entry(memory_id)
    return {"deleted":deleted}

@router.delete("/memories")
def delete_all(user_id: str = "local-user"):
    remove_user_index(user_id)
    return {"deleted_count":remove_all_memories(user_id)}

@router.delete("/sessions/{session_id}")
def clear_session(session_id: str):
    reset_conversation(session_id)
    return {"session_cleared":True}
