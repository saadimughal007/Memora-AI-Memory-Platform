from backend.database.db import create_memory, list_memories, delete_memory, delete_all_memories

def save_memory(user_id, content, category="general", importance=3):
    return create_memory(user_id,content,category,importance)

def get_user_memories(user_id):
    return list_memories(user_id)

def remove_memory(memory_id,user_id):
    return delete_memory(memory_id,user_id)

def remove_all_memories(user_id):
    return delete_all_memories(user_id)
