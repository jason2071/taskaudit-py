# ─────────────────────────────────────────────────────────
# Constants และ shared console instance
# ─────────────────────────────────────────────────────────
import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

# Load .env file — ค้นหาจาก cwd ขึ้นไป หรือจาก project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()  # fallback: cwd/.env

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

# Default model per provider (สามารถ override ผ่าน .env ได้)
DEFAULT_MODELS = {
    "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o"),
    "gemini": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "openrouter": os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4"),
}

# Default provider (override ผ่าน .env)
DEFAULT_PROVIDER = os.getenv("TASKAUDIT_PROVIDER", "anthropic")

# Env var name per provider
API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}
