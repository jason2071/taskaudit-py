# ─────────────────────────────────────────────────────────
# Gemini provider — import SDK แบบ lazy ตอนเรียกใช้จริง
# ─────────────────────────────────────────────────────────
import os

from . import LLMProvider


class GeminiProvider(LLMProvider):
    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text or ""
