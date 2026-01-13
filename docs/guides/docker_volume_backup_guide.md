# Docker 볼륨 백업 및 복구 절차

이 문서는 QTS Ops 프로젝트의 Docker 볼륨(데이터/로그 등) 백업 및 복구 절차를 정리합니다.

## 1. 볼륨 백업
- 컨테이너가 사용하는 볼륨(예: /app/data, /app/logs 등)을 주기적으로 백업
- 예시: 운영 서버에서 rsync, tar, azcopy 등으로 백업

### tar 명령어 예시
```sh
docker run --rm -v qts-observer-data:/data -v $(pwd):/backup busybox tar czf /backup/data_backup_$(date +%Y%m%d).tar.gz -C /data .
```
- 위 명령은 qts-observer-data 볼륨 전체를 tar.gz로 백업

## 2. 볼륨 복구
- 백업 파일을 볼륨에 복원
- 예시:
```sh
docker run --rm -v qts-observer-data:/data -v $(pwd):/backup busybox tar xzf /backup/data_backup_YYYYMMDD.tar.gz -C /data
```

## 3. Azure Storage/Blob 연동
- 백업 파일을 Azure Storage에 업로드하여 장기 보관 가능
- 예시:
```sh
az storage blob upload --account-name observerstorage --container-name backup --name data_backup_YYYYMMDD.tar.gz --file ./data_backup_YYYYMMDD.tar.gz
```

## 4. 자동화
- ops-automation.sh 등에서 주기적 백업/업로드 스크립트로 자동화 가능

## 참고
- 복구 전 컨테이너 중지 권장 (docker-compose down)
- 복구 후 컨테이너 재시작 및 데이터 정상 여부 확인
