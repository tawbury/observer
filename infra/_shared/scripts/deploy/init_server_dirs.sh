#!/bin/bash
# init_server_dirs.sh
# Oracle Cloud VM (oracle-obs-vm-01) 서버 초기화 스크립트
#
# 사용법:
#   chmod +x init_server_dirs.sh
#   ./init_server_dirs.sh
#
# 이 스크립트는 Observer 애플리케이션이 필요로 하는 
# 호스트 디렉토리 구조를 생성합니다.

set -e

echo "=========================================="
echo "Observer Server Directory Initialization"
echo "=========================================="

# 기본 경로 설정
OBSERVER_ROOT="${HOME}/observer"

echo ""
echo "[1/4] Creating base directories..."
mkdir -p "${OBSERVER_ROOT}/config/observer/scalp"
mkdir -p "${OBSERVER_ROOT}/config/observer/swing"
mkdir -p "${OBSERVER_ROOT}/config/observer/system"
echo "  - config/observer/{scalp,swing,system} created"

echo ""
echo "[2/4] Creating log directories..."
mkdir -p "${OBSERVER_ROOT}/logs/scalp"
mkdir -p "${OBSERVER_ROOT}/logs/swing"
mkdir -p "${OBSERVER_ROOT}/logs/system"
mkdir -p "${OBSERVER_ROOT}/logs/maintenance"
echo "  - logs/{scalp,swing,system,maintenance} created"

echo ""
echo "[3/4] Creating data directories..."
mkdir -p "${OBSERVER_ROOT}/data/observer"
echo "  - data/observer created"

echo ""
echo "[4/4] Creating secrets directory..."
mkdir -p "${OBSERVER_ROOT}/secrets/.kis_cache"
echo "  - secrets/.kis_cache created"

# 권한 설정 (Docker 컨테이너에서 접근 가능하도록)
echo ""
echo "[*] Setting permissions..."
chmod -R 777 "${OBSERVER_ROOT}"
echo "  - Permissions set to 777 for ${OBSERVER_ROOT}"

echo ""
echo "=========================================="
echo "Directory structure created successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Create/update ${OBSERVER_ROOT}/secrets/.env with KIS credentials:"
echo "     KIS_APP_KEY=your_app_key"
echo "     KIS_APP_SECRET=your_app_secret"
echo "     KIS_IS_VIRTUAL=false"
echo "     TRACK_A_ENABLED=true"
echo "     TRACK_B_ENABLED=false"
echo ""
echo "  2. Deploy the application:"
echo "     cd ~/observer-deploy"
echo "     export IMAGE_TAG=build-YYYYMMDD-HHMMSS"
echo "     docker compose -f docker-compose.server.yml up -d"
echo ""
echo "  3. Verify:"
echo "     docker logs observer --tail 30"
echo "     docker exec observer env | grep KIS"
echo ""

# 디렉토리 구조 출력
echo "Created directory structure:"
tree "${OBSERVER_ROOT}" 2>/dev/null || find "${OBSERVER_ROOT}" -type d | head -20
