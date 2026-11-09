import json
from backend.services.gemini import GeminiService

PROMPT = """Extract only durable, explicitly user-stated, non-sensitive facts.
Never store passwords, API keys, payment data, medical details, or highly sensitive traits.
Return ONLY JSON: {"memories":[{"content":"fact","category":"preference|goal|background|project|other","importance":1}]}
If nothing qualifies return {"memories":[]}.
importance must be an integer 1-5.
Conversation:
"""

def extract_memories(conversation):
    raw = GeminiService().generate(PROMPT + conversation)
    try:
        parsed = json.loads(raw)
        output = []
        for item in parsed.get("memories",[]):
            content = str(item.get("content","")).strip()
            if content:
                output.append({"content":content,"category":str(item.get("category","other"))[:40],
                               "importance":max(1,min(5,int(item.get("importance",3))))})
        return output
    except (json.JSONDecodeError,TypeError,ValueError):
        return []
