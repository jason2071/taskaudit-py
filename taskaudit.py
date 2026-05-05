#!/usr/bin/env python3
"""
Backward-compatibility shim — logic ย้ายไปอยู่ใน `taskaudit/` package แล้ว
รัน: python taskaudit.py ... (เหมือนเดิม)
หรือ: python -m taskaudit ...
"""
from taskaudit.cli import main

if __name__ == "__main__":
    main()
