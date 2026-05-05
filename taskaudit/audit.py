# ─────────────────────────────────────────────────────────
# Core audit function — เรียก AI provider แล้วแปลง response
# ─────────────────────────────────────────────────────────
import json
from typing import Optional

from .config import MAX_TOKENS
from .models import AuditResult, ChecklistItem, CodeFile, CoverageReport
from .prompt import build_prompt
from .providers import LLMProvider


def audit_code(
    task: str,
    desc: str,
    checklist: list[ChecklistItem],
    files: list[CodeFile],
    provider: LLMProvider,
    model: str,
    context: str = "",
    coverage: Optional[CoverageReport] = None,
    coverage_threshold: float = 80.0,
) -> AuditResult:
    """เรียก AI provider เพื่อ audit code"""

    prompt = build_prompt(task, desc, checklist, files, context, coverage, coverage_threshold)

    text = provider.complete(prompt, model, MAX_TOKENS)

    # ตัด markdown code fences ออก (เผื่อ AI ใส่มา)
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    data = json.loads(text)

    return AuditResult(
        results=data.get("results", []),
        missing_items=data.get("missingItems", []),
        summary=data.get("summary", ""),
    )
