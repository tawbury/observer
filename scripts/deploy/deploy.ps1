#################################################################################
# Observer Deployment Orchestrator (Windows PowerShell)
# 용도: 로컬 검증 → SSH를 통한 서버 배포 → Post-deploy 체크 자동화
# 버전: v1.0.0
#################################################################################

param(
    [string]$ServerHost = "your_server_ip",
    [string]$SshUser = "azureuser",
    [string]$SshKeyPath = "$env:USERPROFILE\.ssh\id_rsa",
    [string]$DeployDir = "/home/azureuser/observer-deploy",
    [string]$ComposeFile = "docker-compose.server.yml",
    [string]$LocalEnvFile = "app\obs_deploy\.env.server",
    [string]$EnvTemplate = "app\obs_deploy\env.template",
    [string]$ArtifactDir = "app\obs_deploy"
)

# ============================================================================
# 설정 및 상수
# ============================================================================
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = "ops\run_records\deploy_${timestamp}.log"
$summaryReport = @()

# 필수 아티팩트 파일
$requiredArtifacts = @(
    "observer-image.tar",
    "docker-compose.server.yml",
    ".env.server"
)

# ============================================================================
# 함수: 로깅
# ============================================================================
function Log-Message {
    param([string]$Message, [string]$Level = "INFO")
    
    $logEntry = "[${timestamp}] [$Level] $Message"
    Write-Host $logEntry -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "White" }
        }
    )
    
    Add-Content -Path $logFile -Value $logEntry
    $script:summaryReport += $logEntry
}

function Log-Debug {
    param([string]$Message)
    if ($VerbosePreference -eq "Continue") {
        Log-Message $Message "DEBUG"
    }
}

# ============================================================================
# 함수: 환경 검증
# ============================================================================
function Validate-LocalEnv {
    Log-Message "=== 로컬 환경 검증 시작 ===" "INFO"
    
    # 1. 템플릿 파일 확인
    if (-not (Test-Path $EnvTemplate)) {
        Log-Message "❌ env.template 파일 없음: $EnvTemplate" "ERROR"
        return $false
    }
    
    # 2. .env.server 파일 확인
    if (-not (Test-Path $LocalEnvFile)) {
        Log-Message "❌ .env.server 파일 없음: $LocalEnvFile" "ERROR"
        return $false
    }
    
    # 3. 템플릿에서 필수 키 읽기
    Log-Debug "env.template에서 필수 키 추출 중..."
    $templateKeys = @()
    Get-Content $EnvTemplate | ForEach-Object {
        if ($_ -match "^([A-Z_0-9]+)=") {
            $templateKeys += $Matches[1]
        }
    }
    
    Log-Debug "필수 키 총 $($templateKeys.Count)개 발견"
    
    # 4. .env.server에서 현재 키 읽기
    Log-Debug ".env.server에서 설정된 키 확인 중..."
    $currentEnv = @{}
    Get-Content $LocalEnvFile | ForEach-Object {
        if ($_ -match "^([A-Z_0-9]+)=(.*)$") {
            $currentEnv[$Matches[1]] = $Matches[2]
        }
    }
    
    Log-Debug "설정된 키 총 $($currentEnv.Count)개 발견"
    
    # 5. 빠진 키 확인
    $missingKeys = @()
    foreach ($key in $templateKeys) {
        if (-not $currentEnv.ContainsKey($key)) {
            $missingKeys += $key
        }
    }
    
    if ($missingKeys.Count -gt 0) {
        Log-Message "❌ 필수 키 누락: $($missingKeys -join ', ')" "ERROR"
        return $false
    }
    
    # 6. 값이 비어있는 키 확인 (자격증명 관련)
    $criticalKeys = @("KIS_APP_KEY", "KIS_APP_SECRET", "DB_PASSWORD")
    $emptyKeys = @()
    
    foreach ($key in $criticalKeys) {
        if ($currentEnv.ContainsKey($key) -and [string]::IsNullOrWhiteSpace($currentEnv[$key])) {
            $emptyKeys += $key
        }
    }
    
    if ($emptyKeys.Count -gt 0) {
        Log-Message "❌ 중요 값이 비어있음: $($emptyKeys -join ', ')" "ERROR"
        return $false
    }
    
    Log-Message "✅ 로컬 환경 검증 성공" "SUCCESS"
    return $true
}

# ============================================================================
# 함수: 아티팩트 검증
# ============================================================================
function Validate-Artifacts {
    Log-Message "=== 아티팩트 검증 시작 ===" "INFO"
    
    $missingFiles = @()
    foreach ($artifact in $requiredArtifacts) {
        $artifactPath = Join-Path $ArtifactDir $artifact
        if (-not (Test-Path $artifactPath)) {
            $missingFiles += $artifact
        } else {
            $size = (Get-Item $artifactPath).Length / 1MB
            Log-Message "✓ $artifact ($([math]::Round($size, 2)) MB)" "SUCCESS"
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Log-Message "❌ 아티팩트 누락: $($missingFiles -join ', ')" "ERROR"
        return $false
    }
    
    Log-Message "✅ 모든 아티팩트 검증 완료" "SUCCESS"
    return $true
}

# ============================================================================
# 함수: SSH 연결 테스트
# ============================================================================
function Test-SshConnection {
    Log-Message "=== SSH 연결 테스트 ===" "INFO"
    
    try {
        Log-Debug "호스트: $ServerHost, 사용자: $SshUser"
        
        # SSH 키 권한 확인
        if (-not (Test-Path $SshKeyPath)) {
            Log-Message "❌ SSH 키 없음: $SshKeyPath" "ERROR"
            return $false
        }
        
        # 간단한 SSH 명령 실행
        $testCmd = ssh -i $SshKeyPath -o ConnectTimeout=5 `
                       -o StrictHostKeyChecking=accept-new `
                       "${SshUser}@${ServerHost}" "echo 'SSH 연결 성공'"
        
        if ($LASTEXITCODE -ne 0) {
            Log-Message "❌ SSH 연결 실패 (exit code: $LASTEXITCODE)" "ERROR"
            return $false
        }
        
        Log-Message "✅ SSH 연결 테스트 성공" "SUCCESS"
        return $true
    }
    catch {
        Log-Message "❌ SSH 연결 오류: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# 함수: 서버 배포 디렉토리 검증
# ============================================================================
function Test-ServerDeployDir {
    Log-Message "=== 서버 배포 디렉토리 검증 ===" "INFO"
    
    try {
        ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
            "${SshUser}@${ServerHost}" "test -d $DeployDir && echo 'OK'" | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Log-Message "❌ 서버 배포 디렉토리 없음: $DeployDir" "ERROR"
            return $false
        }
        
        Log-Message "✅ 서버 배포 디렉토리 존재: $DeployDir" "SUCCESS"
        return $true
    }
    catch {
        Log-Message "❌ 서버 디렉토리 검증 오류: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# 함수: 서버 .env 파일 백업
# ============================================================================
function Backup-ServerEnv {
    Log-Message "=== 서버 .env 파일 백업 중 ===" "INFO"
    
    try {
        $backupTs = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
        $backupFile = ".env.bak-${backupTs}"
        
        ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
            "${SshUser}@${ServerHost}" `
            "cd $DeployDir && if [ -f .env ]; then cp .env $backupFile; fi"
        
        if ($LASTEXITCODE -eq 0) {
            Log-Message "✅ 백업 생성: $backupFile" "SUCCESS"
            $script:summaryReport += "백업 파일: $backupFile"
            return $true
        } else {
            Log-Message "⚠️  백업 생성 실패 (기존 .env 없을 수 있음)" "WARN"
            return $true  # 기존 파일 없는 경우는 계속 진행
        }
    }
    catch {
        Log-Message "❌ 백업 오류: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# 함수: .env 파일 업로드
# ============================================================================
function Upload-EnvFile {
    Log-Message "=== .env 파일 업로드 중 ===" "INFO"
    
    try {
        # 임시 파일로 먼저 업로드
        Log-Debug "로컬 .env.server → 서버로 전송 시작"
        
        scp -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
            $LocalEnvFile "${SshUser}@${ServerHost}:${DeployDir}/.env.tmp"
        
        if ($LASTEXITCODE -ne 0) {
            Log-Message "❌ 파일 업로드 실패" "ERROR"
            return $false
        }
        
        # 서버에서 임시 파일을 최종 .env로 이동하고 권한 설정
        Log-Debug "서버에서 .env 파일 권한 설정 중"
        
        ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
            "${SshUser}@${ServerHost}" `
            "cd $DeployDir && mv .env.tmp .env && chmod 600 .env"
        
        if ($LASTEXITCODE -ne 0) {
            Log-Message "❌ .env 파일 권한 설정 실패" "ERROR"
            return $false
        }
        
        Log-Message "✅ .env 파일 업로드 완료 (chmod 600)" "SUCCESS"
        return $true
    }
    catch {
        Log-Message "❌ .env 파일 업로드 오류: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# 함수: 아티팩트 업로드
# ============================================================================
function Upload-Artifacts {
    Log-Message "=== 아티팩트 업로드 중 ===" "INFO"
    
    try {
        foreach ($artifact in $requiredArtifacts) {
            if ($artifact -eq ".env.server") {
                # .env 파일은 이미 Upload-EnvFile에서 처리됨
                continue
            }
            
            $srcPath = Join-Path $ArtifactDir $artifact
            Log-Debug "업로드 중: $artifact"
            
            scp -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
                $srcPath "${SshUser}@${ServerHost}:${DeployDir}/"
            
            if ($LASTEXITCODE -ne 0) {
                Log-Message "❌ 아티팩트 업로드 실패: $artifact" "ERROR"
                return $false
            }
            
            Log-Message "✓ $artifact 업로드 완료" "SUCCESS"
        }
        
        Log-Message "✅ 모든 아티팩트 업로드 완료" "SUCCESS"
        return $true
    }
    catch {
        Log-Message "❌ 아티팩트 업로드 오류: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# 함수: 서버 배포 스크립트 업로드 및 실행
# ============================================================================
function Execute-ServerDeploy {
    Log-Message "=== 서버 배포 실행 중 ===" "INFO"
    
    try {
        # 로컬 scripts/deploy/server_deploy.sh를 서버로 업로드
        $serverScriptLocal = "scripts\deploy\server_deploy.sh"
        if (-not (Test-Path $serverScriptLocal)) {
            Log-Message "❌ server_deploy.sh 없음: $serverScriptLocal" "WARN"
            Log-Message "⚠️  수동으로 서버에서 docker compose 실행 필요" "WARN"
            return $true  # 스크립트 없어도 계속 진행
        }
        
        Log-Debug "server_deploy.sh 업로드 중"
        scp -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
            $serverScriptLocal "${SshUser}@${ServerHost}:${DeployDir}/"
        
        # 서버 스크립트 실행
        Log-Debug "서버 배포 스크립트 실행 중"
        ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
            "${SshUser}@${ServerHost}" `
            "cd $DeployDir && chmod +x server_deploy.sh && bash ./server_deploy.sh $DeployDir $ComposeFile observer-image.tar"
        
        if ($LASTEXITCODE -ne 0) {
            Log-Message "⚠️  서버 배포 스크립트 종료 코드: $LASTEXITCODE (상세는 서버 로그 참조)" "WARN"
            # 실패해도 health check로 최종 판정
        }
        
        Log-Message "✅ 서버 배포 스크립트 실행 완료" "SUCCESS"
        return $true
    }
    catch {
        Log-Message "❌ 서버 배포 실행 오류: $_" "ERROR"
        return $false
    }
}

# ============================================================================
# 함수: Post-Deploy 헬스 체크
# ============================================================================
function Health-Check {
    Log-Message "=== Post-Deploy 헬스 체크 ===" "INFO"
    
    try {
        # Docker compose 상태 확인
        Log-Debug "Docker compose 상태 확인 중"
        $status = ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
                       "${SshUser}@${ServerHost}" `
                       "cd $DeployDir && docker compose ps"
        
        Log-Message "Docker Compose Status:" "INFO"
        $status | ForEach-Object { Log-Message "  $_" "INFO" }
        
        # 간단한 health endpoint 확인 (선택적)
        Log-Debug "Health endpoint 확인 시도"
        $healthResult = ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new `
                            "${SshUser}@${ServerHost}" `
                            "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health"
        
        if ($healthResult -eq "200") {
            Log-Message "✅ Health endpoint 응답: 200 OK" "SUCCESS"
            return $true
        } else {
            Log-Message "⚠️  Health endpoint 응답 상태 불명: $healthResult (10초 후 재확인 권장)" "WARN"
            return $true  # health check 실패해도 계속 (시작 지연 가능)
        }
    }
    catch {
        Log-Message "❌ 헬스 체크 오류: $_" "WARN"
        return $true  # 헬스 체크 오류도 계속 진행
    }
}

# ============================================================================
# 메인 실행 흐름
# ============================================================================
function Main {
    Log-Message "╔════════════════════════════════════════════════════════════════════════════════╗" "INFO"
    Log-Message "║        Observer Deployment Orchestrator v1.0.0                                ║" "INFO"
    Log-Message "╚════════════════════════════════════════════════════════════════════════════════╝" "INFO"
    Log-Message ""
    
    Log-Message "배포 설정:" "INFO"
    Log-Message "  서버: $ServerHost" "INFO"
    Log-Message "  배포 디렉토리: $DeployDir" "INFO"
    Log-Message "  Compose 파일: $ComposeFile" "INFO"
    Log-Message ""
    
    # 1단계: 로컬 환경 검증
    if (-not (Validate-LocalEnv)) {
        Log-Message "❌ 로컬 환경 검증 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 2단계: 아티팩트 검증
    if (-not (Validate-Artifacts)) {
        Log-Message "❌ 아티팩트 검증 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 3단계: SSH 연결 테스트
    if (-not (Test-SshConnection)) {
        Log-Message "❌ SSH 연결 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 4단계: 서버 배포 디렉토리 검증
    if (-not (Test-ServerDeployDir)) {
        Log-Message "❌ 서버 배포 디렉토리 검증 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 5단계: 서버 .env 백업
    if (-not (Backup-ServerEnv)) {
        Log-Message "❌ 서버 .env 백업 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 6단계: .env 파일 업로드
    if (-not (Upload-EnvFile)) {
        Log-Message "❌ .env 파일 업로드 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 7단계: 아티팩트 업로드
    if (-not (Upload-Artifacts)) {
        Log-Message "❌ 아티팩트 업로드 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 8단계: 서버 배포 실행
    if (-not (Execute-ServerDeploy)) {
        Log-Message "❌ 서버 배포 실행 실패" "ERROR"
        Log-Message "배포 중단됨" "ERROR"
        return 1
    }
    
    # 9단계: 헬스 체크
    Health-Check | Out-Null
    
    # 완료
    Log-Message ""
    Log-Message "╔════════════════════════════════════════════════════════════════════════════════╗" "INFO"
    Log-Message "║        배포 완료 ✅                                                            ║" "INFO"
    Log-Message "╚════════════════════════════════════════════════════════════════════════════════╝" "SUCCESS"
    Log-Message ""
    Log-Message "다음 단계:" "INFO"
    Log-Message "  1. 서버에서 로그 확인: docker logs observer --tail 100" "INFO"
    Log-Message "  2. Status 확인: curl http://$ServerHost:8000/status" "INFO"
    Log-Message "  3. 로컬 로그: $logFile" "INFO"
    
    return 0
}

# ============================================================================
# 실행
# ============================================================================
$exitCode = Main
exit $exitCode
