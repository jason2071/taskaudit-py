# ─────────────────────────────────────────────────────────
# OpenAI provider — import SDK แบบ lazy ตอนเรียกใช้จริง
# ─────────────────────────────────────────────────────────
from . import LLMProvider


class OpenAIProvider(LLMProvider):
    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
