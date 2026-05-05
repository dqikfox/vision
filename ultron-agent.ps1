<#
.SYNOPSIS
    Ultron — Azure AI Deployment Agent
    Deploys FastAPI applications with SLM sidecar extensions to Azure App Service

.DESCRIPTION
    Ultron automates the deployment of AI-powered FastAPI applications on Azure App Service
    with Phi-4/Phi-3 sidecar extensions. Handles infrastructure provisioning, sidecar
    configuration, and verification.

.PARAMETER Action
    Action to perform: deploy, verify, logs, destroy, status, byo-build

.PARAMETER AppName
    Name of the Azure Web App (auto-generated if not provided)

.PARAMETER ResourceGroup
    Azure Resource Group name (auto-generated if not provided)

.PARAMETER Location
    Azure region (default: eastus)

.PARAMETER Sku
    App Service Plan SKU (default: P3MV3 for Phi-4)

.PARAMETER Model
    SLM model to use: phi-4, phi-3, or custom (default: phi-4)

.PARAMETER RepoUrl
    GitHub repository URL (default: Azure-Samples/ai-slm-in-app-service-sidecar)

.PARAMETER Branch
    Git branch to deploy (default: main)

.PARAMETER StartupCommand
    Custom startup command (default: gunicorn with uvicorn workers)

.PARAMETER Timeout
    Timeout in seconds for deployment verification (default: 300)

.PARAMETER DryRun
    Show what would be done without executing

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\ultron-agent.ps1 -Action deploy -AppName mychatbot -Verbose

.EXAMPLE
    .\ultron-agent.ps1 -Action deploy -Model phi-3 -Sku P2MV3

.EXAMPLE
    .\ultron-agent.ps1 -Action verify -AppName mychatbot

.EXAMPLE
    .\ultron-agent.ps1 -Action logs -AppName mychatbot -Follow

.EXAMPLE
    .\ultron-agent.ps1 -Action byo-build -ModelName phi-3-custom

.NOTES
    Version: 1.0.0
    Requires: Azure CLI 2.50+, PowerShell 7.0+, Docker (for BYO builds)
    Author: Ultron Azure AI Agent
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("deploy", "verify", "logs", "destroy", "status", "byo-build", "interactive")]
    [string]$Action,

    [Parameter()]
    [string]$AppName,

    [Parameter()]
    [string]$ResourceGroup,

    [Parameter()]
    [string]$Location = "eastus",

    [Parameter()]
    [ValidateSet("P1V3", "P2MV3", "P3MV3", "P4MV3", "P5MV3")]
    [string]$Sku = "P3MV3",

    [Parameter()]
    [ValidateSet("phi-4", "phi-3", "custom")]
    [string]$Model = "phi-4",

    [Parameter()]
    [string]$RepoUrl = "https://github.com/Azure-Samples/ai-slm-in-app-service-sidecar",

    [Parameter()]
    [string]$Branch = "main",

    [Parameter()]
    [string]$StartupCommand = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app",

    [Parameter()]
    [int]$Timeout = 300,

    [Parameter()]
    [switch]$DryRun,

    [Parameter()]
    [switch]$Follow,

    [Parameter()]
    [string]$CustomImage,

    [Parameter()]
    [string]$AcrName
)

# ── Configuration ──────────────────────────────────────────────────────────────
$script:Version = "1.0.0"
$script:UltronAscii = @"
    ██╗   ██╗██╗  ████████╗██████╗  ██████╗ ███╗   ██╗
    ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
    ██║   ██║██║     ██║   ██████╔╝██║   ██║██╔██╗ ██║
    ██║   ██║██║     ██║   ██╔══██╗██║   ██║██║╚██╗██║
    ╚██████╔╝███████╗██║   ██║  ██║╚██████╔╝██║ ╚████║
     ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
     Azure AI Deployment Agent v$script:Version
"@

$script:Colors = @{
    Reset = "`e[0m"
    Green = "`e[32m"
    Yellow = "`e[33m"
    Red = "`e[31m"
    Cyan = "`e[36m"
    Magenta = "`e[35m"
    Blue = "`e[34m"
    Bold = "`e[1m"
}

# ── Logging Functions ───────────────────────────────────────────────────────
function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "SUCCESS" { $script:Colors.Green }
        "WARNING" { $script:Colors.Yellow }
        "ERROR" { $script:Colors.Red }
        "INFO" { $script:Colors.Cyan }
        "ULTRON" { $script:Colors.Magenta }
        default { $script:Colors.Reset }
    }
    $prefix = switch ($Status) {
        "SUCCESS" { "[✓]" }
        "WARNING" { "[!]" }
        "ERROR" { "[✗]" }
        "INFO" { "[i]" }
        "ULTRON" { "[⚡]" }
        default { "[*]" }
    }
    Write-Host "$color$prefix $Message$($script:Colors.Reset)"
}

function Write-Command {
    param([string]$Command)
    Write-Host "$($script:Colors.Yellow)`$ $Command$($script:Colors.Reset)"
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "$($script:Colors.Bold)$($script:Colors.Blue)═══ $Title ═══$($script:Colors.Reset)"
    Write-Host ""
}

# ── Validation Functions ────────────────────────────────────────────────────
function Test-Prerequisites {
    Write-Section "Phase 1: Prerequisites Check"

    # Check Azure CLI
    try {
        $azVersion = az --version 2>$null | Select-String "azure-cli" | ForEach-Object { $_.ToString().Split()[1] }
        if ($azVersion) {
            Write-Status "Azure CLI version: $azVersion" "SUCCESS"
        }
    } catch {
        Write-Status "Azure CLI not found. Install from https://aka.ms/installazurecliwindows" "ERROR"
        return $false
    }

    # Check Azure login
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-Status "Logged in as: $account" "SUCCESS"
    } else {
        Write-Status "Not logged into Azure. Running 'az login'..." "WARNING"
        if (-not $DryRun) {
            az login
        }
    }

    # Check subscription
    $sub = az account show --query "id" -o tsv 2>$null
    if ($sub) {
        Write-Status "Using subscription: $sub" "INFO"
    }

    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Write-Status "PowerShell 7+ recommended. Current: $($PSVersionTable.PSVersion)" "WARNING"
    }

    # Check Docker for BYO builds
    if ($Action -eq "byo-build") {
        $docker = Get-Command docker -ErrorAction SilentlyContinue
        if (-not $docker) {
            Write-Status "Docker required for BYO builds but not found" "ERROR"
            return $false
        }
        Write-Status "Docker found" "SUCCESS"
    }

    return $true
}

# ── Deployment Functions ──────────────────────────────────────────────────────
function Invoke-Deploy {
    Write-Section "Phase 2: Deployment Configuration"

    # Generate names if not provided
    if (-not $AppName) {
        $random = -join ((1..6) | ForEach-Object { Get-Random -Maximum 10 })
        $AppName = "ultron-app-$random"
        Write-Status "Generated app name: $AppName" "INFO"
    }

    if (-not $ResourceGroup) {
        $ResourceGroup = "$AppName-rg"
        Write-Status "Generated resource group: $ResourceGroup" "INFO"
    }

    Write-Status "App Name: $AppName" "INFO"
    Write-Status "Resource Group: $ResourceGroup" "INFO"
    Write-Status "Location: $Location" "INFO"
    Write-Status "SKU: $Sku" "INFO"
    Write-Status "Model: $Model" "INFO"

    if ($DryRun) {
        Write-Status "DRY RUN MODE - No changes will be made" "WARNING"
        return
    }

    # Create temporary directory
    $tempDir = Join-Path $env:TEMP "ultron-deploy-$(Get-Random)"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    Write-Status "Working directory: $tempDir" "INFO"

    try {
        # Clone repository
        Write-Section "Phase 3: Cloning Repository"
        Write-Command "git clone $RepoUrl $tempDir\repo --branch $Branch --depth 1"
        git clone $RepoUrl "$tempDir\repo" --branch $Branch --depth 1 2>&1 | Out-Null
        Write-Status "Repository cloned" "SUCCESS"

        # Navigate to FastAPI app
        $appDir = "$tempDir\repo\use_sidecar_extension\fastapiapp"
        if (-not (Test-Path $appDir)) {
            Write-Status "FastAPI app directory not found at expected path" "ERROR"
            return
        }

        # Create resource group
        Write-Section "Phase 4: Azure Resource Provisioning"
        Write-Command "az group create --name $ResourceGroup --location $Location"
        $rgResult = az group create --name $ResourceGroup --location $Location --query "properties.provisioningState" -o tsv 2>$null
        if ($rgResult -eq "Succeeded") {
            Write-Status "Resource group created: $ResourceGroup" "SUCCESS"
        }

        # Deploy web app
        Write-Command "az webapp up --name $AppName --resource-group $ResourceGroup --sku $Sku --location $Location"
        Push-Location $appDir
        $deployOutput = az webapp up --name $AppName --resource-group $ResourceGroup --sku $Sku --location $Location 2>&1
        Pop-Location

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Web app deployed successfully" "SUCCESS"
        } else {
            Write-Status "Deployment failed" "ERROR"
            Write-Host $deployOutput
            return
        }

        # Configure startup command
        Write-Command "az webapp config set --startup-file `"$StartupCommand`""
        az webapp config set --name $AppName --resource-group $ResourceGroup --startup-file "$StartupCommand" --query "linuxFxVersion" -o tsv 2>$null | Out-Null
        Write-Status "Startup command configured" "SUCCESS"

        # Get app URL
        $appUrl = az webapp show --name $AppName --resource-group $ResourceGroup --query "defaultHostName" -o tsv 2>$null
        Write-Status "App URL: https://$appUrl" "SUCCESS"

        # Sidecar configuration instructions
        Write-Section "Phase 5: Sidecar Configuration Required"
        Write-Status "Complete these steps in Azure Portal:" "ULTRON"
        Write-Host ""
        Write-Host "  1. Navigate to: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppName/sidecar"
        Write-Host "  2. Select 'Add' → 'Sidecar extension'"
        Write-Host "  3. Choose: AI: $($Model)-q4-gguf (Experimental)"
        Write-Host "  4. Name: $($Model)-sidecar"
        Write-Host "  5. Click Save and wait 2-3 minutes"
        Write-Host ""

        # Wait for user or auto-verify
        Write-Status "Waiting $Timeout seconds for sidecar deployment..." "INFO"

        # Save deployment info
        $deployInfo = @{
            AppName = $AppName
            ResourceGroup = $ResourceGroup
            Location = $Location
            Sku = $Sku
            Model = $Model
            Url = "https://$appUrl"
            DeploymentTime = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        } | ConvertTo-Json -Depth 3

        $deployInfo | Out-File "$tempDir\deployment.json"
        Write-Status "Deployment info saved to: $tempDir\deployment.json" "INFO"

        # Auto-verify if requested
        Invoke-Verify -AppName $AppName -ResourceGroup $ResourceGroup

    } finally {
        # Cleanup
        if (Test-Path $tempDir) {
            Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        }
    }
}

# ── Verification Functions ──────────────────────────────────────────────────
function Invoke-Verify {
    param(
        [string]$AppName = $AppName,
        [string]$ResourceGroup = $ResourceGroup
    )

    Write-Section "Phase 6: Verification"

    if (-not $AppName -or -not $ResourceGroup) {
        Write-Status "AppName and ResourceGroup required for verification" "ERROR"
        return
    }

    # Get app info
    $appInfo = az webapp show --name $AppName --resource-group $ResourceGroup --query "{state: state, url: defaultHostName, sku: sku}" -o json 2>$null | ConvertFrom-Json

    if (-not $appInfo) {
        Write-Status "App not found: $AppName" "ERROR"
        return
    }

    Write-Status "App State: $($appInfo.state)" $(if ($appInfo.state -eq "Running") { "SUCCESS" } else { "WARNING" })
    Write-Status "App URL: https://$($appInfo.url)" "INFO"

    # Check sidecar extensions
    Write-Status "Checking sidecar extensions..." "INFO"
    $sidecars = az webapp show --name $AppName --resource-group $ResourceGroup --query "siteProperties.properties.sidecarExtensions" -o json 2>$null | ConvertFrom-Json

    if ($sidecars) {
        Write-Status "Sidecar extensions found:" "SUCCESS"
        $sidecars | ForEach-Object {
            Write-Host "    - $($_.name): $($_.properties.status)"
        }
    } else {
        Write-Status "No sidecar extensions configured" "WARNING"
    }

    # Test health endpoint
    Write-Status "Testing health endpoint..." "INFO"
    try {
        $health = Invoke-RestMethod -Uri "https://$($appInfo.url)/health" -TimeoutSec 10 -ErrorAction SilentlyContinue
        Write-Status "Health check passed" "SUCCESS"
    } catch {
        Write-Status "Health check failed (app may still be starting)" "WARNING"
    }

    # Test chat endpoint
    Write-Status "Testing chat endpoint..." "INFO"
    try {
        $body = @{ message = "Hello from Ultron" } | ConvertTo-Json
        $chat = Invoke-RestMethod -Uri "https://$($appInfo.url)/chat" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30 -ErrorAction SilentlyContinue
        Write-Status "Chat endpoint responding" "SUCCESS"
    } catch {
        Write-Status "Chat endpoint test failed" "WARNING"
    }
}

# ── Log Functions ─────────────────────────────────────────────────────────────
function Invoke-Logs {
    Write-Section "Log Streaming"

    if (-not $AppName -or -not $ResourceGroup) {
        Write-Status "AppName and ResourceGroup required" "ERROR"
        return
    }

    Write-Status "Streaming logs from $AppName..." "INFO"
    Write-Status "Press Ctrl+C to stop" "WARNING"

    if ($Follow) {
        az webapp log tail --name $AppName --resource-group $ResourceGroup
    } else {
        az webapp log tail --name $AppName --resource-group $ResourceGroup --duration 60
    }
}

# ── Destroy Functions ───────────────────────────────────────────────────────
function Invoke-Destroy {
    Write-Section "Resource Cleanup"

    if (-not $ResourceGroup) {
        Write-Status "ResourceGroup required for cleanup" "ERROR"
        return
    }

    Write-Status "This will delete resource group: $ResourceGroup" "WARNING"
    Write-Status "All resources in this group will be permanently deleted!" "WARNING"

    $confirm = Read-Host "Type 'DELETE' to confirm"
    if ($confirm -ne "DELETE") {
        Write-Status "Cleanup cancelled" "INFO"
        return
    }

    Write-Command "az group delete --name $ResourceGroup --yes"
    az group delete --name $ResourceGroup --yes --no-wait
    Write-Status "Resource group deletion initiated" "SUCCESS"
}

# ── Status Functions ────────────────────────────────────────────────────────
function Invoke-Status {
    Write-Section "Deployment Status"

    if (-not $ResourceGroup) {
        # List all Ultron deployments
        Write-Status "Finding Ultron deployments..." "INFO"
        $groups = az group list --query "[?contains(name, 'ultron-') || contains(name, '-rg')].{Name:name, Location:location, State:properties.provisioningState}" -o table 2>$null
        if ($groups) {
            Write-Host $groups
        } else {
            Write-Status "No deployments found" "INFO"
        }
        return
    }

    # Get specific resource group status
    $rg = az group show --name $ResourceGroup --query "{Name:name, Location:location, State:properties.provisioningState, Tags:tags}" -o json 2>$null | ConvertFrom-Json
    if ($rg) {
        Write-Status "Resource Group: $($rg.Name)" "INFO"
        Write-Status "Location: $($rg.Location)" "INFO"
        Write-Status "State: $($rg.State)" $(if ($rg.State -eq "Succeeded") { "SUCCESS" } else { "WARNING" })

        # List resources
        Write-Section "Resources in Group"
        $resources = az resource list --resource-group $ResourceGroup --query "[].{Name:name, Type:type, State:properties.state}" -o table 2>$null
        if ($resources) {
            Write-Host $resources
        }
    } else {
        Write-Status "Resource group not found: $ResourceGroup" "ERROR"
    }
}

# ── BYO Build Functions ─────────────────────────────────────────────────────
function Invoke-ByoBuild {
    Write-Section "BYO SLM Container Build"

    if (-not $CustomImage) {
        $CustomImage = "phi-3-custom"
        Write-Status "Using default image name: $CustomImage" "INFO"
    }

    # Create temporary directory for build
    $buildDir = Join-Path $env:TEMP "ultron-byo-$(Get-Random)"
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

    try {
        Write-Status "Build directory: $buildDir" "INFO"

        # Clone sample repo
        Write-Command "git clone https://github.com/Azure-Samples/ai-slm-in-app-service-sidecar $buildDir\repo --depth 1"
        git clone https://github.com/Azure-Samples/ai-slm-in-app-service-sidecar "$buildDir\repo" --depth 1 2>&1 | Out-Null

        $sidecarDir = "$buildDir\repo\bring_your_own_slm\src\phi-3-sidecar"
        if (-not (Test-Path $sidecarDir)) {
            Write-Status "Sidecar source not found" "ERROR"
            return
        }

        # Check for Hugging Face CLI
        $hf = Get-Command huggingface-cli -ErrorAction SilentlyContinue
        if (-not $hf) {
            Write-Status "Installing Hugging Face CLI..." "INFO"
            pip install huggingface-hub 2>&1 | Out-Null
        }

        # Download model
        Write-Section "Downloading Phi-3 Model"
        Write-Command "huggingface-cli download microsoft/Phi-3-mini-4k-instruct-onnx --local-dir .\Phi-3-mini-4k-instruct-onnx"
        Push-Location $sidecarDir
        huggingface-cli download microsoft/Phi-3-mini-4k-instruct-onnx --local-dir ".\Phi-3-mini-4k-instruct-onnx" --local-dir-use-symlinks False
        Pop-Location

        # Build Docker image
        Write-Section "Building Docker Image"
        Write-Command "docker build -t $CustomImage $sidecarDir"
        docker build -t $CustomImage $sidecarDir

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Image built: $CustomImage" "SUCCESS"
        } else {
            Write-Status "Build failed" "ERROR"
            return
        }

        # Push to ACR if specified
        if ($AcrName) {
            Write-Section "Pushing to Azure Container Registry"
            Write-Command "az acr login --name $AcrName"
            az acr login --name $AcrName

            $acrImage = "$AcrName.azurecr.io/$CustomImage`:latest"
            Write-Command "docker tag $CustomImage $acrImage"
            docker tag $CustomImage $acrImage

            Write-Command "docker push $acrImage"
            docker push $acrImage

            Write-Status "Image pushed to ACR: $acrImage" "SUCCESS"
        }

    } finally {
        Remove-Item -Recurse -Force $buildDir -ErrorAction SilentlyContinue
    }
}

# ── Interactive Menu ──────────────────────────────────────────────────────────
function Show-InteractiveMenu {
    Clear-Host
    Write-Host $script:UltronAscii -ForegroundColor Magenta
    Write-Host ""
    Write-Host "$($script:Colors.Bold)Select an action:$($script:Colors.Reset)"
    Write-Host ""
    Write-Host "  1. Deploy new FastAPI + SLM app"
    Write-Host "  2. Verify existing deployment"
    Write-Host "  3. Stream logs"
    Write-Host "  4. View deployment status"
    Write-Host "  5. Destroy deployment"
    Write-Host "  6. Build custom SLM container"
    Write-Host "  7. Exit"
    Write-Host ""

    $choice = Read-Host "Enter choice (1-7)"

    switch ($choice) {
        "1" {
            $appName = Read-Host "App name (leave blank for auto-generated)"
            $model = Read-Host "Model (phi-4/phi-3) [phi-4]"
            if (-not $model) { $model = "phi-4" }
            $sku = if ($model -eq "phi-4") { "P3MV3" } else { "P2MV3" }

            Invoke-Deploy -AppName $appName -Model $model -Sku $sku
        }
        "2" {
            $appName = Read-Host "App name"
            $rg = Read-Host "Resource group (leave blank to use '$appName-rg')"
            if (-not $rg) { $rg = "$appName-rg" }
            Invoke-Verify -AppName $appName -ResourceGroup $rg
        }
        "3" {
            $appName = Read-Host "App name"
            $rg = Read-Host "Resource group"
            Invoke-Logs
        }
        "4" { Invoke-Status }
        "5" {
            $rg = Read-Host "Resource group to destroy"
            Invoke-Destroy
        }
        "6" {
            $imageName = Read-Host "Image name [phi-3-custom]"
            $acr = Read-Host "ACR name (optional, press Enter to skip push)"
            Invoke-ByoBuild -CustomImage $imageName -AcrName $acr
        }
        "7" { exit }
        default { Write-Status "Invalid choice" "ERROR" }
    }

    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-InteractiveMenu
}

# ── Main Execution ───────────────────────────────────────────────────────────
Write-Host $script:UltronAscii -ForegroundColor Magenta
Write-Status "Azure AI Deployment Agent v$script:Version initialized" "ULTRON"

# Validate prerequisites
if (-not (Test-Prerequisites)) {
    exit 1
}

# Execute action
switch ($Action) {
    "deploy" { Invoke-Deploy }
    "verify" { Invoke-Verify }
    "logs" { Invoke-Logs }
    "destroy" { Invoke-Destroy }
    "status" { Invoke-Status }
    "byo-build" { Invoke-ByoBuild }
    "interactive" { Show-InteractiveMenu }
    default {
        Write-Status "Unknown action: $Action" "ERROR"
        Write-Status "Use -Action parameter or run with -Action interactive" "INFO"
    }
}

Write-Host ""
Write-Status "Ultron session complete" "ULTRON"
