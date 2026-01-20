# Deploy to Azure VM Script
# Phase 2 서버 배포 자동화

param(
    [string]$VMName = "observer-vm-01",
    [string]$ResourceGroup = "RG-OBSERVER-TEST"
)

Write-Host "🚀 Phase 2: VM 배포 시작" -ForegroundColor Green

# 1. 압축 파일 생성
Write-Host "📦 배포 패키지 생성 중..." -ForegroundColor Yellow
$sourcePath = "app\obs_deploy"
$tarFile = "obs_deploy.tar.gz"

if (Test-Path $tarFile) {
    Remove-Item $tarFile -Force
}

tar -czf $tarFile -C app obs_deploy
Write-Host "✅ 압축 파일 생성 완료: $tarFile" -ForegroundColor Green

# 2. VM에 디렉토리 생성
Write-Host "📁 VM에 디렉토리 생성 중..." -ForegroundColor Yellow
az vm run-command invoke `
    --resource-group $ResourceGroup `
    --name $VMName `
    --command-id RunShellScript `
    --scripts "mkdir -p ~/app && cd ~/app && pwd"

# 3. 파일 업로드 안내
Write-Host ""
Write-Host "📤 다음 단계를 수동으로 진행하세요:" -ForegroundColor Cyan
Write-Host "1. Azure Portal에서 VM 접속 (Bastion 또는 SSH)" -ForegroundColor White
Write-Host "2. 로컬 파일 $tarFile 을 VM의 ~/app/ 에 업로드" -ForegroundColor White
Write-Host "3. VM에서 다음 명령어 실행:" -ForegroundColor White
Write-Host ""
Write-Host "   cd ~/app" -ForegroundColor Yellow
Write-Host "   tar -xzf obs_deploy.tar.gz" -ForegroundColor Yellow
Write-Host "   cd obs_deploy" -ForegroundColor Yellow
Write-Host "   cp env.template .env" -ForegroundColor Yellow
Write-Host "   nano .env  # KIS API 키 입력" -ForegroundColor Yellow
Write-Host "   mkdir -p data logs config/observer" -ForegroundColor Yellow
Write-Host "   docker-compose build" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Yellow
Write-Host "   docker ps" -ForegroundColor Yellow
Write-Host "   docker logs -f observer-prod" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ 배포 준비 완료!" -ForegroundColor Green
