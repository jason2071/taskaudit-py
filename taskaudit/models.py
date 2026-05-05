# ─────────────────────────────────────────────────────────
# Data classes — ใน Python ใช้ @dataclass เพื่อสร้าง class ง่ายๆ
# คล้าย struct ใน Go แต่ไม่ต้องเขียน getter/setter
# ─────────────────────────────────────────────────────────
from dataclasses import dataclass, field


@dataclass
class CodeFile:
    path: str
    content: str


@dataclass
class ChecklistItem:
    id: str
    title: str
    category: str = "code"
    done: bool = False


@dataclass
class AuditResult:
    """ผลลัพธ์จาก AI audit"""
    results: list = field(default_factory=list)        # [{stepId, status, evidence}]
    missing_items: list = field(default_factory=list)   # [{title, category, severity, reason}]
    summary: str = ""
