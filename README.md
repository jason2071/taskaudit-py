# taskaudit (Python)

CLI + Web tool audit Go code เทียบกับ checklist ใช้ AI — รองรับหลาย provider, auto-detect stack (ent+atlas / plain), เช็ค test coverage จริงด้วย `go test -cover`

| Provider | Default Model | Env Variable |
|----------|---------------|--------------|
| `anthropic` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| `gemini` | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| `openrouter` | `anthropic/claude-sonnet-4` | `OPENROUTER_API_KEY` |
| `ollama` | `llama3.2` | `OLLAMA_HOST` (default `http://localhost:11434`) |

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
# Anthropic (default) — auto-detect stack
python3 taskaudit.py --task "Audit API" \
  --include "handler,service,repository,model,utils"

# Force stack ent+atlas
python3 taskaudit.py --task "Audit API" --stack ent

# Plain database/sql
python3 taskaudit.py --task "Audit API" --stack plain

# พร้อม test coverage จริง (รัน `go test -cover ./...`)
python3 taskaudit.py --task "Audit API" \
  --coverage --coverage-threshold 85

# OpenAI
python3 taskaudit.py --task "Audit API" \
  --provider openai --model gpt-4o

# พร้อม HTML + Markdown report
python3 taskaudit.py \
  --task "Audit API" \
  --provider openai \
  --include "handler,service,repository,model,utils" \
  --coverage \
  --html ./audit.html \
  --md ./audit.md \
  -v
```

## Stack Support (ent+atlas vs plain)

Tool รองรับ 2 stack สำหรับ Go BE:

| Stack | When | Default checklist |
|-------|------|-------------------|
| `ent` | ent ORM + atlas migration | ent schema, `go generate ./ent`, atlas migrate diff, ent client builder |
| `plain` | `database/sql` / sqlx + manual migration | prepared statement, rows.Close, SQLi guard, `db.BeginTx` |

**Auto-detect priority:**
```
ent/schema/ exists       → ent
atlas.hcl / atlas.sum    → ent
otherwise                → plain
```

Override ด้วย `--stack ent|plain` หรือ `auto` (default).

## Test Coverage

ใช้ flag `--coverage` เพื่อรัน `go test -cover ./...` จริง แล้วรวมผลใน audit. AI จะใช้ % ประกอบการตัดสินสำหรับ checklist หมวด `test`:

```bash
python3 taskaudit.py --task "..." --coverage --coverage-threshold 80
```

Report จะแสดง:
- Overall coverage % (pass/fail vs threshold)
- Per-package coverage (สี: green ≥ threshold, amber ≥ 50, red < 50)
- Packages ที่ไม่มี test (`no test files`)
- Packages ที่ build/test fail

ต้องมี `go` ใน PATH + `go.mod` ใน root. ถ้าไม่มี → skip + warn (ไม่ fail audit)

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
- เลือก provider + model ผ่าน UI (Fetch models จาก API)
- Browse project directory
- **Stack dropdown** — auto-detect เมื่อเลือก dir, override ได้
- **Coverage checkbox** + threshold input — รัน `go test -cover` จริง
- Optional files: custom checklist, requirement context, manual test results
- Template download (per stack: ent+atlas / plain)
- ดู audit results แบบ interactive — coverage panel + per-package table
- Export Markdown report

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--task` | Task title **(required)** | — |
| `--desc` | Task description | — |
| `--provider` | AI provider (`anthropic`, `openai`, `gemini`, `openrouter`, `ollama`) | `anthropic` |
| `--model` | Override default model | per provider |
| `--stack` | `auto`, `ent`, `plain` | `auto` |
| `--dir` | Root directory to scan | `.` |
| `--include` | Comma-separated paths | `internal/handler,service,repository,models` |
| `--checklist` | Custom checklist file | built-in (per stack) |
| `--context` | Context/requirement file (.md/.txt) | — |
| `--no-tests` | Exclude `_test.go` files | `false` |
| `--coverage` | Run `go test -cover ./...` + รวมผลใน audit | `false` |
| `--coverage-threshold` | Threshold % สำหรับ coverage | `80` |
| `--coverage-timeout` | Timeout วินาทีสำหรับ go test | `300` |
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
│   ├── models.py             # dataclasses (AuditResult, CoverageReport, ...)
│   ├── stack.py              # ent vs plain detection + checklist items
│   ├── checklist.py          # load/default checklist (per stack)
│   ├── scanner.py            # scan .go files
│   ├── prompt.py             # build AI prompt (with coverage section)
│   ├── audit.py              # audit_code()
│   ├── coverage.py           # `go test -cover ./...` runner + parser
│   ├── web.py                # FastAPI Web UI (embedded SPA)
│   ├── providers/
│   │   ├── __init__.py       # LLMProvider ABC + factory
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   ├── openrouter.py
│   │   └── ollama.py
│   └── reporters/
│       ├── terminal.py       # rich terminal output (with coverage panel)
│       ├── html.py           # HTML report
│       └── markdown.py       # Markdown report (with coverage section)
└── templates/
    ├── checklist.txt              # generic
    ├── checklist-ent-atlas.txt    # ent + atlas
    ├── checklist-plain.txt        # plain database/sql
    ├── requirement.md
    └── MANUAL_TEST.md
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

ดู template สำเร็จรูปได้ที่ `templates/checklist-ent-atlas.txt` และ `templates/checklist-plain.txt` (Web UI ดาวน์โหลดได้ใน Optional Files modal)

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
