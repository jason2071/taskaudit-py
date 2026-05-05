# ─────────────────────────────────────────────────────────
# Anthropic provider — import SDK แบบ lazy ตอนเรียกใช้จริง
# ─────────────────────────────────────────────────────────
from . import LLMProvider


class AnthropicProvider(LLMProvider):
    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
