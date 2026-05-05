# ─────────────────────────────────────────────────────────
# Checklist loading — default + file-based
# ─────────────────────────────────────────────────────────
from typing import Optional

from .models import ChecklistItem


# ─────────────────────────────────────────────────────────
# Default checklist — ถ้า user ไม่ส่ง --checklist มา
# ─────────────────────────────────────────────────────────
def default_checklist() -> list[ChecklistItem]:
    items = [
        ("code", "สร้าง model"),
        ("code", "สร้าง repository layer"),
        ("code", "สร้าง service layer พร้อม business logic"),
        ("code", "สร้าง handler + routing"),
        ("code", "เพิ่ม validation (go-playground/validator)"),
        ("code", "Error handling ครบทุก layer"),
        ("test", "เขียน unit test (table-driven) สำหรับ service"),
        ("test", "Test error cases"),
        ("docs", "Comment สำคัญในที่จำเป็น"),
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
