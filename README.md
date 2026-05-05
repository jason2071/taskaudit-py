# taskaudit (Python)

CLI tool audit Go code เทียบกับ checklist ใช้ AI — รองรับหลาย provider

| Provider | Default Model | Env Variable |
|----------|---------------|--------------|
| `anthropic` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| `gemini` | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| `openrouter` | `anthropic/claude-sonnet-4` | `OPENROUTER_API_KEY` |

## Setup

### 1. ลง Python (ถ้ายังไม่มี)

```bash
# Mac
brew install python@3.12

# เช็คว่าได้ 3.10 ขึ้นไป
python3 --version
```

### 2. สร้าง virtual environment

```bash
cd ~/Desktop/work/taskaudit-py

# สร้าง virtual env
python3 -m venv venv

# Activate (ทุกครั้งที่จะใช้)
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### 3. Set API key (เลือกตาม provider ที่ใช้)

**วิธีที่ 1: ใช้ `.env` file (แนะนำ)**

```bash
cp .env.example .env
# แก้ .env ใส่ API key + เลือก provider/model
```

**วิธีที่ 2: export ตรง**

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Gemini
export GEMINI_API_KEY="AI..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
```

> `.env` จะถูกโหลดก่อน — ถ้า export env var ไว้ด้วยจะ override ค่าใน `.env`

### 4. ทดสอบ

```bash
python3 taskaudit.py --help
# หรือ
python3 -m taskaudit --help

# เปิด Web UI
python3 taskaudit.py web
```

## Usage

```bash
# Anthropic (default)
python3 taskaudit.py --task "Audit API" \
  --include "handler,service,repository,model,utils"

# OpenAI
python3 taskaudit.py --task "Audit API" \
  --provider openai --model gpt-4o

# Gemini
python3 taskaudit.py --task "Audit API" \
  --provider gemini

# OpenRouter (เข้าถึง model ต่างๆ ผ่าน endpoint เดียว)
python3 taskaudit.py --task "Audit API" \
  --provider openrouter --model anthropic/claude-sonnet-4

# พร้อม HTML + Markdown report
python3 taskaudit.py \
  --task "Audit API" \
  --provider openai \
  --include "handler,service,repository,model,utils" \
  --html ./audit.html \
  --md ./audit.md \
  -v
```

## Web UI

มี Web UI ใช้ผ่าน browser ได้เลย — ไม่ต้องจำ CLI flags

```bash
# Start Web UI (default port 8080)
python3 taskaudit.py web

# Custom port
python3 taskaudit.py web --port 3000

# หรือรันตรงจาก module
python3 -m taskaudit.web --port 8080
```

เปิด browser ไปที่ `http://localhost:8080` — มี features:
- เลือก provider + model ผ่าน UI
- Browse project directory
- ดู audit results แบบ interactive
- Export Markdown report

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--task` | Task title **(required)** | — |
| `--desc` | Task description | — |
| `--provider` | AI provider (`anthropic`, `openai`, `gemini`, `openrouter`) | `anthropic` |
| `--model` | Override default model | per provider |
| `--dir` | Root directory to scan | `.` |
| `--include` | Comma-separated paths | `internal/handler,service,repository,models` |
| `--checklist` | Custom checklist file | built-in 9 items |
| `--no-tests` | Exclude `_test.go` files | `false` |
| `--html` | Export HTML report path | — |
| `--md` | Export Markdown report path | — |
| `--json` | Output as JSON | `false` |
| `-v` | Verbose output | `false` |

## Project Structure

```
taskaudit-py/
├── taskaudit.py              # entry point (backward compat)
├── requirements.txt
├── taskaudit/
│   ├── __init__.py
│   ├── __main__.py           # python -m taskaudit
│   ├── cli.py                # argparse + main()
│   ├── config.py             # constants
│   ├── models.py             # dataclasses
│   ├── checklist.py          # load/default checklist
│   ├── scanner.py            # scan .go files
│   ├── prompt.py             # build AI prompt
│   ├── audit.py              # audit_code()
│   ├── web.py                # FastAPI Web UI (embedded SPA)
│   ├── providers/
│   │   ├── __init__.py       # LLMProvider ABC + factory
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   └── openrouter.py
│   └── reporters/
│       ├── terminal.py       # rich terminal output
│       ├── html.py           # HTML report
│       └── markdown.py       # Markdown report
```

## Custom Checklist

สร้างไฟล์ format `category: title` ต่อบรรทัด:

```
code: สร้าง model
code: สร้าง repository layer
code: สร้าง service layer พร้อม business logic
code: สร้าง handler + routing
test: เขียน unit test สำหรับ service
docs: Comment สำคัญ
```

```bash
python3 taskaudit.py --task "My API" --checklist ./my-checklist.txt
```

## ทำให้รันเป็น `taskaudit` ตรงๆ

### Shell alias (ง่ายสุด)

```bash
echo 'alias taskaudit="python3 ~/Desktop/work/taskaudit-py/taskaudit.py"' >> ~/.zshrc
source ~/.zshrc
```

### ใช้ pipx (best practice)

```bash
brew install pipx
pipx install ./taskaudit-py  # ต้องสร้าง pyproject.toml ก่อน
```
