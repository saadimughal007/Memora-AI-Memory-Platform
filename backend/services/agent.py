from backend.services.gemini import GeminiService
from backend.services.memory_extractor import extract_memories
from backend.memory.short_term import load_context, remember_turn
from backend.memory.retrieval import search_memories, index_memory
from backend.memory.long_term import save_memory

SYSTEM = """You are Memora, a helpful assistant with user-controlled memory.
Use supplied history and memories only when relevant. Never claim to remember facts not supplied.
Never reveal secrets or another user's data. Be transparent if context is missing."""

def chat(session_id,user_id,message):
    history = load_context(session_id)
    memories = search_memories(user_id,message)
    history_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history)
    memory_text = "\n".join(f"- {m}" for m in memories) or "(none)"
    prompt = f"{SYSTEM}\n\nRELEVANT SAVED MEMORIES:\n{memory_text}\n\nRECENT CHAT:\n{history_text}\n\nUSER: {message}"
    answer = GeminiService().generate(prompt)
    remember_turn(session_id,user_id,message,answer)

    explicit = any(term in message.lower() for term in
        ("remember that","remember this","please remember","save this memory","yaad rakhna","yaad rakh lo"))
    if explicit:
        for item in extract_memories(f"USER: {message}\nASSISTANT: {answer}"):
            memory_id = save_memory(user_id,item["content"],item["category"],item["importance"])
            index_memory(memory_id,user_id,item["content"])
    return answer,memories
