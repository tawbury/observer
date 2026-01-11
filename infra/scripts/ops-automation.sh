#!/bin/bash
# QTS Observer 운영 자동화 스크립트

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/.backups"
LOG_DIR="$PROJECT_ROOT/app/ops_deploy/logs"

# 컬러 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. 정기적인 백업
backup() {
  log "📦 백업 시작..."
  
  mkdir -p "$BACKUP_DIR"
  
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_FILE="$BACKUP_DIR/qts_ops_backup_$TIMESTAMP.tar.gz"
  
  # 데이터 및 로그 백업
  tar -czf "$BACKUP_FILE" \
    -C "$PROJECT_ROOT/app/ops_deploy" \
    data/ logs/ config/ || error "백업 실패"
  
  log "✅ 백업 완료: $BACKUP_FILE"
  
  # 오래된 백업 삭제 (30일 이상)
  find "$BACKUP_DIR" -name "qts_ops_backup_*.tar.gz" -mtime +30 -delete || warn "오래된 백업 삭제 실패"
}

# 2. 로그 로테이션
rotate_logs() {
  log "🔄 로그 로테이션 시작..."
  
  if [ ! -d "$LOG_DIR" ]; then
    warn "로그 디렉토리가 없습니다: $LOG_DIR"
    return
  fi
  
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  
  # 현재 로그를 압축
  for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
      gzip -c "$log_file" > "$log_file.$TIMESTAMP.gz" || warn "로그 압축 실패: $log_file"
      > "$log_file"  # 로그 파일 비우기
    fi
  done
  
  log "✅ 로그 로테이션 완료"
  
  # 30일 이상 된 압축 로그 삭제
  find "$LOG_DIR" -name "*.gz" -mtime +30 -delete || warn "오래된 압축 로그 삭제 실패"
}

# 3. 리소스 정리 (불필요한 Docker 이미지, 컨테이너 정리)
cleanup_resources() {
  log "🧹 리소스 정리 시작..."
  
  # 종료된 컨테이너 제거
  docker container prune -f --filter "until=72h" || warn "컨테이너 정리 실패"
  
  # 사용하지 않는 이미지 제거
  docker image prune -f --filter "until=72h" || warn "이미지 정리 실패"
  
  # 사용하지 않는 볼륨 제거
  docker volume prune -f || warn "볼륨 정리 실패"
  
  # __pycache__ 정리
  find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + || warn "__pycache__ 정리 실패"
  
  # 일시적 파일 정리
  find "$PROJECT_ROOT" -type f -name "*.pyc" -delete || warn "*.pyc 정리 실패"
  find "$PROJECT_ROOT" -type f -name "*.pyo" -delete || warn "*.pyo 정리 실패"
  
  log "✅ 리소스 정리 완료"
}

# 4. 보안 패치 및 업데이트
security_update() {
  log "🔒 보안 패치 및 업데이트 시작..."
  
  # Python 패키지 업데이트 체크
  cd "$PROJECT_ROOT/app/ops_deploy"
  
  if [ -f "requirements.txt" ]; then
    log "업데이트 가능한 패키지 확인 중..."
    pip list --outdated || warn "패키지 확인 실패"
  fi
  
  # Docker 이미지 업데이트 (base image)
  log "Docker base image 업데이트 체크..."
  docker pull python:3.11-slim || warn "Python 이미지 업데이트 실패"
  
  log "✅ 보안 업데이트 확인 완료"
}

# 5. 시스템 헬스 체크
health_check() {
  log "🏥 시스템 헬스 체크 시작..."
  
  # 디스크 사용량 확인
  DISK_USAGE=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
  if [ "$DISK_USAGE" -gt 80 ]; then
    error "디스크 사용량 높음: ${DISK_USAGE}%"
  else
    log "✅ 디스크 사용량: ${DISK_USAGE}%"
  fi
  
  # 컨테이너 상태 확인
  if docker ps | grep -q "qts-observer"; then
    log "✅ 컨테이너 실행 중"
  else
    warn "컨테이너가 실행 중이지 않습니다"
  fi
  
  # 메모리 사용량 확인
  if docker ps -q --filter "name=qts-observer" > /dev/null; then
    MEMORY=$(docker stats --no-stream qts-observer | tail -1 | awk '{print $3}')
    log "✅ 메모리 사용량: $MEMORY"
  fi
}

# 6. 비용 최적화 리포트
cost_report() {
  log "💰 비용 최적화 리포트 생성..."
  
  # 생성 시간
  REPORT_FILE="$PROJECT_ROOT/docs/report/cost_report_$(date +%Y%m%d).md"
  mkdir -p "$(dirname "$REPORT_FILE")"
  
  cat > "$REPORT_FILE" << EOF

# 비용 최적화 리포트 ($(date +'%Y-%m-%d %H:%M:%S'))

## 리소스 사용량

### 스토리지
- 백업 크기: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
- 로그 크기: $(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
- 데이터 크기: $(du -sh "$PROJECT_ROOT/app/ops_deploy/data" 2>/dev/null | cut -f1)

### Docker
- 이미지 수: $(docker images -q | wc -l)
- 컨테이너 수: $(docker ps -a -q | wc -l)
- 총 크기: $(docker system df | grep -i "total" | tail -1)

## 최적화 권장사항

1. 오래된 백업 자동 삭제 (현재: 30일)
2. 이미지 캐싱 최적화
3. 로그 보관 정책 수립
4. 리소스 태깅으로 비용 추적

---
생성일: $(date +'%Y-%m-%d %H:%M:%S')
EOF
  
  log "✅ 리포트 생성 완료: $REPORT_FILE"
}

# 메인 함수
main() {
  local task=${1:-all}
  
  case $task in
    backup)
      backup
      ;;
    rotate_logs)
      rotate_logs
      ;;
    cleanup)
      cleanup_resources
      ;;
    security_update)
      security_update
      ;;
    health_check)
      health_check
      ;;
    cost_report)
      cost_report
      ;;
    all)
      backup
      rotate_logs
      cleanup_resources
      security_update
      health_check
      cost_report
      ;;
    *)
      echo "사용법: $0 {backup|rotate_logs|cleanup|security_update|health_check|cost_report|all}"
      echo ""
      echo "tasks:"
      echo "  backup          - 데이터 백업"
      echo "  rotate_logs     - 로그 로테이션"
      echo "  cleanup         - 리소스 정리"
      echo "  security_update - 보안 업데이트"
      echo "  health_check    - 헬스 체크"
      echo "  cost_report     - 비용 리포트"
      echo "  all             - 모든 작업 수행"
      exit 1
      ;;
  esac
}

main "$@"
