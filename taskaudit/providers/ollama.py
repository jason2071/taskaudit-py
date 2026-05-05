# ─────────────────────────────────────────────────────────
# Ollama provider — local LLM, OpenAI-compatible endpoint
# ─────────────────────────────────────────────────────────
import os

from . import LLMProvider


def _normalize_host(host: str) -> str:
    """Strip trailing slash + ensure scheme"""
    host = host.strip().rstrip("/")
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host


class OllamaProvider(LLMProvider):
    """Ollama local server. Reads OLLAMA_HOST env (default http://localhost:11434)."""

    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        from openai import OpenAI
        host = _normalize_host(os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
        client = OpenAI(
            base_url=f"{host}/v1",
            api_key="ollama",  # required by SDK but Ollama ignores it
        )
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
