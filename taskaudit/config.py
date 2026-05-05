# ─────────────────────────────────────────────────────────
# Constants และ shared console instance
# ─────────────────────────────────────────────────────────
from rich.console import Console

# global console instance — ใช้ร่วมกันทุก module
console = Console()

MAX_TOKENS = 4000
MAX_FILE_BYTES = 100 * 1024  # 100 KB - skip ไฟล์ที่ใหญ่กว่านี้

DEFAULT_INCLUDE_DIRS = [
    "internal/handler",
    "internal/service",
    "internal/repository",
    "internal/models",
]

SKIP_DIRS = {"vendor", "node_modules", ".git", "tmp", "dist", "build"}

# Default model per provider
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-flash",
    "openrouter": "anthropic/claude-sonnet-4",
}

# Env var name per provider
API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}
