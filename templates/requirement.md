# Requirement: [Task Name]

## Overview
<!-- สรุปสั้นๆ ว่างานนี้ทำอะไร -->


## Business Rules
<!-- กฎ business ที่ต้องจำ -->
- 


## Scope
<!-- ระบุ layer/file ที่กระทบ -->

| Layer | Files/Packages | Action |
|-------|---------------|--------|
| DB | `migrations/` | new table / alter |
| Model | `internal/models/` | new struct |
| Repository | `internal/repository/` | new methods |
| Service | `internal/service/` | business logic |
| Handler | `internal/handler/` | new endpoint |
| Route | `main.go` | register |

## API Contract
<!-- endpoint ที่เกี่ยวข้อง -->

```
POST /api/v1/xxx
Request:  { ... }
Response: { ... }
```

## Edge Cases
<!-- case พิเศษที่ต้อง handle -->
- 


## Acceptance Criteria
<!-- เงื่อนไขที่ถือว่า "เสร็จ" -->
- [ ] 


## Dependencies
<!-- ต้องรอ/ใช้อะไรจาก team อื่น -->
- 


## Notes
<!-- หมายเหตุเพิ่มเติม -->
- 
