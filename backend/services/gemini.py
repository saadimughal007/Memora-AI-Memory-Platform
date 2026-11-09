from google import genai
from google.genai import types
from backend.core.config import settings

class GeminiService:
    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing. Add your key to the root .env file.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def generate(self,prompt):
        response = self.client.models.generate_content(
            model=self.model, contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4))
        return (response.text or "").strip()
