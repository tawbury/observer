#!/bin/bash
################################################################################
# oracle-obs-vm-01 서버 상태 점검
# 1. 아카이브(백업 TAR) 생성 여부
# 2. DB 생성/마이그레이션 여부
# 3. 실행 로그 생성 여부
################################################################################

set -euo pipefail

DEPLOY_DIR="${1:-/home/ubuntu/observer-deploy}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

cd "$DEPLOY_DIR" 2>/dev/null || { fail "배포 디렉토리 없음: $DEPLOY_DIR"; exit 1; }

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  oracle-obs-vm-01 서버 점검 — $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "  배포 디렉토리: $DEPLOY_DIR"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ---------------------------------------------------------------------------
# 1. 아카이브 파일 (backups/archives)
# ---------------------------------------------------------------------------
echo "▶ 1. 아카이브 파일 (backups/archives)"
echo "─────────────────────────────────────────────────────────────────"
ARCHIVE_DIR="$DEPLOY_DIR/backups/archives"
if [ ! -d "$ARCHIVE_DIR" ]; then
    fail "디렉토리 없음: $ARCHIVE_DIR"
else
    ok "디렉토리 존재: $ARCHIVE_DIR"
    count=$(find "$ARCHIVE_DIR" -maxdepth 1 -name "observer-image_*.tar" 2>/dev/null | wc -l)
    if [ "$count" -eq 0 ]; then
        warn "TAR 아카이브 0개 (배포 후 최초 1회 생성됨)"
    else
        ok "TAR 아카이브 ${count}개"
        ls -la "$ARCHIVE_DIR"/observer-image_*.tar 2>/dev/null | head -5
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# 2. DB 생성 및 마이그레이션
# ---------------------------------------------------------------------------
echo "▶ 2. DB 생성 / 마이그레이션"
echo "─────────────────────────────────────────────────────────────────"
if ! docker exec observer-postgres pg_isready -U postgres -d observer >/dev/null 2>&1; then
    fail "PostgreSQL 준비 안 됨 (observer-postgres 컨테이너 확인)"
else
    ok "PostgreSQL ready (observer DB)"
fi

migration_out=$(docker exec observer-postgres psql -U postgres -d observer -t -A -c "SELECT migration_name, status FROM migration_log ORDER BY applied_at;" 2>&1) || true
if echo "$migration_out" | grep -qE "ERROR|relation.*does not exist"; then
    fail "migration_log 조회 실패 (마이그레이션 미적용 가능): $migration_out"
elif [ -z "$migration_out" ] || [ "$(echo "$migration_out" | tr -d ' \n')" = "" ]; then
    warn "migration_log 비어 있음 (마이그레이션 미실행)"
else
    ok "마이그레이션 로그:"
    echo "$migration_out" | while read -r line; do
        [ -n "$line" ] && echo "    $line"
    done
fi

# 테이블 존재 여부
tables=$(docker exec observer-postgres psql -U postgres -d observer -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null | tr -d ' \r\n') || echo "0"
if [ -n "$tables" ] && [ "$tables" -gt 0 ]; then
    ok "public 스키마 테이블 ${tables}개"
else
    warn "public 스키마 테이블 없음"
fi
echo ""

# ---------------------------------------------------------------------------
# 3. 실행 로그 (logs/system, logs/maintenance)
# ---------------------------------------------------------------------------
echo "▶ 3. 실행 로그 (logs/system, logs/maintenance)"
echo "─────────────────────────────────────────────────────────────────"
for subdir in system maintenance; do
    dir="$DEPLOY_DIR/logs/$subdir"
    if [ ! -d "$dir" ]; then
        warn "디렉토리 없음: $dir"
    else
        ok "디렉토리 존재: $dir"
        n=$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l)
        if [ "$n" -eq 0 ]; then
            warn "  로그 파일 0개"
        else
            ok "  로그 파일 ${n}개"
            ls -la "$dir" 2>/dev/null | tail -n +2 | head -8
        fi
    fi
done

# 호스트 로그 비어 있으면 컨테이너 내부 확인
host_log_count=0
[ -d "$DEPLOY_DIR/logs/system" ] && host_log_count=$((host_log_count + $(find "$DEPLOY_DIR/logs/system" -maxdepth 1 -type f 2>/dev/null | wc -l)))
[ -d "$DEPLOY_DIR/logs/maintenance" ] && host_log_count=$((host_log_count + $(find "$DEPLOY_DIR/logs/maintenance" -maxdepth 1 -type f 2>/dev/null | wc -l)))
if [ "$host_log_count" -eq 0 ] && docker exec observer test -d /app/logs/system 2>/dev/null; then
    cont_count=$(docker exec observer find /app/logs/system /app/logs/maintenance -maxdepth 1 -type f 2>/dev/null | wc -l)
    if [ "$cont_count" -gt 0 ]; then
        warn "호스트 logs 비어 있으나 컨테이너 내 /app/logs 에 ${cont_count}개 파일 있음 (볼륨 마운트 확인 필요)"
        docker exec observer ls -la /app/logs/system /app/logs/maintenance 2>/dev/null | head -20
    fi
fi

# Docker 로그 (observer) 마지막 몇 줄
echo ""
echo "  [Observer 컨테이너 로그 — 최근 5줄]"
docker compose -f docker-compose.server.yml logs --tail 5 observer 2>/dev/null || docker logs --tail 5 observer 2>/dev/null || warn "Observer 로그 조회 실패"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  점검 완료"
echo "═══════════════════════════════════════════════════════════════"
echo ""
