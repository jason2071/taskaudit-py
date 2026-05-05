# Features

## Stack Support (ent+atlas vs plain)

Tool รองรับ 2 stack สำหรับ Go BE:

| Stack | When | Default checklist |
|-------|------|-------------------|
| `ent` | ent ORM + atlas migration | ent schema, `go generate ./ent`, atlas migrate diff, ent client builder |
| `plain` | `database/sql` / sqlx + manual migration | prepared statement, rows.Close, SQLi guard, `db.BeginTx` |

**Auto-detect priority:**
```
ent/schema/ exists       → ent
atlas.hcl / atlas.sum    → ent
otherwise                → plain
```

Override ด้วย `--stack ent|plain` หรือ `auto` (default).

## Test Coverage

ใช้ flag `--coverage` เพื่อรัน `go test -cover ./...` จริง แล้วรวมผลใน audit. AI จะใช้ % ประกอบการตัดสินสำหรับ checklist หมวด `test`:

```bash
python3 taskaudit.py --task "..." --coverage --coverage-threshold 80
```

Report จะแสดง:
- Overall coverage % (pass/fail vs threshold)
- Per-package coverage (สี: green ≥ threshold, amber ≥ 50, red < 50)
- Packages ที่ไม่มี test (`no test files`)
- Packages ที่ build/test fail

ต้องมี `go` ใน PATH + `go.mod` ใน root. ถ้าไม่มี → skip + warn (ไม่ fail audit)

## Custom Checklist

สร้างไฟล์ format `category: title` ต่อบรรทัด:

```
code: สร้าง model
code: สร้าง repository layer
code: สร้าง service layer พร้อม business logic
code: สร้าง handler + routing
test: เขียน unit test สำหรับ service
docs: Comment สำคัญ
```

```bash
python3 taskaudit.py --task "My API" --checklist ./my-checklist.txt
```

ดู template สำเร็จรูปได้ที่ `templates/checklist-ent-atlas.txt` และ `templates/checklist-plain.txt` (Web UI ดาวน์โหลดได้ใน Optional Files modal)
