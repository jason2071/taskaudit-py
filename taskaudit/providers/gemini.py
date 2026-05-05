# ─────────────────────────────────────────────────────────
# Gemini provider — import SDK แบบ lazy ตอนเรียกใช้จริง
# ─────────────────────────────────────────────────────────
import os

from . import LLMProvider


class GeminiProvider(LLMProvider):
    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text or ""
