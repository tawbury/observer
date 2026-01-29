# 서버 .env 정의 및 env.template 기반 재생성

## 서버 .env 두 종류

| 파일 | 용도 | 소스 |
|------|------|------|
| **observer-deploy/.env** | compose 변수 치환 (IMAGE_TAG, POSTGRES_PASSWORD, GRAFANA_ADMIN_PASSWORD 등) 및 server_deploy.sh 존재 검사 | deploy.ps1이 로컬 `app/observer/.env`를 업로드 |
| **observer/secrets/.env** | observer 컨테이너 env_file (KIS_APP_KEY, KIS_APP_SECRET 등) | deploy.ps1이 동일 내용을 observer/secrets/.env로 복사 |

- `docker-compose.server.yml`은 `env_file: ../observer/secrets/.env`로 컨테이너에 KIS 등 주입.
- deploy.ps1 (옵션 1): 로컬 .env 한 번 업로드 시 **두 위치**에 동일 내용 적용. 백업도 두 곳 모두 수행.

## env.template 기반 .env 재생성 절차

1. **로컬**: `app/observer/env.template`을 복사해 `app/observer/.env` 생성.
2. **필수 값 채우기**: KIS_APP_KEY, KIS_APP_SECRET, DB_PASSWORD(및 필요 시 POSTGRES_PASSWORD, IMAGE_TAG) 등을 로컬에서만 보관·입력.
3. **서버 .env 전부 삭제**(선택): 서버에서 observer-deploy/.env, observer/secrets/.env 및 .env.bak-* 삭제.
4. **업로드**: `deploy.ps1 -EnvOnly` 실행 시 로컬 .env가 observer-deploy/.env와 observer/secrets/.env 둘 다 업로드·복사됨.
5. **검증**: 서버에서 `docker exec observer env | grep KIS_APP` 로 KIS 주입 여부 확인.
