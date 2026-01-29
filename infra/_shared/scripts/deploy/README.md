# deploy – 배포 스크립트

배포 관련 공통 스크립트를 둡니다. **통합 운영**: OCI/AWS/GCP/ARM 등 클라우드별로 폴더를 나누지 않고, 하나의 스펙·스크립트로 어떤 VM(SSH 가능)이든 배포합니다.

## 스크립트

| 파일 | 설명 |
|------|------|
| **deploy.ps1** | 로컬에서 실행하는 수동 배포 (env 검증/업로드, 아티팩트 업로드, server_deploy.sh 호출, 헬스체크). `-EnvOnly`로 env만 갱신 가능 |
| **server_deploy.sh** | 서버에서 실행. 이미지 pull, Compose 기동, 헬스체크, 백업 등 |
| **deploy.sh** | 선언형 CD용. `infra/_shared/deploy/observer.yaml` 파싱 후 SSH로 VM에 docker pull/stop/rm/run. GitHub Actions CD 워크플로우에서 호출 |

## 선언형 스펙 (통합 운영)

- **infra/_shared/deploy/observer.yaml**: 서버(OCI/AWS/GCP 등) 비종속 선언형 배포 스펙. 이미지·포트·레플리카만 정의하며, `deploy.sh`가 VM SSH 배포에 사용.
- 클라우드별 배포 폴더(arm/aws/gcp/oci)는 **만들지 않음**. 대상 VM은 GitHub Secrets의 `SSH_HOST` 등으로만 구분.

실행 경로: **프로젝트 루트**에서 `infra\_shared\scripts\deploy\deploy.ps1` 또는 `./infra/_shared/scripts/deploy/deploy.ps1` (PowerShell), 서버에는 `server_deploy.sh`를 업로드 후 `./server_deploy.sh ...` 로 실행. CD 워크플로우는 루트에서 `./infra/_shared/scripts/deploy/deploy.sh` 호출.

## 사용 시점

- GitHub Actions 외에 **로컬에서 수동 배포**할 때
- 배포 디렉토리·Compose 파일·env 파일 경로를 프로젝트에 맞게 지정해서 실행

## 경로 관례

- Compose 파일: `infra/_shared/compose/docker-compose.prod.yml` 등, 아티팩트: `infra/docker/compose/`
- env 파일: `infra/_shared/secrets/.env.prod`
- 실행은 **프로젝트 루트**에서 호출하는 것을 전제로 상대 경로 작성

---

## .env 재생성 및 서버 이중 업로드 (방법 A + 옵션 1)

- **로컬**: `app/observer/env.template` 을 참고해 `app/observer/.env` 를 작성·보관 (KIS, DB, Observer 변수). `deploy.ps1` 은 env.template 키로 .env 검증 후 업로드.
- **서버 .env 두 곳**:
  - `~/observer-deploy/.env`: compose 변수 치환 (IMAGE_TAG, POSTGRES_PASSWORD 등) 및 server_deploy.sh 존재 검사.
  - `~/observer/secrets/.env`: observer 컨테이너 env_file (KIS_APP_KEY, KIS_APP_SECRET 등).
- **deploy.ps1** (옵션 1): 로컬 .env 한 번 업로드 시 **두 위치**에 동일 내용 적용. 백업도 두 곳 모두 수행.
  - 파라미터 `-ObserverDataDir /home/ubuntu/observer` 로 observer 데이터 디렉터리 지정 가능.
- **EnvOnly**: `-EnvOnly` 로 env만 갱신(아티팩트/배포 스킵) 시에도 observer-deploy/.env 와 observer/secrets/.env 둘 다 업데이트됨.

---

## Server (obs-prod-arm) 수동 배포

`~/observer-deploy` 와 `~/observer` 가 형제 디렉터리일 때, **최소 구성** (postgres + observer) 배포:

### 1. 기존 observer 컨테이너 정리

```bash
docker stop observer
docker rm observer
```

### 2. compose 파일 SCP 업로드 (로컬 PowerShell)

```powershell
scp -i "C:\Users\tawbu\.ssh\oracle-obs-vm-01.key" `
  infra/_shared/compose/docker-compose.server.minimal.yml `
  ubuntu@<서버IP>:~/observer-deploy/docker-compose.server.minimal.yml
```

### 3. 서버에서 기동

```bash
cd ~/observer-deploy
export IMAGE_TAG=build-YYYYMMDD-HHMMSS   # 실제 빌드 태그로 변경
docker compose -f docker-compose.server.minimal.yml up -d
```

### 4. 확인

```bash
docker logs observer --tail 50
docker exec observer env | grep KIS
```

- `KIS_APP_KEY`, `KIS_APP_SECRET` 이 보이면 env_file 적용됨.
- Track A/B 관련 로그에서 Collector 활성화 여부 확인.

### 5. E2E 점검 (볼륨·권한 포함)

서버에서 `check_server_health.sh` 로 아카이브, DB, **Observer 데이터 디렉터리·볼륨 마운트·쓰기 권한**, 로그 생성 여부까지 점검:

```bash
cd ~/observer-deploy
./check_server_health.sh /home/ubuntu/observer-deploy /home/ubuntu/observer docker-compose.server.yml
```

- 인자 1: 배포 디렉터리, 인자 2: Observer 데이터 디렉터리 (~/observer), 인자 3: compose 파일명.
- observer 컨테이너에 config/data/logs/secrets 볼륨이 붙었는지, 해당 디렉터리 쓰기 가능한지 확인됨.

---

## 서버 Compose 경로 (migrations / monitoring)

`docker-compose.server.yml` 은 CWD = observer-deploy 기준으로 다음 상대 경로를 사용합니다.

- `../observer` → ~/observer (데이터 디렉터리)
- `../migrations` → observer-deploy **형제** 디렉터리 (~/migrations)
- `../monitoring` → observer-deploy **형제** 디렉터리 (~/monitoring)

**서버에 ~/migrations, ~/monitoring 이 없으면** postgres init 또는 prometheus/grafana 마운트 실패가 날 수 있습니다.

**대응 (둘 중 하나):**

1. **형제 디렉터리 생성**: 서버에서 `~/migrations`, `~/monitoring` 를 만들고, 레포의 `infra/_shared/migrations`, `infra/_shared/monitoring` 내용을 각각 복사.
2. **observer-deploy 내부로 둘 경우**: 서버에서 `observer-deploy/migrations`, `observer-deploy/monitoring` 에 복사한 뒤, **서버 전용** compose 복사본에서만 경로를 바꿉니다.  
   - `../migrations` → `./migrations`  
   - `../monitoring` → `./monitoring`  
   저장소의 `infra/_shared/compose/docker-compose.server.yml` 은 수정하지 않고, 서버에 올리는 compose 파일만 위처럼 수정해 사용합니다.

자세한 .env 정의 및 env.template 기반 재생성 절차는 [SERVER_ENV.md](SERVER_ENV.md) 참고.
