# ─────────────────────────────────────────────────────────
# Test coverage runner — รัน `go test -cover ./...` แล้ว parse output
# ─────────────────────────────────────────────────────────
import re
import shutil
import subprocess
from pathlib import Path

from .config import console
from .models import CoverageReport, PackageCoverage

# `ok   github.com/foo/bar    0.123s  coverage: 87.5% of statements`
# `ok   github.com/foo/bar    (cached) coverage: 87.5% of statements`
_OK_LINE = re.compile(
    r"^ok\s+(\S+)\s+.*?coverage:\s+([\d.]+)%\s+of\s+statements"
)
# `?    github.com/foo/bar    [no test files]`
_NO_TEST_LINE = re.compile(r"^\?\s+(\S+)\s+\[no test files\]")
# `FAIL github.com/foo/bar [build failed]` หรือ test fail
_FAIL_LINE = re.compile(r"^FAIL\s+(\S+)")


def run_coverage(root: str, timeout: int = 300, verbose: bool = False) -> CoverageReport:
    """รัน `go test -cover ./...` ใน root แล้ว parse coverage % ต่อ package"""

    if shutil.which("go") is None:
        return CoverageReport(
            ran=False,
            error="go binary not found in PATH",
        )

    root_path = Path(root)
    if not (root_path / "go.mod").exists():
        return CoverageReport(
            ran=False,
            error=f"go.mod not found in {root} — not a Go module",
        )

    try:
        proc = subprocess.run(
            ["go", "test", "-cover", "./..."],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return CoverageReport(
            ran=False,
            error=f"go test timed out after {timeout}s",
        )
    except OSError as e:
        return CoverageReport(ran=False, error=f"go test failed to start: {e}")

    raw = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")

    packages: list[PackageCoverage] = []
    failed: list[str] = []

    for line in raw.splitlines():
        if m := _OK_LINE.match(line):
            packages.append(PackageCoverage(
                package=m.group(1),
                percent=float(m.group(2)),
                has_tests=True,
            ))
        elif m := _NO_TEST_LINE.match(line):
            packages.append(PackageCoverage(
                package=m.group(1),
                percent=0.0,
                has_tests=False,
            ))
        elif m := _FAIL_LINE.match(line):
            failed.append(m.group(1))

    # weighted overall = mean ของ packages ที่มี test
    tested = [p for p in packages if p.has_tests]
    overall = sum(p.percent for p in tested) / len(tested) if tested else 0.0

    if verbose:
        console.print(f"  [dim]coverage: {len(packages)} packages, {len(tested)} with tests[/]")

    return CoverageReport(
        ran=True,
        overall_percent=overall,
        packages=packages,
        failed_packages=failed,
        exit_code=proc.returncode,
        raw_output=raw,
    )
