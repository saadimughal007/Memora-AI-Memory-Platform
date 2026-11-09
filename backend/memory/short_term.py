from backend.core.config import settings
from backend.database.db import add_message, get_recent_messages, clear_session

def remember_turn(session_id, user_id, user_text, assistant_text):
    add_message(session_id,user_id,"user",user_text)
    add_message(session_id,user_id,"assistant",assistant_text)

def load_context(session_id):
    return get_recent_messages(session_id,settings.max_conversation_messages)

def reset_conversation(session_id):
    clear_session(session_id)
