# Setup

## 1. ลง Python (ถ้ายังไม่มี)

```bash
# Mac
brew install python@3.12

# เช็คว่าได้ 3.10 ขึ้นไป
python3 --version
```

## 2. สร้าง virtual environment

```bash
cd ~/Desktop/work/taskaudit-py

# สร้าง virtual env
python3 -m venv venv

# Activate (ทุกครั้งที่จะใช้)
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

## 3. Set API key (เลือกตาม provider ที่ใช้)

**วิธีที่ 1: ใช้ `.env` file (แนะนำ)**

```bash
cp .env.example .env
# แก้ .env ใส่ API key + เลือก provider/model
```

**วิธีที่ 2: export ตรง**

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Gemini
export GEMINI_API_KEY="AI..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."

# Ollama (no API key — host URL)
export OLLAMA_HOST="http://localhost:11434"
```

> `.env` จะถูกโหลดก่อน — ถ้า export env var ไว้ด้วยจะ override ค่าใน `.env`

## 4. ทดสอบ

```bash
python3 taskaudit.py --help
# หรือ
python3 -m taskaudit --help

# เปิด Web UI
python3 taskaudit.py web
```

## ทำให้รันเป็น `taskaudit` ตรงๆ

### Shell alias (ง่ายสุด)

```bash
echo 'alias taskaudit="python3 ~/Desktop/work/taskaudit-py/taskaudit.py"' >> ~/.zshrc
source ~/.zshrc
```

### ใช้ pipx (best practice)

```bash
brew install pipx
pipx install ./taskaudit-py  # ต้องสร้าง pyproject.toml ก่อน
```
