#!/usr/bin/env python3
"""
taskaudit Web UI — FastAPI + embedded SPA
เปิด browser แล้วใช้งาน audit ผ่าน web ได้เลย

Usage:
    python -m taskaudit.web              # port 8080
    python -m taskaudit.web --port 3000  # custom port
    python taskaudit.py web              # ผ่าน CLI
"""

# ─────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────
import argparse
import os
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .audit import audit_code
from .checklist import load_checklist
from .config import API_KEY_ENV, DEFAULT_INCLUDE_DIRS, DEFAULT_MODELS
from .providers import get_provider
from .scanner import scan_files

# ─────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────
app = FastAPI(title="taskaudit", docs_url=None, redoc_url=None)


# ─────────────────────────────────────────────────────────
# Pydantic models สำหรับ request/response
# ─────────────────────────────────────────────────────────
class AuditRequest(BaseModel):
    provider: str
    api_key: str = ""  # ถ้าว่าง จะใช้ env var ที่ export ไว้
    model: str = ""
    task: str
    desc: str = ""
    project_dir: str
    include_paths: str = ",".join(DEFAULT_INCLUDE_DIRS)
    no_tests: bool = False
    checklist_path: str | None = None


# ─────────────────────────────────────────────────────────
# Context manager — set env var ชั่วคราวสำหรับ request นั้น
# ─────────────────────────────────────────────────────────
@contextmanager
def temp_env(key: str, value: str):
    """Set env var ชั่วคราว แล้วคืนค่าเดิมเมื่อเสร็จ"""
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


# ─────────────────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index():
    """Serve embedded SPA"""
    return HTMLResponse(content=WEB_HTML)


@app.get("/api/defaults")
def get_defaults():
    """Return default config สำหรับ frontend"""
    return {
        "providers": list(DEFAULT_MODELS.keys()),
        "default_models": DEFAULT_MODELS,
        "default_include_paths": ",".join(DEFAULT_INCLUDE_DIRS),
        "api_key_env": API_KEY_ENV,
    }


@app.get("/api/browse")
def browse_directory(path: str = "~"):
    """List directories/files สำหรับ file browser"""
    target = Path(path).expanduser().resolve()

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {target}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries = []
    try:
        for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            # Skip hidden + skip dirs
            if item.name.startswith("."):
                continue
            if item.name in {"vendor", "node_modules", "dist", "build", "__pycache__", ".git"}:
                continue
            entries.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
            })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        "current": str(target),
        "parent": str(target.parent) if target.parent != target else None,
        "entries": entries,
    }


# ─────────────────────────────────────────────────────────
# Anthropic ไม่มี list models API — hardcode common models
# ─────────────────────────────────────────────────────────
ANTHROPIC_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    "claude-haiku-4-20250506",
]


class ModelsRequest(BaseModel):
    provider: str
    api_key: str


@app.post("/api/models")
def list_models(req: ModelsRequest):
    """Fetch available models from provider using API key"""
    if not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")

    provider = req.provider
    api_key = req.api_key.strip()

    try:
        if provider == "anthropic":
            # Anthropic ไม่มี list models API
            return {"models": ANTHROPIC_MODELS}

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.models.list()
            # Filter เฉพาะ GPT models ที่ใช้งานได้กับ chat
            models = sorted([
                m.id for m in response.data
                if any(x in m.id for x in ("gpt-4", "gpt-3.5", "o1", "o3", "o4"))
            ])
            return {"models": models}

        elif provider == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.list()
            models = []
            for m in response:
                name = getattr(m, "name", None) or ""
                methods = getattr(m, "supported_generation_methods", None) or []
                if "generateContent" in methods and name:
                    models.append(name.removeprefix("models/"))
            return {"models": sorted(models)}

        elif provider == "openrouter":
            import urllib.request
            import json as json_mod
            req_http = urllib.request.Request(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            with urllib.request.urlopen(req_http, timeout=10) as resp:
                data = json_mod.loads(resp.read())
            models = sorted([m["id"] for m in data.get("data", [])])
            return {"models": models}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch models: {e}")


@app.post("/api/audit")
def run_audit(req: AuditRequest):
    """Run audit — core endpoint"""
    # Validate provider
    if req.provider not in API_KEY_ENV:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")

    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task name is required")

    project_dir = Path(req.project_dir).expanduser().resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Project directory not found: {req.project_dir}")

    # ใช้ API key จาก request ถ้ามี ไม่งั้น fallback ไป env var ที่ export ไว้
    env_var = API_KEY_ENV[req.provider]
    api_key = req.api_key.strip() or os.environ.get(env_var, "")
    if not api_key:
        raise HTTPException(status_code=400, detail=f"API key is required — either enter in form or export {env_var}")

    with temp_env(env_var, api_key):
        try:
            provider = get_provider(req.provider)
            model = req.model or DEFAULT_MODELS[req.provider]

            # Load checklist
            checklist = load_checklist(req.checklist_path)

            # Scan files
            include_paths = [p.strip() for p in req.include_paths.split(",") if p.strip()]
            files = scan_files(str(project_dir), include_paths, not req.no_tests, False)

            if not files:
                raise HTTPException(
                    status_code=400,
                    detail=f"No .go files found in {project_dir} with include paths: {include_paths}",
                )

            # Run audit
            result = audit_code(req.task, req.desc, checklist, files, provider, model)

            # Build response — same structure as HTML reporter
            title_by_id = {item.id: item.title for item in checklist}
            cat_by_id = {item.id: item.category for item in checklist}

            counts = {"done": 0, "missing": 0, "partial": 0, "not_applicable": 0}
            items = []
            for r in result.results:
                status = r.get("status", "missing")
                counts[status] = counts.get(status, 0) + 1
                items.append({
                    "title": title_by_id.get(r["stepId"], r["stepId"]),
                    "status": status,
                    "evidence": r.get("evidence", ""),
                    "category": cat_by_id.get(r["stepId"], ""),
                })

            total = len(items)
            done_pct = (counts["done"] * 100 // total) if total > 0 else 0

            return {
                "task": req.task,
                "desc": req.desc,
                "model": model,
                "provider": req.provider,
                "files_scanned": len(files),
                "total_steps": total,
                "done_pct": done_pct,
                "counts": counts,
                "items": items,
                "missing_items": result.missing_items,
                "summary": result.summary,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────
# Embedded HTML — Single Page App
# ─────────────────────────────────────────────────────────
WEB_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>taskaudit — Web UI</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #f8fafc; color: #1e293b;
    line-height: 1.6; -webkit-font-smoothing: antialiased;
    min-height: 100vh;
  }
  .mono { font-family: 'JetBrains Mono', monospace; }

  /* ── Layout ── */
  .app { display: flex; min-height: 100vh; }
  .sidebar {
    width: 380px; min-width: 380px; background: #fff;
    border-right: 1px solid #e2e8f0; padding: 24px;
    overflow-y: auto; height: 100vh; position: sticky; top: 0;
  }
  .main {
    flex: 1; padding: 32px; overflow-y: auto;
    min-width: 0;
  }

  /* ── Sidebar ── */
  .logo { font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
  .logo span { color: #3b82f6; }
  .logo-sub { font-size: 11px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 24px; }

  .form-group { margin-bottom: 16px; }
  .form-group label {
    display: block; font-size: 11px; font-weight: 600;
    color: #64748b; letter-spacing: 0.8px; text-transform: uppercase;
    margin-bottom: 6px;
  }
  .form-group input, .form-group select, .form-group textarea {
    width: 100%; padding: 9px 12px; border: 1px solid #e2e8f0;
    border-radius: 8px; font-size: 13px; background: #f8fafc;
    color: #1e293b; font-family: inherit; transition: border-color 0.15s;
  }
  .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
    outline: none; border-color: #3b82f6; background: #fff;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
  }
  .form-group textarea { resize: vertical; min-height: 60px; }
  .form-group .hint { font-size: 11px; color: #94a3b8; margin-top: 4px; }

  /* ── Dir browser ── */
  .dir-input-wrap { display: flex; gap: 6px; }
  .dir-input-wrap input { flex: 1; }
  .btn-browse {
    padding: 9px 14px; background: #f1f5f9; border: 1px solid #e2e8f0;
    border-radius: 8px; font-size: 12px; cursor: pointer; color: #475569;
    white-space: nowrap; font-weight: 500; transition: all 0.15s;
  }
  .btn-browse:hover { background: #e2e8f0; }

  /* ── Modal ── */
  .modal-overlay {
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4);
    z-index: 1000; align-items: center; justify-content: center;
  }
  .modal-overlay.active { display: flex; }
  .modal {
    background: #fff; border-radius: 12px; width: 560px; max-width: 90vw;
    max-height: 80vh; display: flex; flex-direction: column;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  }
  .modal-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 16px 20px; border-bottom: 1px solid #e2e8f0;
  }
  .modal-header h3 { font-size: 14px; font-weight: 600; color: #0f172a; }
  .modal-close {
    background: none; border: none; font-size: 20px; cursor: pointer;
    color: #94a3b8; padding: 4px 8px; border-radius: 4px;
  }
  .modal-close:hover { background: #f1f5f9; color: #475569; }
  .modal-path {
    padding: 10px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #475569;
    word-break: break-all;
  }
  .modal-body { flex: 1; overflow-y: auto; padding: 8px 0; }
  .modal-footer {
    padding: 12px 20px; border-top: 1px solid #e2e8f0;
    display: flex; justify-content: flex-end; gap: 8px;
  }
  .dir-item {
    display: flex; align-items: center; gap: 10px; padding: 8px 20px;
    cursor: pointer; font-size: 13px; color: #334155; transition: background 0.1s;
  }
  .dir-item:hover { background: #f1f5f9; }
  .dir-item.is-dir { font-weight: 500; }
  .dir-item .icon { font-size: 16px; min-width: 20px; text-align: center; }
  .dir-item-up { color: #3b82f6; font-weight: 600; }

  /* ── Buttons ── */
  .btn {
    padding: 10px 20px; border-radius: 8px; font-size: 13px;
    font-weight: 600; cursor: pointer; border: none; transition: all 0.15s;
  }
  .btn-primary {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: #fff; width: 100%;
  }
  .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59,130,246,0.3); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
  .btn-secondary { background: #f1f5f9; border: 1px solid #e2e8f0; color: #475569; }
  .btn-secondary:hover { background: #e2e8f0; }
  .btn-select { background: #3b82f6; color: #fff; }
  .btn-select:hover { background: #2563eb; }

  /* ── Checkbox ── */
  .checkbox-wrap {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: #475569; cursor: pointer;
  }
  .checkbox-wrap input { width: 16px; height: 16px; accent-color: #3b82f6; cursor: pointer; }

  /* ── Loading ── */
  .loading {
    display: none; align-items: center; justify-content: center;
    flex-direction: column; gap: 16px; padding: 80px 20px;
  }
  .loading.active { display: flex; }
  .spinner {
    width: 40px; height: 40px; border: 3px solid #e2e8f0;
    border-top-color: #3b82f6; border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-text { color: #64748b; font-size: 14px; font-weight: 500; }

  /* ── Welcome state ── */
  .welcome {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; padding: 80px 40px; text-align: center;
    color: #94a3b8;
  }
  .welcome-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
  .welcome h2 { font-size: 20px; font-weight: 600; color: #64748b; margin-bottom: 8px; }
  .welcome p { font-size: 13px; max-width: 400px; }

  /* ── Results (reuse HTML reporter style) ── */
  .results { display: none; }
  .results.active { display: block; }

  .result-header {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 28px; margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .result-badge {
    display: inline-block; background: #eff6ff; color: #2563eb;
    font-size: 11px; letter-spacing: 0.8px; padding: 4px 10px;
    border-radius: 4px; margin-bottom: 12px; font-weight: 600;
  }
  .result-header h1 { color: #0f172a; font-size: 26px; font-weight: 700; margin-bottom: 6px; }
  .result-desc { color: #64748b; font-size: 14px; margin-top: 8px; }
  .result-meta {
    color: #94a3b8; font-size: 12px; margin-top: 14px;
    font-family: 'JetBrains Mono', monospace;
  }
  .progress-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; margin-top: 16px; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #8b5cf6); transition: width 0.5s; }

  .summary-box {
    background: #fff; border: 1px solid #e2e8f0; border-left: 3px solid #3b82f6;
    border-radius: 8px; padding: 18px 20px; margin-bottom: 20px;
    color: #334155; font-size: 14px;
  }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 28px; }
  .stat { padding: 14px 16px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; }
  .stat-label { font-size: 10px; letter-spacing: 1px; color: #94a3b8; margin-bottom: 6px; font-weight: 600; }
  .stat-value { font-size: 24px; font-weight: 700; }
  .stat.done { border-top: 3px solid #10b981; } .stat.done .stat-value { color: #059669; }
  .stat.missing { border-top: 3px solid #ef4444; } .stat.missing .stat-value { color: #dc2626; }
  .stat.partial { border-top: 3px solid #f59e0b; } .stat.partial .stat-value { color: #d97706; }
  .stat.na { border-top: 3px solid #cbd5e1; } .stat.na .stat-value { color: #64748b; }

  .section-title {
    font-size: 11px; color: #64748b; letter-spacing: 1.2px;
    margin: 28px 0 12px 0; font-weight: 700; text-transform: uppercase;
  }

  .item {
    display: flex; gap: 14px; padding: 14px 18px;
    background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
    margin-bottom: 6px; transition: box-shadow 0.15s;
  }
  .item:hover { box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
  .item.missing { border-left: 3px solid #ef4444; }
  .item.partial { border-left: 3px solid #f59e0b; }
  .item.done { border-left: 3px solid #10b981; }
  .item.not_applicable { border-left: 3px solid #cbd5e1; opacity: 0.7; }
  .r-icon { font-size: 18px; min-width: 22px; font-weight: 700; }
  .r-icon.done { color: #10b981; } .r-icon.missing { color: #ef4444; }
  .r-icon.partial { color: #f59e0b; } .r-icon.na { color: #94a3b8; }
  .item-body { flex: 1; }
  .item-title { color: #0f172a; font-size: 14px; font-weight: 500; margin-bottom: 4px; }
  .item-evidence { color: #64748b; font-size: 13px; }
  .cat-badge {
    display: inline-block; font-size: 9px; padding: 3px 9px;
    border-radius: 4px; background: #f1f5f9; border: 1px solid #e2e8f0;
    color: #475569; font-weight: 700; letter-spacing: 0.5px;
    align-self: center; text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
  }

  .missing-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 18px; margin-bottom: 8px; }
  .missing-card.high { border-left: 3px solid #ef4444; background: #fef2f2; }
  .missing-card.medium { border-left: 3px solid #f59e0b; background: #fffbeb; }
  .missing-card.low { border-left: 3px solid #3b82f6; background: #eff6ff; }
  .missing-header { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
  .missing-title { color: #0f172a; font-size: 14px; font-weight: 600; }
  .severity-badge {
    font-size: 9px; padding: 3px 9px; border-radius: 4px; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
  }
  .severity-badge.high { background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; }
  .severity-badge.medium { background: #fef3c7; border: 1px solid #fcd34d; color: #b45309; }
  .severity-badge.low { background: #dbeafe; border: 1px solid #93c5fd; color: #1d4ed8; }
  .missing-reason { color: #475569; font-size: 13px; }
  .empty-good {
    text-align: center; padding: 32px; background: #f0fdf4;
    border: 1px dashed #86efac; border-radius: 8px;
    color: #15803d; font-size: 13px; font-weight: 500;
  }

  /* ── Error toast ── */
  .toast {
    display: none; position: fixed; bottom: 24px; right: 24px;
    background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b;
    padding: 12px 20px; border-radius: 8px; font-size: 13px;
    max-width: 480px; z-index: 2000; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  .toast.active { display: block; }
  .toast .toast-close {
    position: absolute; top: 4px; right: 8px; background: none;
    border: none; font-size: 16px; cursor: pointer; color: #991b1b;
  }

  /* ── Responsive ── */
  @media (max-width: 900px) {
    .app { flex-direction: column; }
    .sidebar { width: 100%; min-width: 0; height: auto; position: static; border-right: none; border-bottom: 1px solid #e2e8f0; }
    .main { padding: 20px; }
    .stats { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div class="app">
  <!-- ── Sidebar: Config Form ── -->
  <div class="sidebar">
    <div class="logo">task<span>audit</span></div>
    <div class="logo-sub">Web UI &mdash; code audit with AI</div>

    <div class="form-group">
      <label>AI Provider</label>
      <select id="provider">
        <option value="anthropic">Anthropic</option>
        <option value="openai">OpenAI</option>
        <option value="gemini">Google Gemini</option>
        <option value="openrouter">OpenRouter</option>
      </select>
    </div>

    <div class="form-group">
      <label>API Key</label>
      <input type="password" id="apiKey" placeholder="sk-... (or leave empty to use env var)" autocomplete="off">
      <div class="hint">Saved in browser localStorage</div>
    </div>

    <div class="form-group">
      <label>Model</label>
      <div class="dir-input-wrap">
        <select id="model" style="flex:1"></select>
        <button class="btn-browse" id="fetchModelsBtn" onclick="fetchModels()">Fetch</button>
      </div>
      <div class="hint" id="modelHint">Enter API key then click Fetch to load models</div>
    </div>

    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">

    <div class="form-group">
      <label>Task Name *</label>
      <input type="text" id="task" placeholder="e.g. Test">
    </div>

    <div class="form-group">
      <label>Description</label>
      <textarea id="desc" placeholder="Optional description..."></textarea>
    </div>

    <div class="form-group">
      <label>Project Directory *</label>
      <div class="dir-input-wrap">
        <input type="text" id="projectDir" placeholder="/path/to/go/project">
        <button class="btn-browse" onclick="openBrowser()">Browse</button>
      </div>
    </div>

    <div class="form-group">
      <label>Checklist File</label>
      <div class="dir-input-wrap">
        <input type="text" id="checklistPath" placeholder="(optional) path to checklist.txt">
        <button class="btn-browse" onclick="openFileBrowser()">Browse</button>
      </div>
      <div class="hint">Format: "category: title" per line. Leave empty for built-in checklist.</div>
    </div>

    <div class="form-group">
      <label>Include Paths</label>
      <input type="text" id="includePaths" placeholder="internal/handler,internal/service,...">
      <div class="hint">Comma-separated relative paths</div>
    </div>

    <div class="form-group">
      <label class="checkbox-wrap">
        <input type="checkbox" id="noTests">
        Exclude _test.go files
      </label>
    </div>

    <button class="btn btn-primary" id="runBtn" onclick="runAudit()">
      Run Audit
    </button>
    <button class="btn btn-secondary" id="exportBtn" onclick="exportMd()" style="display:none; width:100%; margin-top:8px;">
      Export Markdown
    </button>
  </div>

  <!-- ── Main: Results ── -->
  <div class="main">
    <div class="welcome" id="welcome">
      <div class="welcome-icon">&#128270;</div>
      <h2>Ready to Audit</h2>
      <p>Configure settings in the sidebar, select your Go project directory, and click "Run Audit" to start.</p>
    </div>

    <div class="loading" id="loading">
      <div class="spinner"></div>
      <div class="loading-text" id="loadingText">Running audit...</div>
    </div>

    <div class="results" id="results"></div>
  </div>
</div>

<!-- ── Directory Browser Modal ── -->
<div class="modal-overlay" id="browserModal">
  <div class="modal">
    <div class="modal-header">
      <h3>Select Project Directory</h3>
      <button class="modal-close" onclick="closeBrowser()">&times;</button>
    </div>
    <div class="modal-path" id="browserPath">~</div>
    <div class="modal-body" id="browserList"></div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeBrowser()">Cancel</button>
      <button class="btn btn-select" onclick="selectDir()">Select This Directory</button>
    </div>
  </div>
</div>

<!-- ── File Browser Modal (for checklist) ── -->
<div class="modal-overlay" id="fileBrowserModal">
  <div class="modal">
    <div class="modal-header">
      <h3>Select Checklist File</h3>
      <button class="modal-close" onclick="closeFileBrowser()">&times;</button>
    </div>
    <div class="modal-path" id="fileBrowserPath">~</div>
    <div class="modal-body" id="fileBrowserList"></div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeFileBrowser()">Cancel</button>
    </div>
  </div>
</div>

<!-- ── Error Toast ── -->
<div class="toast" id="toast">
  <button class="toast-close" onclick="hideToast()">&times;</button>
  <span id="toastMsg"></span>
</div>

<script>
// ─────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────
let browserCurrentPath = '~';
let defaults = {};
let lastAuditData = null;

// ─────────────────────────────────────────────────────────
// Init — load defaults + restore localStorage
// ─────────────────────────────────────────────────────────
async function init() {
  try {
    const resp = await fetch('/api/defaults');
    defaults = await resp.json();
    document.getElementById('includePaths').placeholder = defaults.default_include_paths || 'Leave empty to scan all';
    resetModelSelect();
  } catch (e) {
    console.error('Failed to load defaults:', e);
  }

  // Restore API keys from localStorage
  const provider = document.getElementById('provider').value;
  restoreApiKey(provider);

  // Restore last used values
  const lastTask = localStorage.getItem('ta_task');
  if (lastTask) document.getElementById('task').value = lastTask;
  const lastDir = localStorage.getItem('ta_dir');
  if (lastDir) document.getElementById('projectDir').value = lastDir;
  const lastInclude = localStorage.getItem('ta_include');
  if (lastInclude) document.getElementById('includePaths').value = lastInclude;
  const lastChecklist = localStorage.getItem('ta_checklist');
  if (lastChecklist) document.getElementById('checklistPath').value = lastChecklist;
  const lastProvider = localStorage.getItem('ta_provider');
  if (lastProvider) {
    document.getElementById('provider').value = lastProvider;
    restoreApiKey(lastProvider);
    resetModelSelect();
  }

  // Auto-fetch models if key already saved
  autoFetchModels();
}

function restoreApiKey(provider) {
  const saved = localStorage.getItem('ta_key_' + provider);
  document.getElementById('apiKey').value = saved || '';
}

function saveApiKey(provider, key) {
  if (key) localStorage.setItem('ta_key_' + provider, key);
}

// Provider change → restore API key + reset/fetch models
document.getElementById('provider').addEventListener('change', function() {
  restoreApiKey(this.value);
  resetModelSelect();
  autoFetchModels();
});

// API key blur → auto-fetch models
document.getElementById('apiKey').addEventListener('blur', function() {
  const provider = document.getElementById('provider').value;
  saveApiKey(provider, this.value);
  autoFetchModels();
});

function resetModelSelect() {
  const select = document.getElementById('model');
  const provider = document.getElementById('provider').value;
  const defaultModel = (defaults.default_models || {})[provider] || '';
  select.innerHTML = '<option value="">Default (' + escapeHtml(defaultModel) + ')</option>';
  document.getElementById('modelHint').textContent = 'Enter API key then click Fetch to load models';
}

function autoFetchModels() {
  const apiKey = document.getElementById('apiKey').value.trim();
  if (apiKey) fetchModels();
}

async function fetchModels() {
  const provider = document.getElementById('provider').value;
  const apiKey = document.getElementById('apiKey').value.trim();
  const hint = document.getElementById('modelHint');
  const btn = document.getElementById('fetchModelsBtn');

  if (!apiKey) {
    hint.textContent = 'API key required to fetch models';
    showToast('Enter API key first to fetch models');
    return;
  }

  // Save key when user clicks Fetch
  saveApiKey(provider, apiKey);

  btn.disabled = true;
  btn.textContent = '...';
  hint.textContent = 'Fetching models from ' + provider + '...';

  try {
    const resp = await fetch('/api/models', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: provider, api_key: apiKey }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(data.detail || 'Failed to fetch models');
    }

    const select = document.getElementById('model');
    const defaultModel = (defaults.default_models || {})[provider] || '';
    select.innerHTML = '<option value="">Default (' + escapeHtml(defaultModel) + ')</option>';

    if (data.models && data.models.length > 0) {
      for (const m of data.models) {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        select.appendChild(opt);
      }
      hint.textContent = data.models.length + ' models loaded';
    } else {
      hint.textContent = 'No models returned';
    }
  } catch (e) {
    hint.textContent = 'Error: ' + e.message;
    showToast('Fetch models failed: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Fetch';
  }
}

// ─────────────────────────────────────────────────────────
// Directory Browser
// ─────────────────────────────────────────────────────────
async function openBrowser() {
  const current = document.getElementById('projectDir').value || '~';
  browserCurrentPath = current;
  document.getElementById('browserModal').classList.add('active');
  await loadDirectory(current);
}

function closeBrowser() {
  document.getElementById('browserModal').classList.remove('active');
}

function selectDir() {
  document.getElementById('projectDir').value = browserCurrentPath;
  localStorage.setItem('ta_dir', browserCurrentPath);
  closeBrowser();
}

async function loadDirectory(path) {
  const listEl = document.getElementById('browserList');
  listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#94a3b8">Loading...</div>';

  try {
    const resp = await fetch('/api/browse?path=' + encodeURIComponent(path));
    if (!resp.ok) {
      const err = await resp.json();
      listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#ef4444">' + escapeHtml(err.detail) + '</div>';
      return;
    }
    const data = await resp.json();
    browserCurrentPath = data.current;
    document.getElementById('browserPath').textContent = data.current;

    listEl.innerHTML = '';

    // Parent directory link
    if (data.parent) {
      const div = document.createElement('div');
      div.className = 'dir-item dir-item-up';
      div.innerHTML = '<span class="icon">&#8593;</span><span>.. (parent)</span>';
      div.addEventListener('click', function() { loadDirectory(data.parent); });
      listEl.appendChild(div);
    }

    // Entries
    for (const entry of data.entries) {
      const div = document.createElement('div');
      if (entry.is_dir) {
        div.className = 'dir-item is-dir';
        div.innerHTML = '<span class="icon">&#128193;</span><span>' + escapeHtml(entry.name) + '</span>';
        div.addEventListener('click', (function(p) { return function() { loadDirectory(p); }; })(entry.path));
      } else {
        div.className = 'dir-item';
        div.style.cssText = 'color:#94a3b8;cursor:default';
        div.innerHTML = '<span class="icon">&#128196;</span><span>' + escapeHtml(entry.name) + '</span>';
      }
      listEl.appendChild(div);
    }

    if (!data.entries.length && !data.parent) {
      listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#94a3b8">Empty directory</div>';
    }
  } catch (e) {
    listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#ef4444">Failed to browse: ' + escapeHtml(e.message) + '</div>';
  }
}

// ─────────────────────────────────────────────────────────
// File Browser (for checklist)
// ─────────────────────────────────────────────────────────
let fileBrowserCurrentPath = '~';

async function openFileBrowser() {
  const current = document.getElementById('checklistPath').value || document.getElementById('projectDir').value || '~';
  // If current is a file, browse its parent
  const startPath = current.includes('.') && !current.endsWith('/') ? current.substring(0, current.lastIndexOf('/')) || '~' : current;
  fileBrowserCurrentPath = startPath;
  document.getElementById('fileBrowserModal').classList.add('active');
  await loadFileDirectory(startPath);
}

function closeFileBrowser() {
  document.getElementById('fileBrowserModal').classList.remove('active');
}

function selectFile(filePath) {
  document.getElementById('checklistPath').value = filePath;
  localStorage.setItem('ta_checklist', filePath);
  closeFileBrowser();
}

async function loadFileDirectory(path) {
  const listEl = document.getElementById('fileBrowserList');
  listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#94a3b8">Loading...</div>';

  try {
    const resp = await fetch('/api/browse?path=' + encodeURIComponent(path));
    if (!resp.ok) {
      const err = await resp.json();
      listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#ef4444">' + escapeHtml(err.detail) + '</div>';
      return;
    }
    const data = await resp.json();
    fileBrowserCurrentPath = data.current;
    document.getElementById('fileBrowserPath').textContent = data.current;

    listEl.innerHTML = '';

    // Parent directory link
    if (data.parent) {
      const div = document.createElement('div');
      div.className = 'dir-item dir-item-up';
      div.innerHTML = '<span class="icon">&#8593;</span><span>.. (parent)</span>';
      div.addEventListener('click', function() { loadFileDirectory(data.parent); });
      listEl.appendChild(div);
    }

    // Entries — dirs navigable, files clickable to select
    for (const entry of data.entries) {
      const div = document.createElement('div');
      if (entry.is_dir) {
        div.className = 'dir-item is-dir';
        div.innerHTML = '<span class="icon">&#128193;</span><span>' + escapeHtml(entry.name) + '</span>';
        div.addEventListener('click', (function(p) { return function() { loadFileDirectory(p); }; })(entry.path));
      } else {
        div.className = 'dir-item';
        div.style.cursor = 'pointer';
        const isText = entry.name.endsWith('.txt') || entry.name.endsWith('.md') || entry.name.endsWith('.checklist');
        div.innerHTML = '<span class="icon">' + (isText ? '&#128203;' : '&#128196;') + '</span><span>' + escapeHtml(entry.name) + '</span>';
        if (isText) div.style.color = '#2563eb';
        div.addEventListener('click', (function(p) { return function() { selectFile(p); }; })(entry.path));
      }
      listEl.appendChild(div);
    }

    if (!data.entries.length && !data.parent) {
      listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#94a3b8">Empty directory</div>';
    }
  } catch (e) {
    listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#ef4444">Failed to browse: ' + escapeHtml(e.message) + '</div>';
  }
}

// ─────────────────────────────────────────────────────────
// Run Audit
// ─────────────────────────────────────────────────────────
async function runAudit() {
  const provider = document.getElementById('provider').value;
  const apiKey = document.getElementById('apiKey').value;
  const model = document.getElementById('model').value;
  const task = document.getElementById('task').value.trim();
  const desc = document.getElementById('desc').value.trim();
  const projectDir = document.getElementById('projectDir').value.trim();
  const includePaths = document.getElementById('includePaths').value.trim();
  const noTests = document.getElementById('noTests').checked;
  const checklistPath = document.getElementById('checklistPath').value.trim();

  // Validation
  if (!task) { showToast('Task name is required'); return; }
  if (!projectDir) { showToast('Project directory is required'); return; }

  // Save to localStorage
  saveApiKey(provider, apiKey);
  localStorage.setItem('ta_task', task);
  localStorage.setItem('ta_dir', projectDir);
  localStorage.setItem('ta_provider', provider);
  localStorage.setItem('ta_include', includePaths);

  // UI: show loading
  document.getElementById('welcome').style.display = 'none';
  document.getElementById('results').classList.remove('active');
  document.getElementById('loading').classList.add('active');
  document.getElementById('loadingText').textContent = 'Auditing with ' + provider + '/' + (model || 'default') + '...';
  document.getElementById('runBtn').disabled = true;

  try {
    const resp = await fetch('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider, api_key: apiKey, model, task, desc,
        project_dir: projectDir, include_paths: includePaths, no_tests: noTests,
        checklist_path: checklistPath || null,
      }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Audit failed');
    }

    const data = await resp.json();
    renderResults(data);
  } catch (e) {
    showToast(e.message);
    document.getElementById('welcome').style.display = 'flex';
  } finally {
    document.getElementById('loading').classList.remove('active');
    document.getElementById('runBtn').disabled = false;
  }
}

// ─────────────────────────────────────────────────────────
// Render Results
// ─────────────────────────────────────────────────────────
function renderResults(data) {
  const statusIcon = { done: '&#10003;', missing: '&#10007;', partial: '&#9680;', not_applicable: '&mdash;' };
  const statusClass = { done: 'done', missing: 'missing', partial: 'partial', not_applicable: 'na' };

  let html = '';

  // Header
  html += '<div class="result-header">';
  html += '  <div class="result-badge">CODE AUDIT REPORT</div>';
  html += '  <h1>' + escapeHtml(data.task) + '</h1>';
  if (data.desc) html += '  <div class="result-desc">' + escapeHtml(data.desc) + '</div>';
  html += '  <div class="result-meta">' + data.provider + '/' + escapeHtml(data.model) +
    ' &bull; ' + data.files_scanned + ' files scanned &bull; ' +
    data.total_steps + ' steps &bull; ' + data.done_pct + '% complete</div>';
  html += '  <div class="progress-bar"><div class="progress-fill" style="width:' + data.done_pct + '%"></div></div>';
  html += '</div>';

  // Summary
  html += '<div class="summary-box">' + escapeHtml(data.summary) + '</div>';

  // Stats
  html += '<div class="stats">';
  html += '  <div class="stat done"><div class="stat-label">DONE</div><div class="stat-value">' + data.counts.done + '</div></div>';
  html += '  <div class="stat missing"><div class="stat-label">MISSING</div><div class="stat-value">' + data.counts.missing + '</div></div>';
  html += '  <div class="stat partial"><div class="stat-label">PARTIAL</div><div class="stat-value">' + data.counts.partial + '</div></div>';
  html += '  <div class="stat na"><div class="stat-label">N/A</div><div class="stat-value">' + data.counts.not_applicable + '</div></div>';
  html += '</div>';

  // Checklist items
  html += '<div class="section-title">CHECKLIST RESULTS (' + data.items.length + ')</div>';
  for (const item of data.items) {
    const sc = statusClass[item.status] || 'na';
    html += '<div class="item ' + item.status + '">';
    html += '  <div class="r-icon ' + sc + '">' + (statusIcon[item.status] || '&mdash;') + '</div>';
    html += '  <div class="item-body">';
    html += '    <div class="item-title">' + escapeHtml(item.title) + '</div>';
    if (item.evidence) html += '    <div class="item-evidence">' + escapeHtml(item.evidence) + '</div>';
    html += '  </div>';
    if (item.category) html += '  <span class="cat-badge">' + escapeHtml(item.category).toUpperCase() + '</span>';
    html += '</div>';
  }

  // Missing items
  html += '<div class="section-title">MISSING ITEMS NOT IN CHECKLIST (' + data.missing_items.length + ')</div>';
  if (data.missing_items.length > 0) {
    for (const m of data.missing_items) {
      const sev = m.severity || 'medium';
      html += '<div class="missing-card ' + sev + '">';
      html += '  <div class="missing-header">';
      html += '    <div class="missing-title">' + escapeHtml(m.title) + '</div>';
      html += '    <span class="severity-badge ' + sev + '">' + sev.toUpperCase() + '</span>';
      html += '  </div>';
      html += '  <div class="missing-reason">' + escapeHtml(m.reason) + '</div>';
      html += '</div>';
    }
  } else {
    html += '<div class="empty-good">No additional missing items found</div>';
  }

  const resultsEl = document.getElementById('results');
  resultsEl.innerHTML = html;
  resultsEl.classList.add('active');
  resultsEl.scrollTop = 0;

  lastAuditData = data;
  document.getElementById('exportBtn').style.display = 'block';
}

// ─────────────────────────────────────────────────────────
// Export Markdown
// ─────────────────────────────────────────────────────────
function exportMd() {
  if (!lastAuditData) return;
  const d = lastAuditData;
  const icons = { done: '✅', missing: '❌', partial: '🟡', not_applicable: '⚪' };

  let md = '# 🔍 Code Audit Report — ' + d.task + '\\n\\n';
  if (d.desc) md += '> ' + d.desc + '\\n\\n';
  md += '**Provider:** `' + d.provider + '/' + d.model + '`  \\n';
  md += '**Files scanned:** `' + d.files_scanned + '`  \\n';
  md += '**Progress:** `' + d.counts.done + '/' + d.total_steps + ' done (' + d.done_pct + '%)`\\n\\n';
  md += '---\\n\\n';
  md += '## 📊 Summary\\n\\n' + d.summary + '\\n\\n';
  md += '## 📈 Stats\\n\\n';
  md += '| Status | Count |\\n|--------|-------|\\n';
  md += '| ✓ Done | ' + d.counts.done + ' |\\n';
  md += '| ✗ Missing | ' + d.counts.missing + ' |\\n';
  md += '| ◐ Partial | ' + d.counts.partial + ' |\\n';
  md += '| — N/A | ' + d.counts.not_applicable + ' |\\n\\n';
  md += '## ✓ Checklist Results\\n\\n';

  for (const item of d.items) {
    const icon = icons[item.status] || '⚪';
    const cat = item.category ? ' `' + item.category.toUpperCase() + '`' : '';
    md += '- ' + icon + ' **' + item.title + '**' + cat + '\\n';
    if (item.evidence) md += '  - _' + item.evidence + '_\\n';
  }

  md += '\\n## ⚠ Missing Items\\n\\n';
  if (d.missing_items.length === 0) {
    md += '_✓ ไม่มีอะไรขาดเพิ่มเติม_\\n';
  } else {
    for (const m of d.missing_items) {
      md += '### `' + (m.severity || 'medium').toUpperCase() + '` — ' + m.title + '\\n\\n';
      md += (m.reason || '') + '\\n\\n';
    }
  }

  md += '---\\n_Generated by taskaudit • Powered by AI_\\n';

  // Download as file
  const blob = new Blob([md], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'audit-' + d.task.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase() + '.md';
  a.click();
  URL.revokeObjectURL(url);
}

// ─────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  document.getElementById('toastMsg').textContent = msg;
  toast.classList.add('active');
  setTimeout(() => toast.classList.remove('active'), 8000);
}

function hideToast() {
  document.getElementById('toast').classList.remove('active');
}

// ─────────────────────────────────────────────────────────
// Boot
// ─────────────────────────────────────────────────────────
init().catch(e => console.error('Init failed:', e));
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────
# CLI entry point — สำหรับ `python -m taskaudit.web`
# ─────────────────────────────────────────────────────────
def start_server(port: int = 8080) -> None:
    """Start uvicorn server"""
    import uvicorn

    print(f"🌐 taskaudit Web UI starting at http://localhost:{port}")
    print(f"   Press Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="taskaudit Web UI")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    args = parser.parse_args()
    start_server(args.port)
