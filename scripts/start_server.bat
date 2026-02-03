@echo off
set KNOWLEDGE_BASE_ENABLED=true
set DEEPSEEK_API_KEY=sk-4fc1e645404d439ea72c3e6500e103e9
set OPENROUTER_API_KEY=
cd C:\Users\graha\.openclaw\workspace\MercuraClone
C:\Python38\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
