# taskaudit (Python)

CLI + Web tool audit Go code เทียบกับ checklist ใช้ AI — รองรับหลาย provider, auto-detect stack (ent+atlas / plain), เช็ค test coverage จริงด้วย `go test -cover`

## Providers

| Provider | Default Model | Env Variable |
|----------|---------------|--------------|
| `anthropic` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| `gemini` | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| `openrouter` | `anthropic/claude-sonnet-4` | `OPENROUTER_API_KEY` |
| `ollama` | `llama3.2` | `OLLAMA_HOST` (default `http://localhost:11434`) |

## Quick start

```bash
# 1. Install
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ใส่ API key

# 2. รัน CLI
python3 taskaudit.py --task "Audit API" --dir /path/to/go-project -v

# 3. หรือเปิด Web UI
python3 taskaudit.py web
```

## Features

- **Multi-provider AI** — Anthropic / OpenAI / Gemini / OpenRouter / Ollama
- **Stack-aware** — auto-detect ent+atlas vs plain `database/sql`, ใช้ checklist + prompt เหมาะสม
- **Test coverage runner** — รัน `go test -cover ./...` จริง, รวม % เข้า audit
- **Web UI** — config form + auto-detect + interactive results + Markdown export
- **Reports** — Terminal (rich), HTML, Markdown, JSON

## Docs

- [Setup](docs/setup.md) — Python install, venv, env config, alias/pipx
- [CLI Usage](docs/cli.md) — examples, options table, project structure
- [Web UI](docs/web-ui.md) — step-by-step คู่มือ + state persistence
- [Features](docs/features.md) — stack support, coverage, custom checklist
