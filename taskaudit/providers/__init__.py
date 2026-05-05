# ─────────────────────────────────────────────────────────
# LLM Provider abstraction + factory
# ─────────────────────────────────────────────────────────
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface สำหรับ AI provider ทุกตัว"""

    @abstractmethod
    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        """ส่ง prompt แล้วได้ text response กลับมา"""
        ...


def get_provider(name: str) -> LLMProvider:
    """Factory function สร้าง provider จากชื่อ"""
    # import แบบ lazy ภายใน function เพื่อไม่บังคับติดตั้งทุก SDK ตอน import package
    from .anthropic import AnthropicProvider
    from .openai import OpenAIProvider
    from .gemini import GeminiProvider
    from .openrouter import OpenRouterProvider

    providers: dict[str, type[LLMProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "openrouter": OpenRouterProvider,
    }
    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Choose from: {', '.join(providers)}")
    return providers[name]()
