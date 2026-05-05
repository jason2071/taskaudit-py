# ─────────────────────────────────────────────────────────
# Terminal reporter — แสดง audit report ใน terminal สีสวย (rich)
# ─────────────────────────────────────────────────────────
from typing import Optional

from rich.panel import Panel
from rich.table import Table

from ..config import console
from ..models import AuditResult, ChecklistItem, CoverageReport


def print_report(
    result: AuditResult,
    checklist: list[ChecklistItem],
    coverage: Optional[CoverageReport] = None,
    coverage_threshold: float = 80.0,
) -> None:
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

    # Coverage section
    if coverage is not None:
        console.print()
        if not coverage.ran:
            console.print(Panel(
                f"[yellow]⚠ {coverage.error}[/]",
                title="📊 Test Coverage",
                border_style="yellow",
            ))
        else:
            passed = coverage.overall_percent >= coverage_threshold
            color = "green" if passed else "red"
            mark = "✓" if passed else "✗"
            cov_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
            cov_table.add_column("Package", style="dim")
            cov_table.add_column("Coverage", justify="right")
            for p in coverage.packages:
                if not p.has_tests:
                    cov_table.add_row(p.package, "[dim]no tests[/]")
                else:
                    pcolor = "green" if p.percent >= coverage_threshold else "yellow" if p.percent >= 50 else "red"
                    cov_table.add_row(p.package, f"[{pcolor}]{p.percent:.1f}%[/]")
            if coverage.failed_packages:
                for fp in coverage.failed_packages:
                    cov_table.add_row(fp, "[red]FAIL[/]")
            console.print(Panel(
                cov_table,
                title=f"📊 Test Coverage — [{color}]{mark} {coverage.overall_percent:.1f}%[/] (threshold: {coverage_threshold:.0f}%)",
                border_style=color,
            ))

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
