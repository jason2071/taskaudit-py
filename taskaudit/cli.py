#!/usr/bin/env python3
"""
taskaudit - CLI tool to audit Go code against a checklist using AI.

Supported providers: anthropic (default), openai, gemini, openrouter

Usage:
    taskaudit --task "Audit API" --include handler,service,repository
    taskaudit --task "..." --provider openai --model gpt-4o
    taskaudit --task "..." --provider gemini --model gemini-2.5-flash
    taskaudit --task "..." --provider openrouter --model anthropic/claude-sonnet-4
    taskaudit --task "..." --html ./audit.html --md ./audit.md
    taskaudit web                        # start Web UI on port 8080
    taskaudit web --port 3000            # custom port

Required env per provider:
    anthropic   → ANTHROPIC_API_KEY
    openai      → OPENAI_API_KEY
    gemini      → GEMINI_API_KEY
    openrouter  → OPENROUTER_API_KEY
"""

# ─────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────
import argparse
import json
import os
import sys

from rich.progress import Progress, SpinnerColumn, TextColumn

from .audit import audit_code
from .checklist import load_checklist
from .config import API_KEY_ENV, DEFAULT_INCLUDE_DIRS, DEFAULT_MODELS, DEFAULT_PROVIDER, console
from .providers import get_provider
from .reporters.html import export_html
from .reporters.markdown import export_markdown
from .reporters.terminal import print_report
from .scanner import scan_files


def main() -> None:
    # เช็คก่อนว่าเป็น web subcommand หรือ --web flag หรือเปล่า
    # ทำก่อน argparse เพราะ --task เป็น required ใน CLI mode
    if _check_web_mode():
        return

    # argparse = standard library สำหรับ parse command-line args
    parser = argparse.ArgumentParser(
        description="Audit Go code against a checklist using AI (supports: anthropic, openai, gemini, openrouter)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task", required=True, help="Task title (required)")
    parser.add_argument("--desc", default="", help="Task description")
    parser.add_argument("--dir", default=".", help="Root directory to scan (default: .)")
    parser.add_argument("--checklist", help="Path to checklist file")
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        choices=["anthropic", "openai", "gemini", "openrouter"],
        help=f"AI provider (default: {DEFAULT_PROVIDER})",
    )
    parser.add_argument("--model", default=None, help="Model name (default: per provider)")
    parser.add_argument(
        "--include",
        default=",".join(DEFAULT_INCLUDE_DIRS),
        help=f"Comma-separated paths (default: {','.join(DEFAULT_INCLUDE_DIRS)})",
    )
    parser.add_argument("--context", help="Path to context/requirement file (.md/.txt) to include in AI prompt")
    parser.add_argument("--no-tests", action="store_true", help="Exclude _test.go files")
    parser.add_argument("--html", help="Export HTML report to path")
    parser.add_argument("--md", help="Export Markdown report to path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # เช็ค API key ตาม provider ที่เลือก
    env_var = API_KEY_ENV[args.provider]
    if not os.environ.get(env_var):
        console.print(f"[red]❌ Error: {env_var} environment variable is required for provider '{args.provider}'[/]")
        sys.exit(1)

    # สร้าง provider + เลือก model
    provider = get_provider(args.provider)
    model = args.model or DEFAULT_MODELS[args.provider]

    # 1. Load checklist
    checklist = load_checklist(args.checklist)
    if args.verbose:
        console.print(f"📋 Loaded {len(checklist)} checklist items")

    # 2. Scan files
    include_paths = [p.strip() for p in args.include.split(",")]
    files = scan_files(args.dir, include_paths, not args.no_tests, args.verbose)

    if not files:
        console.print(f"[red]❌ Error: no code files found in {args.dir}[/]")
        sys.exit(1)

    if args.verbose:
        console.print(f"📂 Found {len(files)} code files:")
        for f in files:
            console.print(f"  [dim]- {f.path} ({len(f.content)} bytes)[/]")

    # 3. Call API — มี spinner ระหว่างรอ
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
        transient=True,  # spinner จะหายไปเมื่อเสร็จ
    ) as progress:
        progress.add_task(f"Auditing code with {args.provider}/{model}...", total=None)
        # Load context file ถ้ามี
        context_text = ""
        if args.context:
            with open(args.context, encoding="utf-8") as cf:
                context_text = cf.read()

        try:
            result = audit_code(args.task, args.desc, checklist, files, provider, model, context_text)
        except Exception as e:
            console.print(f"[red]❌ Audit failed: {e}[/]")
            sys.exit(1)

    # 4. Output
    if args.json:
        # ให้ output เป็น JSON ปกติ ไม่ผ่าน rich (กัน rich ใส่สี)
        print(json.dumps({
            "results": result.results,
            "missingItems": result.missing_items,
            "summary": result.summary,
        }, ensure_ascii=False, indent=2))
        return

    if args.html:
        export_html(args.html, args.task, args.desc, result, checklist)
        console.print(f"[green]📄 HTML report saved to {args.html}[/]")

    if args.md:
        export_markdown(args.md, args.task, args.desc, result, checklist)
        console.print(f"[green]📝 Markdown report saved to {args.md}[/]")

    # Always print to terminal
    print_report(result, checklist)


def _check_web_mode() -> bool:
    """เช็คว่า user ต้องการเปิด web mode หรือเปล่า
    รองรับทั้ง `taskaudit web` และ `taskaudit --web`
    Return True ถ้าเข้า web mode (แล้ว start server)
    """
    args = sys.argv[1:]

    # `taskaudit web` หรือ `taskaudit web --port 3000`
    if args and args[0] == "web":
        port = 8080
        for i, arg in enumerate(args):
            if arg == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
        from .web import start_server
        start_server(port)
        return True

    # `taskaudit --web` หรือ `taskaudit --web --port 3000`
    if "--web" in args:
        port = 8080
        for i, arg in enumerate(args):
            if arg == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
        from .web import start_server
        start_server(port)
        return True

    return False
