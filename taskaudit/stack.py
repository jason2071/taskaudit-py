# ─────────────────────────────────────────────────────────
# Stack detection — ent+atlas vs plain Go
# ─────────────────────────────────────────────────────────
from pathlib import Path
from typing import Literal

Stack = Literal["ent", "plain"]

VALID_STACKS: tuple[Stack, ...] = ("ent", "plain")


def detect_stack(root: str) -> Stack:
    """ดูจาก marker files: ent/schema/, atlas.hcl, atlas.sum → ent. ไม่งั้น plain"""
    p = Path(root)
    if (p / "ent" / "schema").is_dir():
        return "ent"
    if (p / "atlas.hcl").exists() or (p / "atlas.sum").exists():
        return "ent"
    return "plain"


# ─────────────────────────────────────────────────────────
# Checklist items per stack
# ─────────────────────────────────────────────────────────
# Layout: BASE → DB-specific (ent/plain) → COMMON CODE → TEST → DOCS → REVIEW

_BASE_ANALYSIS = [
    ("analysis", "เข้าใจ requirement + ระบุ scope ที่กระทบ"),
    ("analysis", "identify edge cases และ error scenarios"),
]

_ENT_DB = [
    ("code", "ent schema (ent/schema/*.go) — fields + edges + indexes ครบ"),
    ("code", "รัน `go generate ./ent` หลังแก้ schema (ent generated code อัปเดต)"),
    ("code", "validation/default ผ่าน schema (Validators / Annotations)"),
    ("code", "query ใช้ ent client builder ไม่ raw SQL (ยกเว้น hot path)"),
    ("code", "edges + foreign keys ตรงกับ ER diagram"),
    ("code", "schema hooks/interceptors ถ้าต้อง audit log / soft delete"),
    ("code", "atlas migrate diff → versioned migration generated ใน migrations/"),
    ("code", "atlas.sum commit แล้ว + ไม่แก้ migration เก่า (append-only)"),
    ("code", "transaction ใช้ `client.Tx(ctx)` + tx.Commit/Rollback ถูกต้อง"),
]

_PLAIN_DB = [
    ("code", "model + DTO แยกจากกัน, struct tags ครบ"),
    ("code", "migration up + down (golang-migrate/sql-migrate, rollback ได้จริง)"),
    ("code", "constraints + index ใน migration ตามที่ query ใช้"),
    ("code", "repository ใช้ context.Context + prepared statement"),
    ("code", "rows.Close() + check rows.Err() เสมอ"),
    ("code", "SQL ไม่ concat string (SQL injection guard — ใช้ placeholder $1, ?)"),
    ("code", "transaction ใช้ `db.BeginTx(ctx, ...)` + defer rollback"),
]

_COMMON_CODE = [
    ("code", "business logic อยู่ที่ service ไม่รั่วไป handler/repo"),
    ("code", "validation (validator + i18n)"),
    ("code", "error wrapping + map เป็น HTTP status ที่ถูก"),
    ("code", "register route ใน main.go / router"),
    ("code", "no secret hardcoded — ใช้ env config"),
]

_ENT_TEST = [
    ("test", "ent client test ใช้ SQLite in-memory หรือ testcontainer"),
    ("test", "unit test service (table-driven, happy + error)"),
    ("test", "manual test ทุก endpoint (Postman/curl)"),
]

_PLAIN_TEST = [
    ("test", "unit test service (table-driven, happy + error)"),
    ("test", "repository test ใช้ sqlmock หรือ testcontainer"),
    ("test", "manual test ทุก endpoint (Postman/curl)"),
]

_COMMON_TAIL = [
    ("docs", "API Spec + DB Diagram อัปเดต"),
    ("review", "self review + lint/gofmt pass"),
    ("review", "cleanup debug print, commented code"),
]


def stack_items(stack: Stack) -> list[tuple[str, str]]:
    """รวม items ตาม stack"""
    if stack == "ent":
        return _BASE_ANALYSIS + _ENT_DB + _COMMON_CODE + _ENT_TEST + _COMMON_TAIL
    return _BASE_ANALYSIS + _PLAIN_DB + _COMMON_CODE + _PLAIN_TEST + _COMMON_TAIL
