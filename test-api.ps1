# Mercura API Testing Script for Windows PowerShell
# Replace YOUR_URL with your actual deployment URL

$URL = "https://mercuraclone-production.up.railway.app"

Write-Host "Testing Mercura API..." -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Health Check:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$URL/health" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "2. Root Endpoint:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$URL/" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "3. Statistics:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$URL/data/stats" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "4. Emails:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$URL/data/emails" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "5. Line Items:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$URL/data/line-items" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "✅ Basic tests complete!" -ForegroundColor Green
Write-Host "Visit $URL/docs for interactive testing" -ForegroundColor Cyan
