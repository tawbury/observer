# Observer System (QTS Observer)

이 저장소는 한국투자증권(KIS) API를 활용하여 시장 데이터를 관찰, 필터링 및 아카이빙하는 **Observer** 시스템의 소스 코드와 설정을 포함합니다. 현재 실제 서버에서 가동 중인 시스템입니다.

## 프로젝트 개요
- **핵심 목표**: KOSPI/KOSDAQ 전 종목 중 유의미한 종목(4천원 이상 등)의 실시간 시세 스냅샷 및 아카이빙.
- **주요 처리**: 수집 → 실시간 검증(Validation) → 가드(Guard) → 데이터 보강(Enrichment) → 최종 아카이브(JSONL).
- **에코시스템**:
  - **[Deployment Repo](https://github.com/tawbury/Deployment)**: K3s 인프라 및 ArgoCD 기반 자동 배포 환경 관리.
  - **[QTS Repo](https://github.com/tawbury/QTS)**: Observer 데이터를 소비하여 전략 실행 및 자동 매매를 수행하는 코어 엔진.
- **상세 설계**: [Observer Architecture v2.0](docs/dev/archi/observer_architecture_v2.md) 참고.

## 폴더 구조

### 1. 핵심 소스 코드 (`src/`)
- **[observer/](src/observer/)**: 시스템의 중추. 데이터 검증(Validation), 필터(Guard), 데이터 보강(Enrichment) 및 API 서버.
- **[runtime/](src/runtime/)**: 시스템 실행 엔트리포인트 및 런너. 수집 및 유지보수 태스크 관리.
- **[collector/](src/collector/)**: KIS API 실시간 데이터 수집기 (Track A, Track B).
- **[universe/](src/universe/)**: 관찰 대상 종목(Universe) 생성 및 스케줄링 관리.
- **[provider/](src/provider/) / [auth/](src/auth/)**: KIS API 연동 물리 계층 및 인증 토큰 관리.
- **[db/](src/db/)**: PostgreSQL 연동, 스키마 관리 및 DB 마이그레이션.
- **[maintenance/](src/maintenance/)**: 로그 로테이션, 데이터 정리 등 시스템 유지보수 프로세스.
- **[monitoring/](src/monitoring/) / [shared/](src/shared/)**: 시스템 상태 모니터링 및 공통 유틸리티(Time, Serialization).

### 2. 설정 및 운영 자산
- **config/**: 시스템 및 환경별 설정 파일 (`.env` 포함).
- **data/**: 런타임 캐시 및 최종 JSONL 아카이브 저장소.
- **docs/**: 아키텍처 가이드, 데이터 명세서 및 운영 문서.
- **docker/**: Dockerfile 및 K8s 배포를 위한 설정.
- **scripts/**: 빌드, DB 초기화 및 개발 보조 스크립트.
- **tests/**: 단위 테스트 및 통합 테스트 코드.

### 3. CI/CD 및 기타
- **.github/workflows/**: GitHub Actions를 이용한 자동화된 빌드/배포 워크플로우.
- **migrations/**: DB 버전 관리를 위한 마이그레이션 파일.

## 주요 문서
- **[Observer Architecture v2.0](docs/dev/archi/observer_architecture_v2.md)**: 시스템 핵심 설계 및 데이터 흐름도.
- **[Source Code Guide](src/README.md)**: 소스 코드 레이어 구조 및 패키지 간 의존성 설명.
- **[Deployment Guide](docs/dev/deployment/README.md)**: K3s 운영 환경 및 배포 절차.
- **[Database Schema](src/db/README.md)**: DB 테이블 설계 및 마이그레이션 가이드.

## 빠른 시작

### 1. 로컬 실행 (Python)
```bash
# 의존성 설치
pip install -r requirements.txt

# Observer 실행 (예시: Symbol Generator)
python -m src.runtime.symbol_generator
```

### 2. Docker를 이용한 배포
```bash
# Docker Compose 기반 실행
docker-compose -f docker/docker-compose.yml up -d
```

## 운영 및 배포 (CI/CD)

이 프로젝트는 GitHub Actions와 ArgoCD를 활용하여 자동화된 배포 파이프라인을 운영합니다.

### 1. CI: 이미지 빌드 및 푸시
- **GitHub Action**: [Build and push GHCR image](.github/workflows/ghcr-build-image.yml)
- **트리거**: `observer` 브랜치 push 또는 `master` 브랜치로의 PR 머지 시 실행.
- **처리**:
  1. Docker 이미지를 빌드합니다 (ARM64 아키텍처 지원).
  2. 이미지를 **GHCR** (`ghcr.io/tawbury/observer`)에 푸시합니다.
  3. **[Deployment Repo](https://github.com/tawbury/Deployment)**의 Kustomize 설정(`newTag`)을 새 이미지 태그로 자동 업데이트합니다.

### 2. CD: 서버 배포
- **도구**: **ArgoCD**
- **처리**: ArgoCD가 `Deployment` 저장소의 변경 사항을 감지하여 실제 운영 서버(K3s 등)에 최신 이미지를 배포합니다.

### 3. 레지스트리
- **GHCR**: `ghcr.io/tawbury/observer`
- **태그 규칙**: `build-yyyyMMdd-HHmmss` (타임스탬프 기반)

---

> **주의**: 구 버전의 `app/` 디렉토리 기반 배포 구조는 `src/` 중심의 표준 구조로 통합되었습니다. 모든 최신 설정과 문서는 `docs/` 폴더를 참고하세요.
