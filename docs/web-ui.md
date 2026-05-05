# Web UI

ใช้ผ่าน browser ได้เลย — ไม่ต้องจำ CLI flags

## Start

```bash
# Default port 8080
python3 taskaudit.py web

# Custom port
python3 taskaudit.py web --port 3000

# หรือรันตรงจาก module
python3 -m taskaudit.web --port 8080
```

เปิด browser ไปที่ `http://localhost:8080`

## คู่มือใช้งาน (step-by-step)

### 1. เลือก AI Provider + ใส่ API Key

- Dropdown **AI Provider** — เลือก `Anthropic` / `OpenAI` / `Gemini` / `OpenRouter` / `Ollama`
- ช่อง **API Key** — ใส่ key ตรงนี้ (เก็บใน `sessionStorage` — หายเมื่อปิด tab) หรือเว้นว่างถ้า export `.env` ไว้แล้ว
- Ollama: ช่องนี้กลายเป็น **Host URL** (default `http://localhost:11434`)

### 2. เลือก Model

- กดปุ่ม **Fetch** ข้าง model dropdown — โหลด model list จาก provider จริง (ใช้ API key ที่กรอก)
- ถ้าไม่ Fetch → จะใช้ default model ของ provider นั้น
- Anthropic ไม่มี list-models API → ใช้ hardcode list

### 3. ใส่ Task + Description

- **Task Name** (required) — ชื่องาน เช่น `Audit user auth API`
- **Description** (optional) — รายละเอียดงาน

### 4. เลือก Project Directory

- กดปุ่ม **Browse** เปิด file picker (browse ใน server filesystem) — เลือก root ของ Go project
- พอเลือกเสร็จ → tool จะ **auto-detect stack** ผ่าน `/api/detect-stack` แล้วแสดงผลใต้ stack dropdown

### 5. เลือก Stack

- Dropdown **Stack** — default `Auto-detect` (ใช้ผลจาก step 4)
- Override เป็น `ent + atlas` หรือ `plain (database/sql)` ถ้าต้องการ
- กระทบ checklist ที่ใช้ + AI prompt context

### 6. (ถ้าต้องการ) Optional Files & Templates

กดปุ่ม **Configure** เปิด modal — set 3 ไฟล์เสริมได้:

| File | Use |
|------|-----|
| **Checklist File** | path ไป custom checklist (`.txt`) — override built-in. ดาวน์โหลด template ent+atlas หรือ plain ได้ |
| **Context / Requirement File** | path ไป requirement doc (`.md`/`.txt`) — append เข้า AI prompt |
| **Manual Test File** | path ไป manual test results (`.md`) — รวมเข้า context |

ปุ่มดาวน์โหลด (`⤓`) ข้างแต่ละช่อง — โหลด template สำเร็จรูปไว้แก้

### 7. Include Paths

- Comma-separated paths (relative to project dir) ที่ scanner จะอ่าน
- Default: `internal/handler,internal/service,internal/repository,internal/models`
- เว้นว่าง = scan ทั้งหมด (ภายใต้ skip dirs)

### 8. Options

- ☐ **Exclude `_test.go` files** — ข้าม test files ตอน scan
- ☐ **Run `go test -cover ./...`** — เปิด coverage runner
  - พอ check จะโผล่ช่อง **Coverage Threshold (%)** (default 80)
  - AI ใช้ coverage data ตัดสิน checklist หมวด test
  - ต้องมี `go` ใน PATH + `go.mod` ใน project dir

### 9. Run Audit

กดปุ่ม **Run Audit** — spinner แสดงสถานะ. ใช้เวลา ~10–60s ขึ้นกับขนาด code + provider

### 10. ดูผล + Export

Result panel แสดง:
- **Header** — task, provider/model, files scanned, % complete, stack badge
- **Summary** — สรุปจาก AI 2-3 ประโยค
- **Stats** — Done / Missing / Partial / N/A counts
- **Coverage Panel** (ถ้าเปิด `--coverage`) — overall %, per-package table (สี: green ≥ threshold, amber ≥ 50, red < 50, dim "no tests")
- **Checklist Results** — ทุก step + status icon + AI evidence
- **Missing Items** — สิ่งที่ AI พบเพิ่มแม้ไม่อยู่ใน checklist (severity high/medium/low)

กดปุ่ม **Export Markdown** ดาวน์โหลด `.md` report

## State persistence

- **localStorage** (จำข้ามวัน): provider, dir, include paths, task, coverage settings, stack choice
- **sessionStorage** (หายเมื่อปิด tab): API keys, optional file paths

## Tip

ถ้า Web UI ค้าง / model fetch fail → ดู terminal ที่รัน `taskaudit.py web` — error จะ log ตรงนั้น
