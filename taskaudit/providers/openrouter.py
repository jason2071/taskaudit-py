# ─────────────────────────────────────────────────────────
# OpenRouter provider — ใช้ OpenAI-compatible API
# import SDK แบบ lazy ตอนเรียกใช้จริง
# ─────────────────────────────────────────────────────────
import os

from . import LLMProvider


class OpenRouterProvider(LLMProvider):
    """OpenRouter ใช้ OpenAI-compatible API"""

    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
