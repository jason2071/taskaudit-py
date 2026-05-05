# taskaudit (Python)

CLI tool audit Go code เทียบกับ checklist ใช้ Claude API
**Python version** — เขียนสั้นกว่า Go ~3 เท่า, iterate แก้ prompt ง่ายไม่ต้อง build

## Setup

### 1. ลง Python (ถ้ายังไม่มี)

```bash
# Mac
brew install python@3.12

# เช็คว่าได้ 3.10 ขึ้นไป
python3 --version
```

### 2. สร้าง virtual environment (แนะนำ)

```bash
cd ~/Desktop/work/taskaudit-py

# สร้าง virtual env ใน folder venv/
python3 -m venv venv

# Activate (ทุกครั้งที่จะใช้)
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

> 💡 **Virtual env คืออะไร?** เหมือน sandbox แยก library ของแต่ละ project ออกจากกัน
> ป้องกัน version conflict — เช่น project A ใช้ `anthropic 0.40` แต่ project B ใช้ `anthropic 0.50`

### 3. Set API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# ติดถาวร
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
```

### 4. ทดสอบ

```bash
python3 taskaudit.py --help
```

## Usage

```bash
# Quick check
python3 taskaudit.py --task "test" --include "handler,service,repository,model,utils"

# พร้อม HTML + Markdown
python3 taskaudit.py \
  --task "Planogram compare API" \
  --include "handler,service,repository,model,utils" \
  --html ./audit.html \
  --md ./audit.md \
  -v
```

## ทำให้รันเป็น `taskaudit` ตรงๆ ไม่ต้องพิมพ์ `python3 taskaudit.py`

### วิธีที่ 1: Shell alias (ง่ายสุด)

```bash
echo 'alias taskaudit="python3 ~/Desktop/work/taskaudit-py/taskaudit.py"' >> ~/.zshrc
source ~/.zshrc
```

### วิธีที่ 2: ทำเป็น executable

```bash
# 1. ใส่ shebang แล้ว (#!/usr/bin/env python3 บรรทัดแรก) ✓
# 2. ทำให้รันได้
chmod +x taskaudit.py

# 3. Symlink ไป path
ln -s ~/Desktop/work/taskaudit-py/taskaudit.py /usr/local/bin/taskaudit
```

แต่วิธีนี้ต้อง `source venv/bin/activate` ก่อน ไม่งั้นหา library ไม่เจอ

### วิธีที่ 3: ใช้ pipx (best practice)

```bash
brew install pipx
pipx install ./taskaudit-py  # ต้องสร้าง pyproject.toml ก่อน
```

---

## Distribute ให้ทีม

Python distribute ลำบากกว่า Go เพราะต้องลง Python + dependencies เอง — มี 3 ทาง:

### A. แชร์เป็น script + README (ง่ายสุด แต่เพื่อนต้อง setup เอง)

ส่งเป็น zip ทีมก็ทำตาม README setup เอง

### B. Build เป็น standalone binary ด้วย PyInstaller

```bash
pip install pyinstaller
pyinstaller --onefile taskaudit.py
# จะได้ dist/taskaudit รันได้เลย ไม่ต้องลง Python
```

ข้อเสีย: ไฟล์ใหญ่ (30-50MB), ต้อง build แยกแต่ละ OS

### C. Publish เป็น package ใน internal PyPI

ทีม install ด้วย `pip install taskaudit` ดีสุดแต่ setup ยาก

> ⚠️ ถ้าเรื่อง distribute สำคัญสำหรับทีม **Go เหมาะกว่า** เพราะได้ binary ตัวเดียว
> แต่ถ้าใช้คนเดียว Python iterate เร็วกว่ามาก

---

## Concept Python สำคัญที่ใช้ใน code นี้

### 1. f-string

```python
name = "MaCc"
greeting = f"Hello {name}"  # "Hello MaCc"
# Multi-line + แทรก expression ได้
text = f"""
Task: {task.title}
Done: {len([s for s in steps if s.done])}
"""
```

### 2. List comprehension

```python
# Go style
result := []int{}
for _, n := range numbers {
    if n > 0 {
        result = append(result, n * 2)
    }
}

# Python style - บรรทัดเดียว
result = [n * 2 for n in numbers if n > 0]
```

### 3. @dataclass

```python
# แทนที่จะเขียน __init__, __repr__, __eq__ เอง
@dataclass
class User:
    name: str
    age: int = 0  # default value
```

### 4. Context manager (`with`)

```python
# เหมือน defer file.Close() ใน Go
with open("file.txt") as f:
    content = f.read()
# file ปิดอัตโนมัติแม้เกิด exception
```

### 5. Type hints

```python
def get_user(id: str) -> User:  # บอก type ของ args และ return
    ...

def names(users: list[User]) -> list[str]:
    return [u.name for u in users]
```

ทำให้ IDE auto-complete ได้ และ catch bug ก่อนรัน

### 6. Pathlib (modern path handling)

```python
from pathlib import Path

# แทนที่จะใช้ os.path.join, os.path.exists, ...
p = Path("data/file.txt")
p.exists()
p.read_text()
p.write_text("hello")
for f in Path(".").rglob("*.go"):  # recursive glob
    print(f)
```

---

## เปรียบเทียบ Go vs Python (ตัว tool นี้)

| | Go | Python |
|---|---|---|
| Lines of code | ~990 | ~430 |
| External dependencies | 0 (stdlib only) | 3 (anthropic, rich, jinja2) |
| Build needed | ✓ | ✗ |
| Distribute | binary 8MB | ส่ง .py + ทำ setup |
| Iteration speed | ช้า | เร็ว |
| Performance | เร็วมาก | พอใช้ |
| Match กับงาน MaCc | ✓ Go ทุกวัน | สลับ stack |

ทั้งคู่ทำงานได้เหมือนกัน — เลือกตามความชอบและ context การใช้งาน
