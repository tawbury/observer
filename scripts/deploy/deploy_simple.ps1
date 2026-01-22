param(
    [string]$ServerHost = "your_server_ip",
    [string]$SshUser = "azureuser",
    [string]$SshKeyPath = "$env:USERPROFILE\.ssh\id_rsa",
    [string]$DeployDir = "/home/azureuser/observer-deploy",
    [string]$LocalEnvFile = "app\obs_deploy\.env.server"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "Observer Env Deployment Script (wrapper)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "This script now delegates to deploy.ps1 with EnvOnly mode." -ForegroundColor Yellow
Write-Host ""

$deployScript = Join-Path $PSScriptRoot "deploy.ps1"
if (-not (Test-Path $deployScript)) {
    Write-Host "ERROR: deploy.ps1 not found at $deployScript" -ForegroundColor Red
    exit 1
}

$argsList = @(
    "-NoProfile",
    "-File", $deployScript,
    "-ServerHost", $ServerHost,
    "-SshUser", $SshUser,
    "-SshKeyPath", $SshKeyPath,
    "-DeployDir", $DeployDir,
    "-LocalEnvFile", $LocalEnvFile,
    "-EnvOnly"
)

$null = & powershell @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
exit 0
