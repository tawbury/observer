#!/bin/bash

# Azure VM에서 기존 파일 정리 스크립트

echo "========================================"
echo "   VM 기존 파일 정리"
echo "========================================"

# 기존 파일 확인
echo ""
echo "=== 기존 파일 확인 ==="
ls -la ~ | grep -E "observer|obs_deploy|app" || echo "관련 파일 없음"

# 기존 파일 삭제
echo ""
echo "=== 기존 파일 삭제 ==="
rm -rf ~/observer-deploy && echo "✅ observer-deploy 삭제" || echo "⚠️ observer-deploy 없음"
rm -rf ~/app && echo "✅ app 삭제" || echo "⚠️ app 없음"
rm -f ~/obs_deploy.tar.gz && echo "✅ obs_deploy.tar.gz 삭제" || echo "⚠️ obs_deploy.tar.gz 없음"

# 삭제 확인
echo ""
echo "=== 삭제 확인 ==="
ls -la ~ | grep -E "observer|obs_deploy|app" || echo "✅ 관련 파일 모두 삭제됨"

# 홈 디렉토리 상태
echo ""
echo "=== 현재 홈 디렉토리 ==="
ls -la ~

echo ""
echo "========================================"
echo "   정리 완료"
echo "========================================"
