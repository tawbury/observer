# 공통 인프라 리소스 (Shared Infrastructure Resources)

이 디렉토리는 모든 환경(로컬 개발, OCI 배포, 향후 Kubernetes 등)에서 공통으로 사용되는 인프라 리소스를 포함합니다.

## 🔀 배포 vs 프로비저닝 분리 원칙

- **배포(앱 컨테이너 띄우기)**: 통합 운영. `_shared/deploy/` 스펙 + `_shared/scripts/deploy/deploy.sh` 하나로 OCI/AWS/GCP/ARM 등 **어떤 VM이든 SSH만 되면 동일하게** 배포합니다. 따라서 arm/aws/gcp/oci 별로 배포 스크립트·YAML을 나눌 필요 없습니다.
- **프로비저닝(VM 생성·네트워크·cloud-init 등)**: 클라우드마다 API/도구가 다르므로 `infra/oci_deploy/`, `infra/aws_deploy/` 등 **클라우드별 폴더**에만 둡니다. 예: OCI 인스턴스 런치, cloud-init, OCI CLI 스크립트.

정리: **배포는 _shared만 사용하고, 클라우드별 폴더는 VM 만들기·부트스트랩 전용**으로 두면 됩니다.

## 📁 디렉토리 구조

```
infra/_shared/
├── compose/             # 프로덕션 docker-compose 파일
│   ├── docker-compose.prod.yml
│   └── docker-compose.server.yml
│
├── monitoring/          # 모니터링 스택 설정 (compose 제외)
│   ├── prometheus.yml
│   ├── alertmanager.yml
│   ├── prometheus_alerting_rules.yaml
│   ├── grafana_dashboard.json
│   └── grafana_datasources.yml
│
├── deploy/              # 선언형 배포 스펙 (통합 운영, 클라우드 비종속)
│   └── observer.yaml
│
├── migrations/          # 데이터베이스 마이그레이션 스크립트
│   ├── 001_create_scalp_tables.sql
│   ├── 002_create_swing_tables.sql
│   ├── 003_create_portfolio_tables.sql
│   └── 004_create_analysis_tables.sql
│
└── scripts/             # 공통 스크립트
    ├── build/           # 빌드 태그 생성
    ├── deploy/          # 배포 (deploy.ps1, server_deploy.sh 등)
    ├── docker/          # Docker/Compose 헬퍼
    ├── docs/            # 문서 (QUICKSTART, IMPLEMENTATION_REPORT)
    ├── env/             # 환경 설정 (setup_env_secure.sh 등)
    ├── migrate/         # DB 마이그레이션 (migrate.sh)
    ├── oci/             # OCI 프로비저닝 스크립트
    └── README.md
```

## 🔧 사용 방법

### 모니터링 설정 사용

#### Docker Compose에서 사용
```yaml
volumes:
  - ../_shared/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  - ../_shared/monitoring/prometheus_alerting_rules.yaml:/etc/prometheus/rules.yaml
  - ../_shared/monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
  - ../_shared/monitoring/grafana_dashboard.json:/etc/grafana/provisioning/dashboards/observer.json
  - ../_shared/monitoring/grafana_datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
```

#### 독립 실행 (전체 스택)
```bash
cd infra/_shared/compose
docker-compose -f docker-compose.server.yml up -d
```

### 데이터베이스 마이그레이션 사용

#### Docker Compose에서 사용
```yaml
volumes:
  - ../_shared/migrations:/docker-entrypoint-initdb.d
```

#### 수동 실행
```bash
psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} < infra/_shared/migrations/001_create_scalp_tables.sql
psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} < infra/_shared/migrations/002_create_swing_tables.sql
psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} < infra/_shared/migrations/003_create_portfolio_tables.sql
psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} < infra/_shared/migrations/004_create_analysis_tables.sql
```

## 📋 포함된 리소스

### 모니터링 스택
- **Prometheus**: 메트릭 수집 및 저장
- **Grafana**: 대시보드 및 시각화
- **Alertmanager**: 알림 관리 및 라우팅

### 데이터베이스 마이그레이션
- **001_create_scalp_tables.sql**: Scalp Trading (Track B) 테이블
- **002_create_swing_tables.sql**: Swing Trading (Track A) 테이블
- **003_create_portfolio_tables.sql**: 포트폴리오 및 리밸런싱 테이블
- **004_create_analysis_tables.sql**: 분석용 테이블(롤링 통계, 임계값 후보, 시그널 이벤트)

### Secrets (민감한 정보)
- **환경 변수 파일**: `.env.prod`, `.env.dev` 등 환경별 설정
- **SSL 인증서**: HTTPS 통신용 인증서
- **SSH 키**: 배포 및 서버 접근용 키
- **클라우드 인증 정보**: OCI, AWS 등 클라우드 서비스 인증 정보

자세한 내용은 [`secrets/README.md`](secrets/README.md) 참조

### Scripts (공통 스크립트)
- **build/**: 빌드 태그 생성 (generate_build_tag.ps1, generate_build_tag.sh)
- **deploy/**: 배포 (deploy.ps1, server_deploy.sh, init_server_dirs.sh 등)
- **docker/**: Docker/Compose 헬퍼 (sync_container_time.ps1 등)
- **docs/**: 문서 (QUICKSTART.md, IMPLEMENTATION_REPORT.md)
- **env/**: 환경 설정 (setup_env_secure.sh)
- **migrate/**: DB 마이그레이션 실행 (migrate.sh)
- **oci/**: OCI 프로비저닝 (oci_launch_instance.ps1, oracle_bootstrap.sh 등)

자세한 내용은 [`scripts/README.md`](scripts/README.md) 참조

## 🚀 향후 확장 계획

향후 Kubernetes 환경으로 전환할 때:
- `_shared/monitoring/`의 설정 파일을 ConfigMap으로 변환
- `_shared/migrations/`를 InitContainer나 Job으로 실행
- `_shared/secrets/`의 환경 변수를 Secret 리소스로 변환
- `_shared/scripts/`의 배포·마이그레이션 스크립트를 CI/InitContainer 등에서 재사용
- 동일한 설정 파일을 재사용하여 일관성 유지

## 📝 주의사항

- 이 디렉토리의 파일은 **모든 환경에서 공통으로 사용**됩니다
- 환경별 커스터마이징이 필요한 경우, 각 환경 디렉토리(`oci_deploy/`, `k8s/` 등)에서 오버라이드하세요
- 설정 파일을 수정할 때는 모든 환경에 영향을 미칠 수 있으므로 주의하세요
