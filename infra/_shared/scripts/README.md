# 공통 스크립트 (Shared Scripts)

이 디렉토리는 **모든 환경**에서 공통으로 사용하는 인프라/배포 스크립트를 담습니다.

## 📁 디렉토리 구조

```
infra/_shared/scripts/
├── build/            # 빌드 태그 생성 (generate_build_tag.ps1, generate_build_tag.sh)
├── deploy/           # 배포 (deploy.ps1, server_deploy.sh, init_server_dirs.sh)
├── docker/           # Docker/Compose 헬퍼 (sync_container_time.ps1 등)
├── docs/             # QUICKSTART, IMPLEMENTATION_REPORT 등 상위 문서
├── env/              # 환경 설정 (setup_env_secure.sh)
├── migrate/          # DB/앱 마이그레이션 (migrate.sh)
├── oci/              # OCI 프로비저닝 (oci_launch_instance.ps1, oracle_bootstrap.sh)
└── README.md         # 이 파일
```

## 📋 역할별 설명

| 폴더 | 역할 | 스크립트 |
|------|------|-----------|
| **build/** | 빌드 태그 생성 (20YYMMDD-HHMMSS) | generate_build_tag.ps1, generate_build_tag.sh |
| **deploy/** | 배포 (로컬→서버, Compose 기동 등) | deploy.ps1, server_deploy.sh, init_server_dirs.sh |
| **docker/** | Docker/Compose 헬퍼 | sync_container_time.ps1 (컨테이너·호스트 시간 drift 검사) |
| **env/** | 환경 변수·시크릿 설정 | setup_env_secure.sh |
| **migrate/** | DB/앱 마이그레이션 | migrate.sh (Phase 13 JSONL→DB 등) |
| **oci/** | OCI 프로비저닝 | oci_launch_instance.ps1, oci_helpers.ps1, oracle_bootstrap.sh |

## 🔗 _shared 리소스 참조

스크립트 내부에서는 상대 경로로 공통 리소스를 참조합니다.

- **마이그레이션**: `../../migrations/`
- **시크릿/환경변수**: `../../secrets/.env.prod` 등
- **모니터링 설정**: `../../monitoring/`

실행 시 작업 디렉토리는 **프로젝트 루트**에서 호출하는 것을 전제로 상대 경로를 해석합니다.

## 🚫 환경 전용 스크립트

Kubernetes 등 **특정 환경만** 쓰는 스크립트는 여기 두지 않습니다.

- Kubernetes 전용: `infra/k8s/scripts/` (향후)

OCI 프로비저닝 스크립트는 `oci/` 폴더에 통합되었습니다.

## 📚 하위 폴더별 가이드

- [build/README.md](build/README.md) – 빌드 태그 생성
- [deploy/README.md](deploy/README.md) – 배포 스크립트 사용법
- [docker/README.md](docker/README.md) – Docker/Compose 스크립트 사용법
- [env/README.md](env/README.md) – 환경 설정 스크립트 사용법
- [migrate/README.md](migrate/README.md) – 마이그레이션 스크립트 사용법
- [oci/README.md](oci/README.md) – OCI 프로비저닝 스크립트 사용법
- [docs/](docs/) – QUICKSTART, IMPLEMENTATION_REPORT 등 상위 문서

---

**마지막 업데이트**: 2026-01-29
