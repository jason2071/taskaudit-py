# ─────────────────────────────────────────────────────────
# HTML reporter — generate light-theme HTML report ด้วย Jinja2
# ─────────────────────────────────────────────────────────
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from ..models import AuditResult, ChecklistItem


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code Audit Report — {{ task }}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #f8fafc; color: #1e293b;
    padding: 32px 24px; line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }
  .mono { font-family: 'JetBrains Mono', monospace; }
  .container { max-width: 980px; margin: 0 auto; }
  .header {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 28px; margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .badge {
    display: inline-block; background: #eff6ff; color: #2563eb;
    font-size: 11px; letter-spacing: 0.8px; padding: 4px 10px;
    border-radius: 4px; margin-bottom: 12px; font-weight: 600;
  }
  h1 { color: #0f172a; font-size: 26px; font-weight: 700; margin-bottom: 6px; }
  .desc { color: #64748b; font-size: 14px; margin-top: 8px; }
  .meta { color: #94a3b8; font-size: 12px; margin-top: 14px; font-family: 'JetBrains Mono', monospace; }
  .progress-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; margin-top: 16px; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
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
  .icon { font-size: 18px; min-width: 22px; font-weight: 700; }
  .icon.done { color: #10b981; } .icon.missing { color: #ef4444; }
  .icon.partial { color: #f59e0b; } .icon.na { color: #94a3b8; }
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
  .severity { font-size: 9px; padding: 3px 9px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; }
  .severity.high { background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; }
  .severity.medium { background: #fef3c7; border: 1px solid #fcd34d; color: #b45309; }
  .severity.low { background: #dbeafe; border: 1px solid #93c5fd; color: #1d4ed8; }
  .missing-reason { color: #475569; font-size: 13px; }
  .empty { text-align: center; padding: 32px; background: #f0fdf4; border: 1px dashed #86efac; border-radius: 8px; color: #15803d; font-size: 13px; font-weight: 500; }
  .footer { text-align: center; color: #94a3b8; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-family: 'JetBrains Mono', monospace; }
  @media (max-width: 640px) { .stats { grid-template-columns: repeat(2, 1fr); } body { padding: 16px 12px; } h1 { font-size: 22px; } }
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">🔍 CODE AUDIT REPORT</div>
      <h1>{{ task }}</h1>
      {% if desc %}<div class="desc">{{ desc }}</div>{% endif %}
      <div class="meta">Generated at {{ generated_at }} • {{ total_steps }} steps • {{ done_pct }}% complete</div>
      <div class="progress-bar"><div class="progress-fill" style="width: {{ done_pct }}%"></div></div>
    </div>

    <div class="summary-box">{{ summary }}</div>

    <div class="stats">
      <div class="stat done"><div class="stat-label">DONE</div><div class="stat-value">{{ counts.done }}</div></div>
      <div class="stat missing"><div class="stat-label">MISSING</div><div class="stat-value">{{ counts.missing }}</div></div>
      <div class="stat partial"><div class="stat-label">PARTIAL</div><div class="stat-value">{{ counts.partial }}</div></div>
      <div class="stat na"><div class="stat-label">N/A</div><div class="stat-value">{{ counts.not_applicable }}</div></div>
    </div>

    <div class="section-title">✓ Checklist Results ({{ items|length }})</div>
    {% for item in items %}
    <div class="item {{ item.status }}">
      <div class="icon {{ 'done' if item.status == 'done' else 'missing' if item.status == 'missing' else 'partial' if item.status == 'partial' else 'na' }}">
        {{ '✓' if item.status == 'done' else '✗' if item.status == 'missing' else '◐' if item.status == 'partial' else '—' }}
      </div>
      <div class="item-body">
        <div class="item-title">{{ item.title }}</div>
        {% if item.evidence %}<div class="item-evidence">{{ item.evidence }}</div>{% endif %}
      </div>
      {% if item.category %}<span class="cat-badge">{{ item.category }}</span>{% endif %}
    </div>
    {% endfor %}

    <div class="section-title">⚠ Missing Items Not in Checklist ({{ missing_items|length }})</div>
    {% if missing_items %}
      {% for m in missing_items %}
      <div class="missing-card {{ m.severity }}">
        <div class="missing-header">
          <div class="missing-title">{{ m.title }}</div>
          <span class="severity {{ m.severity }}">{{ m.severity }}</span>
        </div>
        <div class="missing-reason">{{ m.reason }}</div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">✓ ไม่มีอะไรขาดเพิ่มเติม</div>
    {% endif %}

    <div class="footer">Generated by taskaudit • Powered by AI</div>
  </div>
</body>
</html>"""


def export_html(
    path: str,
    task: str,
    desc: str,
    result: AuditResult,
    checklist: list[ChecklistItem],
) -> None:
    """Generate HTML report จาก template ด้วย Jinja2"""

    title_by_id = {item.id: item.title for item in checklist}
    cat_by_id = {item.id: item.category for item in checklist}

    # นับ stats
    counts: dict[str, int] = {"done": 0, "missing": 0, "partial": 0, "not_applicable": 0}
    items = []
    for r in result.results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        items.append({
            "title": title_by_id.get(r["stepId"], r["stepId"]),
            "status": r["status"],
            "evidence": r.get("evidence", ""),
            "category": cat_by_id.get(r["stepId"], ""),
        })

    total = len(items)
    done_pct = (counts["done"] * 100 // total) if total > 0 else 0

    # Render template — Jinja2 จะแทนที่ {{ ... }} ด้วยค่าจริง
    html = Template(HTML_TEMPLATE).render(
        task=task,
        desc=desc,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_steps=total,
        done_pct=done_pct,
        summary=result.summary,
        counts=counts,
        items=items,
        missing_items=result.missing_items,
    )

    Path(path).write_text(html, encoding="utf-8")
