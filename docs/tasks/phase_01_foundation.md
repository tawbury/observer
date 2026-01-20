# Phase 01: Foundation

**목적:** Repository/Packaging/Runtime 스캐폴딩 검증  
**선수 조건:** 없음  
**완료 기준:** 로컬/컨테이너 실행 환경 동등성 확보, 기본 파이프라인 동작 확인

---

## 개요

### 목표
- 프로젝트 구조와 패키징이 아키텍처와 일치하는지 검증
- 설정/경로 계약이 문서대로 동작하는지 확인
- 최소한의 "hello pipeline"으로 전체 흐름 검증

### 배경
아키텍처 문서에서 정의한 실행 모드(collect/etl)와 경로 계약이 실제 코드와 일치하는지 기본 검증이 필요합니다.

---

## Deliverables

- [ ] 로컬 실행 환경 검증 보고서
- [ ] 컨테이너 실행 환경 검증 보고서
- [ ] 경로/환경변수 계약 준수 확인서
- [ ] 기본 파이프라인 동작 증명

---

## Tasks

### 1. Repository 구조 검증
- [ ] 프로젝트 루트 구조가 아키텍처와 일치하는지 확인
  - [ ] app/obs_deploy/ 위치 확인
  - [ ] docs/development/ SSoT 문서 존재 확인
  - [ ] infra/ Terraform 구조 확인
- [ ] 패키징 파일 검증
  - [ ] requirements.txt 또는 pyproject.toml 존재 확인
  - [ ] Dockerfile 존재 및 기본 구조 검증
  - [ ] docker-compose.yml 존재 확인

### 2. Config/Path 계약 검증
- [ ] 환경변수 표준화 확인
  - [ ] QTS_OBSERVER_STANDALONE 사용 여부 확인
  - [ ] OBSERVER_STANDALONE 사용 위치 확인 (있을 경우)
- [ ] 경로 계약 검증
  - [ ] config/observer/ 경로가 코드에서 사용되는지 확인
  - [ ] paths.py의 observer_asset_dir() 구현 확인
  - [ ] 환경변수 우선순위 로직 확인
- [ ] 볼륨 마운트 정합성 확인
  - [ ] docker-compose.yml 볼륨 설정 확인
  - [ ] 호스트-컨테이너 경로 매핑 확인

### 3. Runtime 스캐폴딩 검증
- [ ] 로컬 실행 가능성 확인
  - [ ] python observer.py 직접 실행 테스트
  - [ ] 기본 인자/옵션 동작 확인
  - [ ] 에러 메시지 적절성 확인
- [ ] 컨테이너 실행 가능성 확인
  - [ ] Docker 이미지 빌드 성공 확인
  - [ ] docker-compose up 최소 실행 확인
  - [ ] 컨테이너 내부 경로 접근 확인

### 4. 최소 파이프라인 검증
- [ ] "Hello Pipeline" 구현
  - [ ] 더미 스냅샷 생성 함수 구현
  - [ ] Observer.on_snapshot() 호출 테스트
  - [ ] Validation → Guard → Enrichment 흐름 확인
- [ ] 로그 출력 확인
  - [ ] 콘솔 로그 출력 확인
  - [ ] JSONL 파일 생성 최소 확인
  - [ ] EventBus 동작 확인

---

## Test Plan

### 환경 준비
1. 로컬 Python 환경 설정
2. Docker 설치 확인
3. 프로젝트 코드 체크아웃

### 실행 단계
1. 로컬 실행 테스트
   - python observer.py 실행
   - 기본 옵션 테스트
   - 에러 케이스 확인

2. 컨테이너 실행 테스트
   - docker build -t observer:test .
   - docker-compose up -d
   - 컨테이너 로그 확인

3. 경로 계약 테스트
   - 환경변수 설정 전후 경로 확인
   - config/observer/ 디렉토리 생성 확인
   - 파일 쓰기 권한 확인

4. 파이프라인 테스트
   - 더미 스냅샷 주입
   - 전체 파이프라인 흐름 확인
   - 출력 파일 검증

---

## Done Criteria

### 기술적 완료
- [ ] 로컬과 컨테이너 실행 결과 동일
- [ ] QTS_OBSERVER_STANDALONE 환경변수가 경로 결정에 영향을 줌
- [ ] 더미 스냅샷이 전체 파이프라인을 통과하여 JSONL로 출력됨
- [ ] 모든 에러 케이스가 적절한 메시지를 출력함

### 문서적 완료
- [ ] 검증 결과가 SSoT 문서와 일치함을 증명
- [ ] 경로/환경변수 계약이 코드에 반영되어 있음
- [ ] 다음 Phase를 위한 기반 환경이 준비됨

---

## 의존성

- **선수 조건:** 없음
- **후속 영향:** Phase 02 KIS Integration 기반 제공

---

## 리스크 및 완화

### 고위험
- 환경변수 불일치 → Phase 03 로그 생성 실패
- 경로 권한 문제 → 컨테이너 실행 실패

### 완화 조치
- 모든 경로/환경변수 조합 테스트
- 권한 문제 사전 확인 및 수정 가이드 작성
