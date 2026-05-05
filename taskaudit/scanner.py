# ─────────────────────────────────────────────────────────
# File scanner — เดิน folder หาไฟล์ .go
# ─────────────────────────────────────────────────────────
from pathlib import Path

from .config import MAX_FILE_BYTES, SKIP_DIRS, console
from .models import CodeFile


def scan_files(
    root: str,
    include_paths: list[str],
    include_tests: bool,
    verbose: bool,
) -> list[CodeFile]:
    """
    Walk through directory tree หาไฟล์ .go ใน include_paths.
    Pathlib เป็น modern way ของ Python ในการจัดการ path
    """
    root_path = Path(root)
    files: list[CodeFile] = []

    # rglob("*.go") = recursive glob หาไฟล์ทุก .go ในทุก subfolder
    for go_file in root_path.rglob("*.go"):
        # Get relative path สำหรับเช็ค include
        try:
            rel = go_file.relative_to(root_path)
        except ValueError:
            continue

        rel_str = str(rel)

        # Skip ถ้าอยู่ใน skip dirs
        if any(part in SKIP_DIRS for part in rel.parts):
            continue

        # Skip ถ้าไม่ตรงกับ include path
        # any() = True ถ้ามีอย่างน้อย 1 อันที่ match
        if not any(rel_str.startswith(p) for p in include_paths):
            continue

        # Skip test files ถ้าไม่ต้องการ
        if not include_tests and rel_str.endswith("_test.go"):
            continue

        # Skip ไฟล์ใหญ่เกิน
        size = go_file.stat().st_size
        if size > MAX_FILE_BYTES:
            if verbose:
                console.print(f"  [yellow]⚠ skip {rel_str} ({size/1024:.1f}KB > {MAX_FILE_BYTES//1024}KB)[/]")
            continue

        # อ่านไฟล์
        content = go_file.read_text(encoding="utf-8", errors="replace")
        files.append(CodeFile(path=rel_str, content=content))

    return files
