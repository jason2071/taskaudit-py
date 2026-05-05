# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CLI + Web tool ที่ scan Go BE codebase แล้ว audit เทียบ checklist ผ่าน LLM. รองรับหลาย AI provider, auto-detect Go stack (ent+atlas vs plain `database/sql`), เช็ค test coverage จริงด้วย `go test -cover`.

## Common commands

```bash
# Activate venv (Windows: .venv\Scripts\activate)
source venv/bin/activate
pip install -r requirements.txt

# CLI audit (auto-detect stack)
python taskaudit.py --task "Audit X" --dir /path/to/go-project -v

# With test coverage runner
python taskaudit.py --task "..." --coverage --coverage-threshold 85

# Force stack
python taskaudit.py --task "..." --stack ent     # ent + atlas
python taskaudit.py --task "..." --stack plain   # database/sql

# Web UI
python taskaudit.py web              # port 8080
python taskaudit.py web --port 3000

# Help / module entry
python taskaudit.py --help
python -m taskaudit --help
```

**No test suite, no linter, no build step.** Pure-Python CLI — change file, re-run.

For ad-hoc verification write a temp script in repo root, run with `python <name>.py`, delete after.

## Architecture

### Pipeline (per audit run)

```
cli.py / web.py
  → detect_stack(dir)         (stack.py)        — ent vs plain
  → load_checklist(path, stack) (checklist.py)  — built-in per stack OR user file
  → scan_files(dir, ...)      (scanner.py)      — walk *.go, skip vendor/node_modules/.git/...
  → run_coverage(dir)         (coverage.py)     — opt-in: `go test -cover ./...` + parse
  → audit_code(...)           (audit.py)
       → build_prompt(...)    (prompt.py)       — task + checklist + code + coverage section
       → provider.complete()  (providers/*)     — anthropic | openai | gemini | openrouter | ollama
       → parse JSON response → AuditResult
  → reporters/{terminal,html,markdown}.py       — render result + coverage panel
```

`audit_code()` expects LLM to return JSON `{results, missingItems, summary}`. Markdown fences stripped before `json.loads()`.

### Provider abstraction

`providers/__init__.py` defines `LLMProvider` ABC with single method `complete(prompt, model, max_tokens) -> str`. `get_provider(name)` is lazy-import factory — adding a provider = new file in `providers/`, register in factory dict, add to `DEFAULT_MODELS` + `API_KEY_ENV` in `config.py`.

`LOCAL_PROVIDERS = {"ollama"}` controls which providers skip API key validation (use host URL instead).

### Stack system

`stack.py` is the source of truth for ent vs plain. `detect_stack()` checks markers in this order:
1. `ent/schema/` directory → `ent`
2. `atlas.hcl` or `atlas.sum` → `ent`
3. otherwise → `plain`

Checklist items live in `stack.py` as tuples, composed via `stack_items(stack)` returning `_BASE_ANALYSIS + _ENT_DB|_PLAIN_DB + _COMMON_CODE + _ENT_TEST|_PLAIN_TEST + _COMMON_TAIL`. Edit checklist content there, not in `checklist.py`.

`templates/checklist-{ent-atlas,plain}.txt` are user-facing copies — keep in sync with `stack.py` items if you change either.

### Coverage runner

`coverage.py` shells out to `go test -cover ./...` in target dir, parses three line patterns (`ok ... coverage: X%`, `? ... [no test files]`, `FAIL ...`). Returns `CoverageReport` with `ran=False + error` if `go` missing or no `go.mod`. Failure to run is **non-fatal** for audit — just warn and continue.

Coverage data flows: `cli.py`/`web.py` → `audit_code()` → `build_prompt()` injects "Test coverage report" section into LLM prompt → reporters render coverage panel.

### Web UI

`web.py` is FastAPI app with embedded SPA (HTML/JS/CSS as Python triple-quoted string `WEB_HTML`). All UI changes are string edits inside that file.

Endpoints:
- `GET /api/defaults` — providers, default models, env var names, stacks
- `GET /api/detect-stack?path=` — stack auto-detection on directory selection
- `GET /api/browse?path=` — directory listing for file picker
- `POST /api/models` — fetch live model list from provider (uses user's API key)
- `POST /api/audit` — main audit endpoint; mirrors CLI but returns JSON for SPA to render
- `GET /api/template/{name}` — whitelisted template downloads (add to `allowed` set in handler when shipping new template)

Per-request env var swap via `temp_env()` context manager — keeps API keys out of process env after request finishes.

SPA persists settings (provider, dir, include paths, coverage opts, stack) in `localStorage`; API keys in `sessionStorage` (cleared on tab close).

### Config conventions

- `taskaudit/config.py` — single source of truth for `DEFAULT_MODELS`, `API_KEY_ENV`, `MAX_TOKENS=4000`, `MAX_FILE_BYTES=100KB`, `SKIP_DIRS`, `DEFAULT_INCLUDE_DIRS`. `.env` loaded from project root + cwd.
- Comments in this codebase are mostly **Thai** with section dividers (`# ──...──`). Prompts and user-facing strings in reporters/templates are Thai. Keep that style when editing — code reviewers expect it.
- `ChecklistItem.id` follows `step-N` convention; `audit.py` and reporters look up by `stepId` to map LLM result back to title/category.
