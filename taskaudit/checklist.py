# ─────────────────────────────────────────────────────────
# Checklist loading — default + file-based
# ─────────────────────────────────────────────────────────
from typing import Optional

from .models import ChecklistItem


# ─────────────────────────────────────────────────────────
# Default checklist — ถ้า user ไม่ส่ง --checklist มา
# ─────────────────────────────────────────────────────────
def default_checklist() -> list[ChecklistItem]:
    """Default checklist สำหรับ BE Go developer - ครอบคลุมตั้งแต่ analysis ถึง QA handoff"""
    items = [
        # === ANALYSIS ===
        ("analysis", "เข้าใจ requirement + ระบุ scope ที่กระทบ"),
        ("analysis", "identify edge cases และ error scenarios"),
        # === DATABASE ===
        ("code", "migration up + down (rollback ได้จริง)"),
        ("code", "constraints + index ตามที่ query ใช้"),
        # === CODE ===
        ("code", "model + DTO แยกจากกัน, tags ครบ"),
        ("code", "repository ใช้ context.Context + prepared statement"),
        ("code", "transaction handling สำหรับ multi-statement"),
        ("code", "business logic อยู่ที่ service ไม่รั่วไป handler/repo"),
        ("code", "validation (validator + i18n)"),
        ("code", "error wrapping + map เป็น HTTP status ที่ถูก"),
        ("code", "register route ใน main.go"),
        # === TEST ===
        ("test", "unit test service (table-driven, happy + error)"),
        ("test", "manual test ทุก endpoint (Postman/curl)"),
        # === DOCS ===
        ("docs", "API Spec + DB Diagram อัปเดต"),
        # === REVIEW ===
        ("review", "self review + lint/gofmt pass"),
        ("review", "cleanup debug print, commented code")
    ]
    # List comprehension — สร้าง list จากการ loop สั้นๆ ใน 1 บรรทัด
    return [
        ChecklistItem(id=f"step-{i+1}", category=cat, title=title)
        for i, (cat, title) in enumerate(items)
    ]


def load_checklist(path: Optional[str]) -> list[ChecklistItem]:
    """โหลด checklist จาก file format: 'category: title' ต่อบรรทัด"""
    if not path:
        return default_checklist()

    items = []
    # `with open(...)` = context manager จะ close file ให้อัตโนมัติ (เหมือน defer ใน Go)
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            # Skip บรรทัดว่างและ comment
            if not line or line.startswith("#"):
                continue

            # split(":", 1) แยกแค่ครั้งแรก เผื่อ title มี ":" ข้างใน
            parts = line.split(":", 1)
            if len(parts) == 2:
                category = parts[0].strip()
                title = parts[1].strip()
            else:
                category = "code"
                title = line

            items.append(ChecklistItem(
                id=f"step-{i+1}",
                category=category,
                title=title,
            ))
    return items
