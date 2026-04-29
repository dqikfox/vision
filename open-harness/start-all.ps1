param(
  [string]$VisionRoot = "..",
  [string]$VisionPython = "python"
)

$ErrorActionPreference = "Stop"

function Test-PortListening {
  param([int]$Port)
  try {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    return $null -ne $conn
  }
  catch {
    return $false
  }
}

function Wait-Http {
  param(
    [string]$Url,
    [int]$Retries = 20,
    [int]$DelaySeconds = 1
  )

  for ($i = 0; $i -lt $Retries; $i++) {
    try {
      $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
        return $true
      }
    }
    catch {
      Start-Sleep -Seconds $DelaySeconds
    }
  }

  return $false
}

Write-Host "[open-harness] Starting orchestrator..."

$visionDir = Resolve-Path (Join-Path $PSScriptRoot $VisionRoot)
$visionApp = Join-Path $visionDir "live_chat_app.py"

if (!(Test-Path $visionApp)) {
  Write-Error "Vision app not found at $visionApp"
  exit 1
}

if (!(Test-PortListening -Port 8765)) {
  Write-Host "[open-harness] Vision backend not listening on 8765; starting live_chat_app.py"
  Start-Process -FilePath $VisionPython -ArgumentList "$visionApp" -WorkingDirectory $visionDir | Out-Null
}
else {
  Write-Host "[open-harness] Vision backend already listening on 8765"
}

$healthy = Wait-Http -Url "http://localhost:8765/api/health" -Retries 25 -DelaySeconds 1
if (-not $healthy) {
  Write-Warning "Vision health endpoint did not become ready in time"
}
else {
  Write-Host "[open-harness] Vision health endpoint is ready"
}

Write-Host "[open-harness] Running harness health checks"
npm run health

Write-Host "[open-harness] Starting CLI agent"
npm run start:vision-agent
