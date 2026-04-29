param(
    [switch]$Verify
)

$openClawConfigPath = Join-Path $env:USERPROFILE '.openclaw\openclaw.json'
if (-not (Test-Path $openClawConfigPath)) {
    throw "OpenClaw config not found at $openClawConfigPath"
}

$config = Get-Content -Raw $openClawConfigPath | ConvertFrom-Json
$gatewayToken = $config.gateway.auth.token
if ([string]::IsNullOrWhiteSpace($gatewayToken)) {
    throw 'OpenClaw gateway token is missing from the local config.'
}

$baseUrl = 'http://msi.tail886dbb.ts.net:18789/v1'
$model = 'openclaw/default'

$env:COPILOT_PROVIDER_TYPE = 'openai'
$env:COPILOT_PROVIDER_BASE_URL = $baseUrl
$env:COPILOT_PROVIDER_API_KEY = $gatewayToken
$env:COPILOT_MODEL = $model

if ($Verify) {
    $headers = @{ Authorization = "Bearer $gatewayToken" }
    $response = Invoke-WebRequest -UseBasicParsing -Headers $headers -Uri "$baseUrl/models" -TimeoutSec 10
    Write-Host "OpenClaw API OK ($($response.StatusCode))" -ForegroundColor Green
    Write-Host $response.Content
    exit 0
}
if (-not (Get-Command copilot -ErrorAction SilentlyContinue)) {
    throw 'GitHub Copilot CLI is not installed or not on PATH.'
}

Write-Host 'Launching GitHub Copilot CLI against OpenClaw...' -ForegroundColor Cyan
Write-Host "Base URL: $baseUrl" -ForegroundColor DarkGray
Write-Host "Model: $model" -ForegroundColor DarkGray
Write-Host 'Token source: %USERPROFILE%\.openclaw\openclaw.json' -ForegroundColor DarkGray

copilot
