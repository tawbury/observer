# 서버 볼륨 마운트 점검 결과 - 2026-02-02

## 1. 확인 결과 요약

### 1.1 발견된 문제: **볼륨 마운트 미적용**

| 항목 | 상태 | 설명 |
|------|------|------|
| `docker inspect observer --format '{{json .Mounts}}'` | `[]` (빈 배열) | 컨테이너에 **볼륨이 마운트되어 있지 않음** |
| `HostConfig.Binds` | `[]` (빈 배열) | bind 마운트 없음 |
| 컨테이너 `/app/config/scalp/` | **비어 있음** | JSONL 파일 없음 (스켈프 미저장) |
| 컨테이너 `/app/config/swing/` | 20260202.jsonl만 존재 | 컨테이너 내부에만 있음, 호스트와 분리 |
| 호스트 `~/observer/config/` | 이전 데이터 있음 | 마지막 마운트 시점 이후 갱신 없음 |

### 1.2 결론

- **컨테이너가 호스트 디렉터리와 연결되어 있지 않습니다.**
- 컨테이너는 `/app/config`를 **자체 파일시스템**에 사용하고 있어, 재시작 시 데이터가 사라집니다.
- `docker-compose.server.yml`에는 볼륨 정의가 있으나, **현재 실행 중인 컨테이너에는 적용되지 않은 상태**입니다.
- 이전에 볼륨이 적용된 컨테이너로 수집된 데이터는 호스트 `~/observer/config/`에 남아 있습니다.

---

## 2. 상세 점검 내역

### 2.1 컨테이너 및 이미지

```bash
# 실행 중인 컨테이너
NAMES               IMAGE                                            STATUS
observer            ghcr.io/tawbury/observer:build-20260202-041215   Up About a minute (healthy)
observer-postgres   postgres:15-alpine                               Up 4 hours (healthy)

# 컨테이너 사용자
uid=999(observer) gid=999(observer)
```

### 2.2 볼륨 마운트 상태

```bash
$ docker inspect observer --format '{{json .Mounts}}'
[]
```

### 2.3 컨테이너 내부 vs 호스트

**컨테이너 내부 `/app/config/`**

```
/app/config/scalp/:  (비어 있음 - test_write_.txt만 존재)
/app/config/swing/:  20260202.jsonl (907KB, 13:16 KST 기준)
```

**호스트 `~/observer/config/`**

```
/home/ubuntu/observer/config/scalp/:
  20260202_09.jsonl (12KB), 20260202_10.jsonl (20KB), 20260202_11.jsonl (16KB)
  - 마지막 수정: 00:55, 01:59, 02:47 UTC (이전 컨테이너/마운트 시점)

/home/ubuntu/observer/config/swing/:
  20260202.jsonl (9.5MB), 20260130~20260201.jsonl
  - 마지막 수정: 04:12 UTC
```

### 2.4 Compose 설정 확인

`~/observer-deploy/docker-compose.server.yml`에 볼륨이 정상 정의되어 있음:

```yaml
volumes:
  - ../observer/data:/app/data
  - ../observer/logs:/app/logs
  - ../observer/config:/app/config
  - ../observer/secrets:/app/secrets
```

---

## 3. 원인 추정

1. **컨테이너가 볼륨 없이 처음 생성된 후 재생성되지 않음**  
   - `docker compose up -d`만 수행되어 기존 컨테이너가 유지됨  
   - compose 파일 변경(볼륨 추가) 이후 `--force-recreate` 없이 배포됨  

2. **이전에 다른 compose 파일로 실행됨**  
   - 볼륨이 없는 compose 파일로 먼저 실행했을 가능성  

3. **배포 스크립트/워크플로우 차이**  
   - 배포 시 업로드되는 compose 파일과 실제 서버의 compose 파일이 다를 수 있음  

---

## 4. 조치 방법

### 4.1 컨테이너 재생성 (볼륨 적용)

```bash
ssh oracle-obs-vm-01

cd ~/observer-deploy

# 현재 이미지 태그 확인
export IMAGE_TAG=build-20260202-041215

# observer 컨테이너만 강제 재생성 (볼륨 적용)
docker compose -f docker-compose.server.yml up -d --force-recreate observer

# 마운트 확인
docker inspect observer --format '{{range .Mounts}}Source: {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

### 4.2 마운트 확인

```bash
# 컨테이너에서 파일 생성 후 호스트에서 확인
docker exec observer touch /app/config/scalp/volume_test.txt
ls -la ~/observer/config/scalp/volume_test.txt  # 존재하면 마운트 정상
docker exec observer rm /app/config/scalp/volume_test.txt
```

### 4.3 권한 점검 (필요 시)

호스트 디렉터리/파일 소유자가 컨테이너 사용자(999)와 다를 경우:

```bash
sudo chown -R 999:999 ~/observer/config/swing ~/observer/config/scalp
```

---

## 5. 배포 스크립트 권장 수정

향후 배포 시 볼륨이 반드시 적용되도록:

```bash
# server_deploy.sh 또는 deploy.ps1 내
docker compose -f docker-compose.server.yml up -d --force-recreate observer
```

또는:

```bash
docker compose -f docker-compose.server.yml down observer
docker compose -f docker-compose.server.yml up -d observer
```

---

**작성**: 2026-02-02  
**서버**: oracle-obs-vm-01
