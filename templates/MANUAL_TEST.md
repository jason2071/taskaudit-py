# Manual API Test — taskaudit Web

Manual test ทุก endpoint ของ `taskaudit web` server. กรอก actual response + ผล Pass/Fail หลังรัน

---

## Setup

```bash
# Start server
python taskaudit.py web --port 8080

# Base URL
BASE_URL=http://localhost:8080
```

**Tester:** _______________
**Date:** YYYY-MM-DD
**Branch / Commit:** _______________
**Server version:** _______________

---

## Endpoint Summary

| # | Method | Path | Purpose | Status |
|---|--------|------|---------|--------|
| 1 | GET  | `/` | Serve SPA | ☐ Pass ☐ Fail |
| 2 | GET  | `/api/defaults` | Default config | ☐ Pass ☐ Fail |
| 3 | GET  | `/api/template/{name}` | Download template | ☐ Pass ☐ Fail |
| 4 | GET  | `/api/browse` | Directory listing | ☐ Pass ☐ Fail |
| 5 | POST | `/api/models` | List provider models | ☐ Pass ☐ Fail |
| 6 | POST | `/api/audit` | Run audit (core) | ☐ Pass ☐ Fail |

---

## 1. `GET /` — Serve SPA

### Request

```bash
curl -i http://localhost:8080/
```

### Expected

- Status: `200 OK`
- Content-Type: `text/html; charset=utf-8`
- Body contains `<title>taskaudit — Web UI</title>`

### Actual

```
<paste status line + relevant headers + first 5 lines of body>
```

**Result:** ☐ Pass ☐ Fail
**Notes:** _______________

---

## 2. `GET /api/defaults` — Default Config

### Request

```bash
curl -s http://localhost:8080/api/defaults | jq .
```

### Expected

```json
{
  "providers": ["anthropic", "openai", "gemini", "openrouter"],
  "default_models": { "anthropic": "...", "openai": "...", "gemini": "...", "openrouter": "..." },
  "default_include_paths": "internal/handler,internal/service,...",
  "api_key_env": { "anthropic": "ANTHROPIC_API_KEY", "...": "..." }
}
```

### Actual

```json
<paste response>
```

**Result:** ☐ Pass ☐ Fail
**Notes:** _______________

---

## 3. `GET /api/template/{name}` — Download Template

### 3.1 Valid: `checklist.txt`

```bash
curl -s http://localhost:8080/api/template/checklist.txt | jq .
```

**Expected:** `200`, JSON `{ "filename": "checklist.txt", "content": "<file text>" }`

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 3.2 Valid: `requirement.md`

```bash
curl -s http://localhost:8080/api/template/requirement.md | jq .
```

**Expected:** `200`, JSON with non-empty `content`

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 3.3 Invalid name (not in allowlist)

```bash
curl -i http://localhost:8080/api/template/secret.txt
```

**Expected:** `404`, body `{"detail":"Template not found: secret.txt"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

---

## 4. `GET /api/browse` — Directory Listing

### 4.1 Default path (`~`)

```bash
curl -s "http://localhost:8080/api/browse" | jq .
```

**Expected:** `200`, JSON with `current`, `parent`, `entries[]` (each `{name, path, is_dir}`)

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 4.2 Specific path

```bash
curl -s "http://localhost:8080/api/browse?path=C:/Users/Mac/Works" | jq .
```

**Expected:** `200`, listing of given dir

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 4.3 Hidden + skip dirs filtered

**Verify:** entries do NOT include `.git`, `node_modules`, `vendor`, `dist`, `build`, `__pycache__`, dot-files

**Actual:** ☐ Confirmed ☐ Found leak: _______________

**Result:** ☐ Pass ☐ Fail

### 4.4 Path not found

```bash
curl -i "http://localhost:8080/api/browse?path=/no/such/path"
```

**Expected:** `404`, `{"detail":"Path not found: ..."}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 4.5 Path is file not dir

```bash
curl -i "http://localhost:8080/api/browse?path=C:/Users/Mac/Works/taskaudit-py/README.md"
```

**Expected:** `400`, `{"detail":"Path is not a directory"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

---

## 5. `POST /api/models` — List Provider Models

### 5.1 Anthropic (hardcoded list)

```bash
curl -s -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":"sk-ant-..."}'
```

**Expected:** `200`, `{"models":["claude-sonnet-4-...","claude-opus-4-...","claude-haiku-4-..."]}`

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 5.2 OpenAI (live fetch)

```bash
curl -s -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"sk-..."}'
```

**Expected:** `200`, sorted list of GPT/o-series models

**Actual:**

```json
<paste first 5 entries>
```

**Result:** ☐ Pass ☐ Fail

### 5.3 Gemini (live fetch)

```bash
curl -s -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"gemini","api_key":"AIza..."}'
```

**Expected:** `200`, sorted list with `generateContent` support

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 5.4 OpenRouter (live fetch)

```bash
curl -s -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"openrouter","api_key":"sk-or-..."}'
```

**Expected:** `200`, sorted list

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 5.5 Empty API key

```bash
curl -i -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":""}'
```

**Expected:** `400`, `{"detail":"API key is required"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 5.6 Unknown provider

```bash
curl -i -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"xai","api_key":"x"}'
```

**Expected:** `400`, `{"detail":"Unknown provider: xai"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 5.7 Invalid API key

```bash
curl -i -X POST http://localhost:8080/api/models \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"sk-invalid"}'
```

**Expected:** `400`, `{"detail":"Failed to fetch models: ..."}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

---

## 6. `POST /api/audit` — Run Audit

### 6.1 Happy path

```bash
curl -s -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "provider":"anthropic",
    "api_key":"sk-ant-...",
    "model":"",
    "task":"Test task",
    "desc":"Manual test run",
    "project_dir":"C:/path/to/go/project",
    "include_paths":"internal/handler,internal/service",
    "no_tests":false,
    "checklist_path":null,
    "context_path":null
  }' | jq .
```

**Expected:** `200`, JSON `{task, desc, model, provider, files_scanned, total_steps, done_pct, counts, items[], missing_items[], summary}`

**Actual:**

```json
<paste — counts + total_steps + summary at minimum>
```

**Result:** ☐ Pass ☐ Fail

### 6.2 With checklist + context file

```bash
curl -s -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "provider":"anthropic",
    "api_key":"sk-ant-...",
    "task":"Test",
    "project_dir":"C:/path/to/go/project",
    "checklist_path":"C:/path/to/checklist.txt",
    "context_path":"C:/path/to/requirement.md"
  }' | jq .
```

**Expected:** `200`, items reflect custom checklist

**Actual:**

```json
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 6.3 Missing task

```bash
curl -i -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":"sk-ant-...","task":"","project_dir":"C:/path"}'
```

**Expected:** `400`, `{"detail":"Task name is required"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 6.4 Unknown provider

```bash
curl -i -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider":"xai","api_key":"x","task":"T","project_dir":"C:/path"}'
```

**Expected:** `400`, `{"detail":"Unknown provider: xai"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 6.5 Project dir not found

```bash
curl -i -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":"sk-ant-...","task":"T","project_dir":"/no/such"}'
```

**Expected:** `400`, `{"detail":"Project directory not found: ..."}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 6.6 No API key + no env var

```bash
unset ANTHROPIC_API_KEY  # PowerShell: Remove-Item Env:ANTHROPIC_API_KEY
curl -i -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":"","task":"T","project_dir":"C:/path/to/go/project"}'
```

**Expected:** `400`, `{"detail":"API key is required — either enter in form or export ANTHROPIC_API_KEY"}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 6.7 No `.go` files in project

```bash
curl -i -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":"sk-ant-...","task":"T","project_dir":"C:/empty/dir"}'
```

**Expected:** `400`, `{"detail":"No .go files found in ..."}`

**Actual:**

```
<paste>
```

**Result:** ☐ Pass ☐ Fail

### 6.8 Env var fallback (no api_key in body)

```bash
$env:ANTHROPIC_API_KEY="sk-ant-..."   # PowerShell
curl -s -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","api_key":"","task":"T","project_dir":"C:/path/to/go/project"}' | jq .
```

**Expected:** `200`, runs successfully using env var

**Actual:**

```json
<paste counts>
```

**Result:** ☐ Pass ☐ Fail

---

## Postman

Import same requests into Postman:

1. New Collection: `taskaudit`
2. Variable: `base_url = http://localhost:8080`
3. Add 6 folders (one per endpoint), one request per test case above
4. Export collection: `Collection > ... > Export > v2.1` → save as `postman/taskaudit.postman_collection.json`

---

## Sign-off

- [ ] All endpoints tested
- [ ] All Pass/Fail filled
- [ ] Failed cases logged as issues
- [ ] Screenshots/logs attached for failures

**Tested by:** _______________ **Date:** _______________
**Reviewed by:** _______________ **Date:** _______________
