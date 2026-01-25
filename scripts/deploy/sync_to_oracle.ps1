# Sync local workspace (infra + app) to Oracle VM and run docker compose
# Usage: pwsh -File scripts/deploy/sync_to_oracle.ps1

param(
  [string]$HostName = "10.0.0.12",
  [string]$User = "opc",
  [string]$KeyPath = "C:\Users\tawbu\.oci\oci_api_key.pem",
  [string]$RemoteBase = "~/workspace",
  [string]$SudoPassword = ""
)

function Log($msg) { Write-Host "[sync] $msg" }
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

# Ensure required tools
$required = @("ssh","scp")
foreach ($cmd in $required) {
  $exists = (Get-Command $cmd -ErrorAction SilentlyContinue)
  if (-not $exists) { throw "Required command not found: $cmd" }
}

$workspace = (Get-Location).Path
$infra = Join-Path $workspace "infra"
$app = Join-Path $workspace "app"
$scripts = Join-Path $workspace "scripts"

if (-not (Test-Path $infra)) { throw "infra folder not found: $infra" }
if (-not (Test-Path $app)) { throw "app folder not found: $app" }
if (-not (Test-Path $scripts)) { throw "scripts folder not found: $scripts" }

Log "Creating remote base directory: $RemoteBase"
ssh -i $KeyPath "${User}@${HostName}" "mkdir -p $RemoteBase" | Out-Null

Log "Copying infra/"
scp -i $KeyPath -r "$infra" "${User}@${HostName}:${RemoteBase}/" | Out-Null

Log "Copying app/"
scp -i $KeyPath -r "$app" "${User}@${HostName}:${RemoteBase}/" | Out-Null

Log "Copying scripts/"
scp -i $KeyPath -r "$scripts" "${User}@${HostName}:${RemoteBase}/" | Out-Null

Log "Verifying remote compose path"
$composePath = "$RemoteBase/infra/docker/compose/docker-compose.yml"
ssh -i $KeyPath "${User}@${HostName}" "test -f $composePath && echo OK || echo MISSING"

Log "Checking Docker/Compose availability"
$dockerCheck = ssh -i $KeyPath "${User}@${HostName}" "command -v docker >/dev/null && echo DOCKER_OK || echo DOCKER_MISSING"
Write-Host $dockerCheck
$composeCheck = ssh -i $KeyPath "${User}@${HostName}" "docker compose version >/dev/null 2>&1 && echo COMPOSE_OK || echo COMPOSE_MISSING"
Write-Host $composeCheck

if ($dockerCheck -match 'MISSING' -or $composeCheck -match 'MISSING') {
  Log "Bootstrapping Docker on server"
  if ([string]::IsNullOrEmpty($SudoPassword)) {
    Write-Warning "Sudo password not provided; attempting non-interactive install (may fail)."
    ssh -i $KeyPath "${User}@${HostName}" "SUDO_PASSWORD='' bash $RemoteBase/scripts/deploy/oracle_bootstrap.sh" | Write-Host
  } else {
    ssh -i $KeyPath "${User}@${HostName}" "SUDO_PASSWORD='$SudoPassword' bash $RemoteBase/scripts/deploy/oracle_bootstrap.sh" | Write-Host
  }
}

Log "Running docker compose up (build)"
ssh -i $KeyPath "${User}@${HostName}" "cd $RemoteBase; docker compose -f infra/docker/compose/docker-compose.yml up -d --build"

Log "Comparing compose file hashes (local vs remote)"
$localHash = (Get-FileHash "$workspace/infra/docker/compose/docker-compose.yml" -Algorithm SHA256).Hash
Write-Host "[sync] Local SHA256: $localHash"

# Try sha256sum, fallback to openssl
$remoteHash = ssh -i $KeyPath "${User}@${HostName}" "sha256sum $composePath | awk '{print \`$1}'" 2>$null
Write-Host "[sync] Remote SHA256: $remoteHash"
if ($localHash -eq $remoteHash) {
  Write-Host "[sync] Hash match: server compose equals local"
} else {
  Write-Warning "[sync] Hash mismatch: server compose differs from local"
}