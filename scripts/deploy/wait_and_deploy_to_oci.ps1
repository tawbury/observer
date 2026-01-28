################################################################################
# Wait for GitHub Actions Build and Deploy to OCI
# Monitors build completion and automatically deploys when ready
################################################################################

param(
    [string]$WorkflowRunId = "21403674206",
    [string]$ImageTag = "20260127-154214",
    [string]$ServerHost = "134.185.117.22",
    [string]$SshUser = "ubuntu",
    [string]$SshKeyPath = "C:\Users\tawbu\.ssh\oracle-obs-vm-01.key",
    [string]$DeployDir = "/home/ubuntu/observer-deploy",
    [string]$Repository = "tawbury/observer",
    [int]$MaxRetries = 60,
    [int]$RetryIntervalSeconds = 10
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = "ops\run_records\wait_deploy_${timestamp}.log"

# Ensure log directory exists
$logDir = Split-Path $logFile
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Log-Message {
    param([string]$Message, [string]$Level = "INFO")
    $logEntry = "[${timestamp}] [$Level] $Message"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    Write-Host $logEntry -ForegroundColor $color
    Add-Content -Path $logFile -Value $logEntry
}

# ============================================================================
# Phase 1: Wait for Build Completion
# ============================================================================
Log-Message "==== Wait and Deploy Orchestrator ====" "INFO"
Log-Message "Workflow Run ID: $WorkflowRunId" "INFO"
Log-Message "Image Tag: $ImageTag" "INFO"
Log-Message "Target Server: $ServerHost" "INFO"
Log-Message "Max Retries: $MaxRetries (${MaxRetries*$RetryIntervalSeconds}s max wait)" "INFO"
Log-Message ""
Log-Message "[PHASE 1] Waiting for GitHub Actions build completion..." "INFO"

$retryCount = 0
$buildComplete = $false
$buildSuccess = $false

while ($retryCount -lt $MaxRetries -and -not $buildComplete) {
    try {
        $status = gh run view $WorkflowRunId --json status,conclusion --repo $Repository | ConvertFrom-Json
        
        if ($status.status -eq "completed") {
            Log-Message "Build completed!" "SUCCESS"
            $buildComplete = $true
            
            if ($status.conclusion -eq "success") {
                Log-Message "Build conclusion: SUCCESS ✓" "SUCCESS"
                $buildSuccess = $true
            } else {
                Log-Message "Build conclusion: $($status.conclusion) ✗" "ERROR"
                $buildSuccess = $false
            }
        } else {
            $elapsedSeconds = $retryCount * $RetryIntervalSeconds
            Log-Message "[${elapsedSeconds}s] Build in progress... (retry $($retryCount + 1)/$MaxRetries)" "INFO"
        }
    } catch {
        Log-Message "Error checking build status: $_" "WARN"
    }
    
    if (-not $buildComplete) {
        Start-Sleep -Seconds $RetryIntervalSeconds
    }
    
    $retryCount++
}

if (-not $buildComplete) {
    Log-Message "Build did not complete within timeout (${MaxRetries*$RetryIntervalSeconds}s)" "ERROR"
    exit 1
}

if (-not $buildSuccess) {
    Log-Message "Build failed, cannot proceed with deployment" "ERROR"
    exit 1
}

Log-Message ""
Log-Message "[PHASE 2] Deploying to OCI..." "INFO"

# ============================================================================
# Phase 2: Deploy to OCI
# ============================================================================

$deployScript = ".\scripts\deploy\deploy.ps1"

if (-not (Test-Path $deployScript)) {
    Log-Message "Deploy script not found: $deployScript" "ERROR"
    exit 1
}

Log-Message "Executing deployment with image tag: $ImageTag" "INFO"

try {
    & $deployScript `
        -ServerHost $ServerHost `
        -SshUser $SshUser `
        -SshKeyPath $SshKeyPath `
        -DeployDir $DeployDir `
        -ImageTag $ImageTag
    
    Log-Message ""
    Log-Message "Deployment completed!" "SUCCESS"
    Log-Message "Log file: $logFile" "INFO"
} catch {
    Log-Message "Deployment failed: $_" "ERROR"
    Log-Message "Log file: $logFile" "INFO"
    exit 1
}
