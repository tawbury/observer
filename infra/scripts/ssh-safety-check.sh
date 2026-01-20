#!/bin/bash

# SSH 안전성 검증 스크립트 (읽기 전용)
# SSH 권한 및 설정 확인만 수행하며, 수정하지 않음

set -e

# 컬러 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 사용자 확인
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)
SSH_DIR="$USER_HOME/.ssh"
AUTH_KEYS="$SSH_DIR/authorized_keys"

log "SSH 안전성 검증 시작 (사용자: $CURRENT_USER)"

# 검증 실패 카운터
FAILURES=0

# 1. 홈 디렉토리 권한 확인 (읽기 전용)
if [ -d "$USER_HOME" ]; then
    HOME_PERM=$(stat -c %a "$USER_HOME" 2>/dev/null || echo "unknown")
    HOME_OWNER=$(stat -c %U "$USER_HOME" 2>/dev/null || echo "unknown")
    
    if [ "$HOME_PERM" != "700" ]; then
        error "홈 디렉토리 권한 오류: $HOME_PERM (요구: 700)"
        error "경로: $USER_HOME"
        error "소유자: $HOME_OWNER"
        FAILURES=$((FAILURES + 1))
    else
        log "홈 디렉토리 권한 정상: 700"
    fi
    
    if [ "$HOME_OWNER" != "$CURRENT_USER" ]; then
        error "홈 디렉토리 소유자 오류: $HOME_OWNER (요구: $CURRENT_USER)"
        FAILURES=$((FAILURES + 1))
    fi
else
    error "홈 디렉토리를 찾을 수 없습니다: $USER_HOME"
    FAILURES=$((FAILURES + 1))
fi

# 2. SSH 디렉토리 권한 확인 (읽기 전용)
if [ -d "$SSH_DIR" ]; then
    SSH_PERM=$(stat -c %a "$SSH_DIR" 2>/dev/null || echo "unknown")
    SSH_OWNER=$(stat -c %U "$SSH_DIR" 2>/dev/null || echo "unknown")
    
    if [ "$SSH_PERM" != "700" ]; then
        error "SSH 디렉토리 권한 오류: $SSH_PERM (요구: 700)"
        error "경로: $SSH_DIR"
        error "소유자: $SSH_OWNER"
        FAILURES=$((FAILURES + 1))
    else
        log "SSH 디렉토리 권한 정상: 700"
    fi
    
    if [ "$SSH_OWNER" != "$CURRENT_USER" ]; then
        error "SSH 디렉토리 소유자 오류: $SSH_OWNER (요구: $CURRENT_USER)"
        FAILURES=$((FAILURES + 1))
    fi
else
    error "SSH 디렉토리를 찾을 수 없습니다: $SSH_DIR"
    FAILURES=$((FAILURES + 1))
fi

# 3. authorized_keys 파일 권한 확인 (읽기 전용)
if [ -f "$AUTH_KEYS" ]; then
    AUTH_PERM=$(stat -c %a "$AUTH_KEYS" 2>/dev/null || echo "unknown")
    AUTH_OWNER=$(stat -c %U "$AUTH_KEYS" 2>/dev/null || echo "unknown")
    
    if [ "$AUTH_PERM" != "600" ]; then
        error "authorized_keys 권한 오류: $AUTH_PERM (요구: 600)"
        error "경로: $AUTH_KEYS"
        error "소유자: $AUTH_OWNER"
        FAILURES=$((FAILURES + 1))
    else
        log "authorized_keys 권한 정상: 600"
    fi
    
    if [ "$AUTH_OWNER" != "$CURRENT_USER" ]; then
        error "authorized_keys 소유자 오류: $AUTH_OWNER (요구: $CURRENT_USER)"
        FAILURES=$((FAILURES + 1))
    fi
    
    # 파일 내용 확인
    if [ ! -s "$AUTH_KEYS" ]; then
        error "authorized_keys 파일이 비어있습니다"
        FAILURES=$((FAILURES + 1))
    else
        KEY_COUNT=$(wc -l < "$AUTH_KEYS" 2>/dev/null || echo "0")
        log "SSH 키 $KEY_COUNT 개 등록됨"
        
        # 키 유효성 기본 확인 (읽기 전용)
        INVALID_KEYS=0
        while IFS= read -r line; do
            if [[ -n "$line" && ! "$line" =~ ^# ]]; then
                if [[ "$line" =~ ^ssh-(rsa|dss|ecdsa|ed25519) ]]; then
                    continue
                else
                    warn "유효하지 않은 SSH 키 형식: ${line:0:30}..."
                    INVALID_KEYS=$((INVALID_KEYS + 1))
                fi
            fi
        done < "$AUTH_KEYS"
        
        if [ $INVALID_KEYS -gt 0 ]; then
            warn "유효하지 않은 SSH 키 $INVALID_KEYS 개 발견"
        fi
    fi
else
    error "authorized_keys 파일을 찾을 수 없습니다: $AUTH_KEYS"
    FAILURES=$((FAILURES + 1))
fi

# 4. SSH 서비스 상태 확인 (읽기 전용)
SSH_SERVICE="sshd"
if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "$SSH_SERVICE" 2>/dev/null; then
        log "SSH 서비스 실행 중 ($SSH_SERVICE)"
    elif systemctl is-active --quiet ssh 2>/dev/null; then
        SSH_SERVICE="ssh"
        log "SSH 서비스 실행 중 ($SSH_SERVICE)"
    else
        error "SSH 서비스가 실행 중이 아닙니다"
        FAILURES=$((FAILURES + 1))
    fi
else
    warn "systemctl을 사용할 수 없습니다. SSH 서비스 상태 확인을 건너뜁니다."
fi

# 5. 추가 보안 검증 (읽기 전용)
log "추가 보안 검증 중..."

# SSH 설정 파일 기본 권한 확인
SSH_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSH_CONFIG" ]; then
    CONFIG_PERM=$(stat -c %a "$SSH_CONFIG" 2>/dev/null || echo "unknown")
    if [ "$CONFIG_PERM" != "644" ] && [ "$CONFIG_PERM" != "600" ]; then
        warn "SSH 설정 파일 권한 비표준: $CONFIG_PERM (권장: 644 또는 600)"
    else
        log "SSH 설정 파일 권한 정상: $CONFIG_PERM"
    fi
fi

# 6. 네트워크 연결 확인 (읽기 전용)
if command -v netstat >/dev/null 2>&1; then
    SSH_PORT=$(grep -i "^Port" "$SSH_CONFIG" 2>/dev/null | awk '{print $2}' || echo "22")
    if netstat -ln 2>/dev/null | grep -q ":$SSH_PORT "; then
        log "SSH 포트 $SSH_PORT 수신 대기 중"
    else
        error "SSH 포트 $SSH_PORT 수신 대기 상태가 아닙니다"
        FAILURES=$((FAILURES + 1))
    fi
fi

# 7. 최종 상태 요약
echo ""
if [ $FAILURES -eq 0 ]; then
    log "✅ SSH 안전성 검증 통과"
    echo ""
    echo "📋 검증 결과 요약:"
    echo "   - 사용자: $CURRENT_USER"
    echo "   - 홈 디렉토리: $USER_HOME (권한: $(stat -c %a "$USER_HOME" 2>/dev/null || echo "unknown"))"
    echo "   - SSH 디렉토리: $SSH_DIR (권한: $(stat -c %a "$SSH_DIR" 2>/dev/null || echo "unknown"))"
    echo "   - authorized_keys: $AUTH_KEYS (권한: $(stat -c %a "$AUTH_KEYS" 2>/dev/null || echo "unknown"))"
    echo "   - 등록된 SSH 키: $(wc -l < "$AUTH_KEYS" 2>/dev/null || echo "0") 개"
    echo "   - SSH 서비스: $SSH_SERVICE"
    echo ""
    exit 0
else
    error "❌ SSH 안전성 검증 실패 ($FAILURES 개 오류)"
    echo ""
    echo "🔧 수동 수정 필요:"
    echo "   chmod 700 ~"
    echo "   chmod 700 ~/.ssh"
    echo "   chmod 600 ~/.ssh/authorized_keys"
    echo "   chown -R $CURRENT_USER:$CURRENT_USER ~/.ssh"
    echo ""
    exit 1
fi
