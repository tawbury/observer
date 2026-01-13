#!/bin/bash

cd ~/observer-deploy

echo "=== 파일 검증 ==="
echo ""

# 1. 주요 파일
echo "[1. 주요 파일]"
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile: $(ls -lh Dockerfile | awk '{print $5}')"
else
    echo "❌ Dockerfile 없음"
fi
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml: $(ls -lh docker-compose.yml | awk '{print $5}')"
else
    echo "❌ docker-compose.yml 없음"
fi
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt: $(ls -lh requirements.txt | awk '{print $5}')"
else
    echo "❌ requirements.txt 없음"
fi
if [ -f "env.template" ]; then
    echo "✅ env.template: $(ls -lh env.template | awk '{print $5}')"
else
    echo "❌ env.template 없음"
fi

# 2. app 폴더
echo ""
echo "[2. app 폴더]"
if [ -f "app/observer.py" ]; then
    obs_size=$(stat -c%s app/observer.py)
    echo "✅ observer.py: $obs_size bytes (2895 예상)"
else
    echo "❌ observer.py 없음"
fi
if [ -f "app/paths.py" ]; then
    paths_size=$(stat -c%s app/paths.py)
    echo "✅ paths.py: $paths_size bytes (6808 예상)"
else
    echo "❌ paths.py 없음"
fi

# 3. src 폴더
echo ""
echo "[3. src 폴더]"
if [ -d "app/src" ]; then
    src_count=$(find app/src -type f | wc -l)
    echo "파일 개수: $src_count (111개 이상 예상)"
    if [ "$src_count" -ge 111 ]; then
        echo "✅ src 폴더 정상"
    else
        echo "⚠️ src 폴더 파일 부족"
    fi
else
    echo "❌ src 폴더 없음"
fi

# 4. 전체 통계
echo ""
echo "[4. 전체 통계]"
total_files=$(find . -type f | wc -l)
total_size=$(du -sh . | cut -f1)
echo "총 파일: $total_files 개"
echo "총 크기: $total_size"

# 5. 권한
echo ""
echo "[5. 파일 소유자]"
ls -la | head -10

echo ""
echo "=== 검증 완료 ==="
