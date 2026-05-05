# CLI Usage

## Examples

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

## Options

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
