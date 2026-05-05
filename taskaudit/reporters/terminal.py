# ─────────────────────────────────────────────────────────
# Terminal reporter — แสดง audit report ใน terminal สีสวย (rich)
# ─────────────────────────────────────────────────────────
from rich.panel import Panel
from rich.table import Table

from ..config import console
from ..models import AuditResult, ChecklistItem


def print_report(result: AuditResult, checklist: list[ChecklistItem]) -> None:
    """แสดง audit report ใน terminal สีสวย"""

    # Map id -> title สำหรับ lookup
    title_by_id = {item.id: item.title for item in checklist}

    # Header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔍 CODE AUDIT REPORT[/]",
        border_style="cyan"
    ))

    # Summary box
    console.print()
    console.print(Panel(
        result.summary,
        title="📊 Summary",
        border_style="blue"
    ))

    # Stats — นับจำนวนแต่ละ status
    counts: dict[str, int] = {}
    for r in result.results:
        status = r["status"]
        counts[status] = counts.get(status, 0) + 1

    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_row(
        f"[green]● done: {counts.get('done', 0)}[/]",
        f"[red]● missing: {counts.get('missing', 0)}[/]",
        f"[yellow]● partial: {counts.get('partial', 0)}[/]",
        f"[dim]● n/a: {counts.get('not_applicable', 0)}[/]",
    )
    console.print()
    console.print("[bold]📈 Stats:[/]")
    console.print(stats_table)

    # Checklist results
    console.print()
    console.print("[bold]✓ Checklist Results:[/]")

    icons = {
        "done": ("✓", "green"),
        "missing": ("✗", "red"),
        "partial": ("◐", "yellow"),
        "not_applicable": ("—", "dim"),
    }

    for r in result.results:
        status = r.get("status", "missing")
        icon, color = icons.get(status, ("?", "dim"))
        step_id = r.get("stepId") or r.get("id") or ""
        title = title_by_id.get(step_id) or r.get("title") or step_id or "(unnamed)"
        console.print(f"  [{color}]{icon}[/] {title}")
        if r.get("evidence"):
            console.print(f"    [dim]{r['evidence']}[/]")

    # Missing items
    if result.missing_items:
        console.print()
        console.print("[bold yellow]⚠ สิ่งที่ขาดเพิ่มเติม:[/]")
        sev_colors = {"high": "red", "medium": "yellow", "low": "blue"}
        for item in result.missing_items:
            sev = item.get("severity", "low")
            color = sev_colors.get(sev, "dim")
            console.print(f"  [{color}][{sev.upper()}][/] {item['title']}")
            console.print(f"    [dim]{item.get('reason', '')}[/]")
    console.print()
