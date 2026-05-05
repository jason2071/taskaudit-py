# ─────────────────────────────────────────────────────────
# Prompt builder — สร้าง prompt ส่งให้ AI
# ─────────────────────────────────────────────────────────
from .models import ChecklistItem, CodeFile


def build_prompt(
    task: str,
    desc: str,
    checklist: list[ChecklistItem],
    files: list[CodeFile],
    context: str = "",
) -> str:
    """สร้าง prompt — ใช้ f-string ของ Python ทำให้อ่านง่าย"""

    # สร้าง checklist text
    # \n.join() เร็วกว่าการ += string ในลูป (เหมือน strings.Builder ใน Go)
    checklist_text = "\n".join(
        f"{item.id}: [{'✓' if item.done else ' '}] {item.title} ({item.category})"
        for item in checklist
    )

    # สร้าง code text
    code_text = "\n\n".join(
        f"--- FILE: {f.path} ---\n{f.content}"
        for f in files
    )

    # Context section (requirement/spec document)
    context_section = ""
    if context:
        context_section = f"""
Requirement/Context document:
{context}
"""

    # f-string + triple quote = multi-line string ที่แทรก variable ได้
    return f"""คุณเป็น senior Go/Fiber code reviewer ตรวจ code ของ developer คนนี้แล้วเทียบกับ checklist ของงาน

งาน: {task}
รายละเอียด: {desc or '(ไม่ระบุ)'}
{context_section}

Checklist ทั้งหมด:
{checklist_text}

Code ที่ scan มาจาก project:
{code_text}

ตรวจสอบทุก step ใน checklist แล้วบอกว่าใน code ทำหรือยัง:
- "done": ทำแล้วจริงใน code
- "missing": ยังไม่เห็นใน code (ขาด)
- "partial": ทำแล้วแต่ไม่สมบูรณ์
- "not_applicable": step ที่ไม่เกี่ยวกับ code

ตอบ JSON เท่านั้น ไม่มี markdown:
{{
  "results": [
    {{"stepId": "id", "status": "done|missing|partial|not_applicable", "evidence": "หลักฐานใน code (ภาษาไทย สั้นๆ)"}}
  ],
  "missingItems": [
    {{"title": "สิ่งที่ขาด", "category": "code|test|docs", "severity": "high|medium|low", "reason": "เหตุผล"}}
  ],
  "summary": "สรุป 2-3 ประโยค ภาษาไทย"
}}"""
