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


@dataclass
class PackageCoverage:
    package: str
    percent: float
    has_tests: bool = True


@dataclass
class CoverageReport:
    """ผลลัพธ์จาก `go test -cover ./...`"""
    ran: bool = False
    overall_percent: float = 0.0
    packages: list[PackageCoverage] = field(default_factory=list)
    failed_packages: list[str] = field(default_factory=list)
    exit_code: int = 0
    raw_output: str = ""
    error: str = ""  # set เมื่อ ran=False (เช่น ไม่มี go binary)
