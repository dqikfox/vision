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

$port = if ($config.gateway.port) { $config.gateway.port } else { 18789 }

# Determine base URL based on bind configuration
$resolvedBind = if ([string]::IsNullOrWhiteSpace($config.gateway.bind) -or $config.gateway.bind -eq 'loopback') {
    '127.0.0.1'
} else {
    $config.gateway.bind
}
$baseUrl = "http://${resolvedBind}:$port/v1"

$model = 'openclaw/default'

$env:OPENCLAW_GATEWAY_TOKEN = $gatewayToken

$env:COPILOT_PROVIDER_TYPE = 'openai'
$env:COPILOT_PROVIDER_BASE_URL = $baseUrl
$env:COPILOT_PROVIDER_API_KEY = $gatewayToken
$env:COPILOT_MODEL = $model

Write-Host "Using gateway URL: $baseUrl" -ForegroundColor Cyan

if ($Verify) {
    $headers = @{ Authorization = "Bearer $gatewayToken" }
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Headers $headers -Uri "$baseUrl/models" -TimeoutSec 10
        Write-Host "OpenClaw API OK ($($response.StatusCode))" -ForegroundColor Green
        Write-Host $response.Content
    } catch {
        Write-Host "OpenClaw API check failed: $_" -ForegroundColor Red
        Write-Host "Gateway may not be running. Try: openclaw gateway run" -ForegroundColor Yellow
        exit 1
    }
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
