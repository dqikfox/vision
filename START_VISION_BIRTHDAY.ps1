# VISION BIRTHDAY LAUNCHER
# One-click start for your sister
# Double-click this file to start Vision

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  VISION - Voice Computer Control" -ForegroundColor Cyan
Write-Host "  Starting for [Sister's Name]..." -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to Vision directory
$visionPath = "C:\project\vision"
Set-Location $visionPath

Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Python not found!" -ForegroundColor Red
    Write-Host "      Please install Python 3.10+" -ForegroundColor Red
    pause
    exit
}

Write-Host "[2/4] Checking dependencies..." -ForegroundColor Yellow
$required = @("fastapi", "uvicorn", "openai", "ollama")
$missing = @()

foreach ($pkg in $required) {
    $check = python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missing += $pkg
    }
}

if ($missing.Count -gt 0) {
    Write-Host "      Installing missing packages..." -ForegroundColor Yellow
    pip install $missing -q
}
Write-Host "      All packages ready!" -ForegroundColor Green

Write-Host "[3/4] Starting Vision backend..." -ForegroundColor Yellow
Write-Host "      Please wait 10 seconds..." -ForegroundColor Yellow
Write-Host ""

# Start Vision in background
$process = Start-Process python -ArgumentList "live_chat_app.py" -NoNewWindow -PassThru

# Wait for startup
Start-Sleep -Seconds 10

Write-Host "[4/4] Opening Vision interface..." -ForegroundColor Yellow
Start-Process "http://localhost:8765"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  VISION IS RUNNING!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps for your sister:" -ForegroundColor Cyan
Write-Host "1. Click the microphone icon in the browser" -ForegroundColor White
Write-Host "2. Say 'Help' to see available commands" -ForegroundColor White
Write-Host "3. Try: 'Open Chrome' or 'Search for music'" -ForegroundColor White
Write-Host ""
Write-Host "To stop Vision: Close this window" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop, or close window to continue running" -ForegroundColor DarkGray
Write-Host ""

# Keep window open
try {
    Wait-Process -Id $process.Id
} catch {
    # Process ended
}

Write-Host "Vision stopped." -ForegroundColor Yellow
