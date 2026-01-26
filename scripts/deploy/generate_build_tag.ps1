# Observer Build Tag Generator (PowerShell)
# 용도: Docker 빌드 시점에 자동으로 타임스탬프 기반 태그 생성
# 형식: YYMMDD-HHMMSS (예: 20260126-155945)
# 버전: v1.0.0

param(
    [string]$OutputFile = ""
)

function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Log-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 태그 생성 함수
function New-BuildTag {
    # 현재 시간으로 타임스탬프 생성 (KST)
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    
    # YYMMDD-HHMMSS 형식으로 변환 (20YYMMDD-HHMMSS)
    $tag = "20$($timestamp.Substring(2,6))-$($timestamp.Substring(9,6))"
    
    return $tag
}

# 태그 검증 함수
function Test-BuildTag {
    param([string]$Tag)
    
    # 정규식 검증: 20YYMMDD-HHMMSS
    if ($Tag -notmatch '^20[0-9]{6}-[0-9]{6}$') {
        Log-Error "Invalid tag format: $Tag"
        Log-Error "Expected format: 20YYMMDD-HHMMSS (e.g., 20260126-155945)"
        return $false
    }
    
    # 날짜/시간 유효성 검증
    $datePart = $Tag.Substring(0, 8)
    $timePart = $Tag.Substring(9, 6)
    
    try {
        # 날짜 검증 (YYYYMMDD)
        $year = [int]$datePart.Substring(0, 4)
        $month = [int]$datePart.Substring(4, 2)
        $day = [int]$datePart.Substring(6, 2)
        
        $dateObj = Get-Date -Year $year -Month $month -Day $day -ErrorAction Stop
        
        # 시간 검증 (HHMMSS)
        $hour = [int]$timePart.Substring(0, 2)
        $minute = [int]$timePart.Substring(2, 2)
        $second = [int]$timePart.Substring(4, 2)
        
        if ($hour -gt 23 -or $minute -gt 59 -or $second -gt 59) {
            Log-Error "Invalid time: $timePart"
            return $false
        }
        
        return $true
    }
    catch {
        Log-Error "Invalid date/time: $Tag"
        Log-Error "Error: $($_.Exception.Message)"
        return $false
    }
}

# 메인 함수
function Main {
    Log-Info "=== Observer Build Tag Generator ==="
    
    # 태그 생성
    $tag = New-BuildTag
    Log-Info "Generated tag: $tag"
    
    # 태그 검증
    if (-not (Test-BuildTag -Tag $tag)) {
        Log-Error "Tag validation failed"
        exit 1
    }
    
    Log-Info "✅ Tag validation passed: $tag"
    
    # 출력 파일이 지정된 경우 파일에 저장
    if ($OutputFile -ne "") {
        $dir = Split-Path $OutputFile -Parent
        if ($dir -and -not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        $tag | Out-File -FilePath $OutputFile -Encoding UTF8 -NoNewline
        Log-Info "✅ Tag saved to: $OutputFile"
    }
    
    # 표준 출력으로 태그 출력 (다른 스크립트에서 사용)
    Write-Output $tag
    
    Log-Info "=== Tag Generation Complete ==="
}

# 스크립트 실행
Main
