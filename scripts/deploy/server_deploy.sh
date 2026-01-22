#!/bin/bash
################################################################################
# Observer Deployment Server Runner (Linux/Bash)
# 용도: 서버에서 Docker 이미지 로드, Compose 실행, 운영 체크
# 버전: v1.0.0
################################################################################

set -euo pipefail

# ============================================================================
# 설정 및 상수
# ============================================================================
DEPLOY_DIR="${1:-.}"
COMPOSE_FILE="${2:-docker-compose.server.yml}"
IMAGE_TAR="${3:-observer-image.tar}"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
HEALTH_ENDPOINT="http://localhost:8000/health"
MAX_RETRIES=5
RETRY_DELAY=3

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# 함수: 로깅
# ============================================================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo -e "[DEBUG] $1"
    fi
}

# ============================================================================
# 함수: 입력 검증
# ============================================================================
validate_inputs() {
    log_info "=== 입력 검증 시작 ==="
    
    # 배포 디렉토리 확인
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "배포 디렉토리 없음: $DEPLOY_DIR"
        return 1
    fi
    
    log_debug "배포 디렉토리: $DEPLOY_DIR"
    
    # Compose 파일 확인
    if [ ! -f "$DEPLOY_DIR/$COMPOSE_FILE" ]; then
        log_error "Compose 파일 없음: $DEPLOY_DIR/$COMPOSE_FILE"
        return 1
    fi
    
    log_debug "Compose 파일: $COMPOSE_FILE"
    
    # 이미지 TAR 파일 확인
    if [ ! -f "$DEPLOY_DIR/$IMAGE_TAR" ]; then
        log_warn "이미지 TAR 파일 없음: $DEPLOY_DIR/$IMAGE_TAR (기존 이미지 사용)"
    else
        log_debug "이미지 TAR 파일: $IMAGE_TAR"
    fi
    
    # .env 파일 확인
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        log_error ".env 파일 없음: $DEPLOY_DIR/.env"
        return 1
    fi
    
    log_debug ".env 파일 존재 확인됨"
    
    log_info "✅ 입력 검증 완료"
    return 0
}

# ============================================================================
# 함수: Docker 이미지 로드
# ============================================================================
load_docker_image() {
    log_info "=== Docker 이미지 로드 중 ==="
    
    if [ ! -f "$DEPLOY_DIR/$IMAGE_TAR" ]; then
        log_warn "이미지 TAR 없음, 스킵"
        return 0
    fi
    
    cd "$DEPLOY_DIR"
    log_debug "현재 디렉토리: $(pwd)"
    
    if docker load -i "$IMAGE_TAR"; then
        log_info "✅ Docker 이미지 로드 완료"
        return 0
    else
        log_error "Docker 이미지 로드 실패"
        return 1
    fi
}

# ============================================================================
# 함수: 필수 디렉토리 생성
# ============================================================================
create_required_directories() {
    log_info "=== 필수 디렉토리 생성 중 ==="
    
    cd "$DEPLOY_DIR"
    
    local required_dirs=(
        "data/observer"
        "data/postgres"
        "logs/system"
        "logs/maintenance"
        "config"
        "secrets"
    )
    
    for dir in "${required_dirs[@]}"; do
        if mkdir -p "$dir"; then
            log_debug "✓ $dir"
        else
            log_error "디렉토리 생성 실패: $dir"
            return 1
        fi
    done
    
    log_info "✅ 모든 필수 디렉토리 생성 완료"
    return 0
}

# ============================================================================
# 함수: Docker Compose 시작
# ============================================================================
start_compose_stack() {
    log_info "=== Docker Compose 스택 시작 중 ==="
    
    cd "$DEPLOY_DIR"
    
    log_debug "Compose 파일: $COMPOSE_FILE"
    
    if docker compose -f "$COMPOSE_FILE" up -d; then
        log_info "✅ Docker Compose 스택 시작 완료"
        log_info "⏳ PostgreSQL 헬스 체크 대기 중 (10초)..."
        sleep 10
        return 0
    else
        log_error "Docker Compose 시작 실패"
        return 1
    fi
}

# ============================================================================
# 함수: Docker Compose 상태 확인
# ============================================================================
check_compose_status() {
    log_info "=== Docker Compose 상태 확인 ==="
    
    cd "$DEPLOY_DIR"
    
    echo ""
    docker compose ps
    echo ""
    
    # 모든 서비스가 Up 상태인지 확인
    local down_count=$(docker compose ps --format "{{.Status}}" | grep -v "Up" | wc -l)
    
    if [ "$down_count" -gt 0 ]; then
        log_warn "⚠️  일부 서비스가 Up 상태가 아님 (다시 시작 중...)"
        docker compose restart
        sleep 5
        docker compose ps
    fi
    
    log_info "✅ Docker Compose 상태 확인 완료"
}

# ============================================================================
# 함수: 로그 확인 (초기 에러 감지)
# ============================================================================
check_initial_logs() {
    log_info "=== 초기 로그 확인 ==="
    
    cd "$DEPLOY_DIR"
    
    echo ""
    log_info "Observer 서비스 로그 (최근 100줄):"
    echo "─────────────────────────────────────────────────────────────────"
    docker compose logs --tail 100 observer || true
    echo "─────────────────────────────────────────────────────────────────"
    echo ""
    
    # 심각한 에러 감지 (선택적)
    if docker compose logs observer | grep -i "fatal\|critical error" > /dev/null 2>&1; then
        log_warn "⚠️  로그에서 심각한 에러 발견 (상세 로그 참조)"
    fi
    
    log_info "✅ 로그 확인 완료"
}

# ============================================================================
# 함수: Health Endpoint 확인
# ============================================================================
check_health_endpoint() {
    log_info "=== Health Endpoint 확인 ==="
    
    log_debug "대상: $HEALTH_ENDPOINT"
    
    local attempt=1
    while [ $attempt -le $MAX_RETRIES ]; do
        log_debug "시도 $attempt/$MAX_RETRIES..."
        
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")
        
        if [ "$http_code" = "200" ]; then
            log_info "✅ Health endpoint 응답: 200 OK"
            return 0
        else
            log_debug "응답 코드: $http_code (재시도 대기 중...)"
            sleep $RETRY_DELAY
            attempt=$((attempt + 1))
        fi
    done
    
    log_warn "⚠️  Health endpoint 응답 없음 (시작 지연 가능)"
    return 0  # 실패해도 계속 진행
}

# ============================================================================
# 함수: 최종 운영 체크
# ============================================================================
operational_summary() {
    log_info "=== 최종 운영 체크 ==="
    
    cd "$DEPLOY_DIR"
    
    echo ""
    log_info "📊 최종 상태:"
    echo "─────────────────────────────────────────────────────────────────"
    
    # 1. Compose 상태
    local total=$(docker compose ps --format "table" | tail -n +2 | wc -l)
    local running=$(docker compose ps --format "{{.Status}}" | grep "Up" | wc -l)
    log_info "  · Docker Compose: $running/$total 서비스 실행 중"
    
    # 2. 이미지 정보
    local image=$(docker compose ps --format "{{.Image}}" | head -1)
    if [ ! -z "$image" ]; then
        log_info "  · Observer 이미지: $image"
    fi
    
    # 3. 포트 확인
    if docker compose ps observer | grep -q "8000"; then
        log_info "  · API 포트: 8000 바인딩됨"
    fi
    
    # 4. 데이터 디렉토리
    if [ -d "data/observer" ]; then
        log_info "  · 데이터 디렉토리: 준비 완료"
    fi
    
    echo "─────────────────────────────────────────────────────────────────"
    echo ""
    
    log_info "✅ 운영 체크 완료"
}

# ============================================================================
# 메인 실행 흐름
# ============================================================================
main() {
    echo ""
    log_info "╔═════════════════════════════════════════════════════════════════════════════════╗"
    log_info "║        Observer Deployment Server Runner v1.0.0                                ║"
    log_info "╚═════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "배포 설정:"
    log_info "  · 배포 디렉토리: $DEPLOY_DIR"
    log_info "  · Compose 파일: $COMPOSE_FILE"
    log_info "  · 이미지 TAR: $IMAGE_TAR"
    echo ""
    
    # 1단계: 입력 검증
    if ! validate_inputs; then
        log_error "입력 검증 실패"
        return 1
    fi
    
    # 2단계: Docker 이미지 로드
    if ! load_docker_image; then
        log_error "Docker 이미지 로드 실패"
        return 1
    fi
    
    # 3단계: 필수 디렉토리 생성
    if ! create_required_directories; then
        log_error "필수 디렉토리 생성 실패"
        return 1
    fi
    
    # 4단계: Docker Compose 시작
    if ! start_compose_stack; then
        log_error "Docker Compose 스택 시작 실패"
        return 1
    fi
    
    # 5단계: 상태 확인
    check_compose_status || true
    
    # 6단계: 로그 확인
    check_initial_logs || true
    
    # 7단계: Health Endpoint 확인
    check_health_endpoint || true
    
    # 8단계: 최종 운영 체크
    operational_summary || true
    
    # 완료
    echo ""
    log_info "╔═════════════════════════════════════════════════════════════════════════════════╗"
    log_info "║        배포 완료 ✅                                                              ║"
    log_info "╚═════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "다음 단계:"
    log_info "  1. 서버 .env 확인: cat $DEPLOY_DIR/.env | grep -v '^$' | wc -l"
    log_info "  2. 로그 모니터링: docker compose logs -f observer"
    log_info "  3. Status 엔드포인트: curl http://localhost:8000/status"
    echo ""
    
    return 0
}

# ============================================================================
# 실행
# ============================================================================
if main; then
    exit 0
else
    exit 1
fi
