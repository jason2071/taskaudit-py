# ─────────────────────────────────────────────────────────
# Checklist loading — default + file-based
# ─────────────────────────────────────────────────────────
from typing import Optional

from .models import ChecklistItem
from .stack import Stack, stack_items


# ─────────────────────────────────────────────────────────
# Default checklist — ถ้า user ไม่ส่ง --checklist มา
# ─────────────────────────────────────────────────────────
def default_checklist(stack: Stack = "plain") -> list[ChecklistItem]:
    """Default checklist สำหรับ BE Go developer ตาม stack (ent หรือ plain)"""
    items = stack_items(stack)
    return [
        ChecklistItem(id=f"step-{i+1}", category=cat, title=title)
        for i, (cat, title) in enumerate(items)
    ]


def load_checklist(path: Optional[str], stack: Stack = "plain") -> list[ChecklistItem]:
    """โหลด checklist จาก file format: 'category: title' ต่อบรรทัด"""
    if not path:
        return default_checklist(stack)

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
