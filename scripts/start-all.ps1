# Start backend and frontend (each in a new window).
# Usage: .\scripts\start-all.ps1

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $root) { $root = (Get-Location).Path }

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "Backend and frontend started in separate windows."
Write-Host "Backend: http://127.0.0.1:8000  |  Frontend: http://localhost:5173"
