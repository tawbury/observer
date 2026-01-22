param(
    [string]$ServerHost = "your_server_ip",
    [string]$SshUser = "azureuser",
    [string]$SshKeyPath = "$env:USERPROFILE\.ssh\id_rsa",
    [string]$DeployDir = "/home/azureuser/observer-deploy",
    [string]$LocalEnvFile = "app\obs_deploy\.env.server"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "Observer Env Deployment Script v1.0" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Server: $ServerHost"
Write-Host "  User: $SshUser"
Write-Host "  Deploy Dir: $DeployDir"
Write-Host ""

# 1. 로컬 파일 확인
if (-not (Test-Path $LocalEnvFile)) {
    Write-Host "ERROR: .env.server file not found: $LocalEnvFile" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] .env.server file found" -ForegroundColor Green

# 2. SSH 키 확인
if (-not (Test-Path $SshKeyPath)) {
    Write-Host "ERROR: SSH key not found: $SshKeyPath" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] SSH key found" -ForegroundColor Green

# 3. SSH 연결 테스트
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
$testResult = ssh -i $SshKeyPath -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new `
    "$SshUser@$ServerHost" "echo OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: SSH connection failed" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}
Write-Host "[OK] SSH connection successful" -ForegroundColor Green

# 4. 배포 디렉토리 확인
Write-Host "Checking server deploy directory..." -ForegroundColor Yellow
ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
    "$SshUser@$ServerHost" "test -d $DeployDir" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deploy directory not found: $DeployDir" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Deploy directory exists" -ForegroundColor Green

# 5. 기존 .env 백업
Write-Host "Backing up existing .env file..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
    "$SshUser@$ServerHost" `
    "cd $DeployDir; if [ -f .env ]; then cp .env .env.bak-$timestamp; fi" 2>&1
Write-Host "[OK] Backup created (.env.bak-$timestamp)" -ForegroundColor Green

# 6. .env 파일 업로드
Write-Host "Uploading .env.server to server..." -ForegroundColor Yellow
scp -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
    $LocalEnvFile "$SshUser@$ServerHost`:$DeployDir/.env.tmp" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Upload failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] File uploaded successfully" -ForegroundColor Green

# 7. 서버에서 파일 이동 및 권한 설정
Write-Host "Finalizing .env file on server..." -ForegroundColor Yellow
ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
    "$SshUser@$ServerHost" `
    "cd $DeployDir; mv .env.tmp .env; chmod 600 .env" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: File finalization failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] .env file is ready (chmod 600)" -ForegroundColor Green

# 8. 최종 확인
Write-Host "Verifying .env file..." -ForegroundColor Yellow
ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
    "$SshUser@$ServerHost" `
    "cd $DeployDir; ls -la .env; echo '---'; wc -l .env" 2>&1
Write-Host "[OK] .env file verified" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review server .env: ssh $SshUser@$ServerHost 'cat $DeployDir/.env'"
Write-Host "  2. Restart services: docker compose -f $DeployDir/docker-compose.server.yml restart observer"
Write-Host "  3. Check logs: docker logs observer --tail 50"
Write-Host ""

exit 0
