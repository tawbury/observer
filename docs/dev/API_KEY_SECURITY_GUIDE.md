# API 키 보안 가이드

## 🔒 보안 원칙

**절대 금지:**
- ❌ .env 파일을 Git에 커밋
- ❌ API 키를 코드에 하드코딩
- ❌ .env 파일을 SCP/FTP로 직접 전송
- ❌ 공개 저장소에 키 노출
- ❌ 채팅/이메일/Slack에 키 붙여넣기

**권장 방법:**
- ✅ SSH로 서버 접속 후 직접 생성
- ✅ 파일 권한 600 (소유자만 읽기/쓰기)
- ✅ 정기적으로 키 교체
- ✅ 테스트 완료 후 즉시 새 키 발급
- ✅ .gitignore에 .env 포함 확인

---

## 📋 배포 방법 (VM 기준)

### 1. SSH로 VM 접속

```bash
ssh observer-vm
```

### 2. 배포 디렉토리로 이동

```bash
cd ~/observer-deploy
```

### 3. .env 파일 안전하게 생성

**Option A: nano 에디터 사용 (권장)**
```bash
nano .env
```

다음 내용 입력:
```bash
# KIS API 인증 정보
KIS_APP_KEY=실제_앱_키를_여기에
KIS_APP_SECRET=실제_시크릿_키를_여기에
KIS_IS_VIRTUAL=false

# PostgreSQL 설정
DB_HOST=postgres
DB_USER=postgres
DB_PASSWORD=observer_db_pwd
DB_NAME=observer
DB_PORT=5432
```

저장: `Ctrl + O` → Enter → `Ctrl + X`

**Option B: heredoc 사용 (복사 불편할 때)**
```bash
cat > .env << 'EOF'
KIS_APP_KEY=실제_앱_키를_여기에
KIS_APP_SECRET=실제_시크릿_키를_여기에
KIS_IS_VIRTUAL=false

DB_HOST=postgres
DB_USER=postgres
DB_PASSWORD=observer_db_pwd
DB_NAME=observer
DB_PORT=5432
EOF
```

**Option C: echo 명령어로 한 줄씩**
```bash
echo "KIS_APP_KEY=실제_앱_키" > .env
echo "KIS_APP_SECRET=실제_시크릿_키" >> .env
echo "KIS_IS_VIRTUAL=false" >> .env
echo "" >> .env
echo "DB_HOST=postgres" >> .env
echo "DB_USER=postgres" >> .env
echo "DB_PASSWORD=observer_db_pwd" >> .env
echo "DB_NAME=observer" >> .env
echo "DB_PORT=5432" >> .env
```

### 4. 파일 권한 설정 (중요!)

```bash
# 소유자만 읽기/쓰기 가능 (600)
chmod 600 .env

# 확인
ls -la .env
# 출력 예시: -rw------- 1 azureuser azureuser 234 Jan 22 10:00 .env
```

### 5. 확인 (키는 안 보임)

```bash
# 파일 존재 확인
test -f .env && echo "✅ .env 파일 존재" || echo "❌ .env 파일 없음"

# 권한 확인
stat -c "%a %n" .env
# 출력: 600 .env
```

### 6. Docker Compose 재시작

```bash
docker compose down
docker compose up -d

# 로그에서 Universe Scheduler 확인
docker compose logs observer | grep "Universe Scheduler"
```

---

## 🔑 로컬 개발 환경

로컬에서도 동일한 방식으로 `.env` 파일을 생성하되, **절대 Git에 추가하지 마세요**.

### Windows (PowerShell)
```powershell
# obs_deploy 디렉토리에서
cd app\obs_deploy

# .env 파일 생성
@"
KIS_APP_KEY=로컬_테스트_앱_키
KIS_APP_SECRET=로컬_테스트_시크릿_키
KIS_IS_VIRTUAL=true

DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=observer_db_pwd
DB_NAME=observer
DB_PORT=5432
"@ | Out-File -FilePath .env -Encoding UTF8
```

### 확인 (.gitignore)
```powershell
# .env가 무시되는지 확인
git status

# .env가 나타나면 안됨!
# 만약 나타나면:
git check-ignore .env
# 출력: .env (정상)
```

---

## 🔄 키 교체 프로세스 (테스트 완료 후)

### 1. 한국투자증권에서 새 API 키 발급
1. https://apiportal.koreainvestment.com/ 로그인
2. 기존 키 삭제
3. 새 앱키/시크릿 발급
4. **즉시 안전한 곳에 백업** (비밀번호 관리자 추천)

### 2. VM에서 키 업데이트
```bash
ssh observer-vm
cd ~/observer-deploy

# 기존 .env 백업 (선택)
cp .env .env.backup

# 새 키로 업데이트
nano .env
# KIS_APP_KEY, KIS_APP_SECRET만 변경

# 재시작
docker compose down
docker compose up -d
```

### 3. 로컬에서도 동일하게 업데이트

---

## 🛡️ 추가 보안 조치

### Azure Key Vault 사용 (고급 - 선택사항)

프로덕션 환경에서는 Azure Key Vault를 사용하는 것이 가장 안전합니다:

```bash
# 1. Key Vault 생성 (한 번만)
az keyvault create \
  --name observer-keyvault \
  --resource-group RG-OBSERVER-TEST \
  --location koreacentral

# 2. API 키 저장
az keyvault secret set \
  --vault-name observer-keyvault \
  --name KIS-APP-KEY \
  --value "실제_앱_키"

az keyvault secret set \
  --vault-name observer-keyvault \
  --name KIS-APP-SECRET \
  --value "실제_시크릿_키"

# 3. VM에서 키 가져오기
KIS_APP_KEY=$(az keyvault secret show \
  --vault-name observer-keyvault \
  --name KIS-APP-KEY \
  --query value -o tsv)

echo "KIS_APP_KEY=$KIS_APP_KEY" > .env
```

**장점:**
- 키가 파일 시스템에 저장 안됨
- 감사 로그 자동 기록
- 접근 권한 세밀하게 제어

**단점:**
- 설정이 복잡함
- Azure CLI 필요

---

## ⚠️ 노출 사고 발생 시 대응

키가 노출되었다면 (Git 커밋, 공개 채널 등):

### 즉시 조치
1. **한국투자증권 API 포털에서 키 즉시 삭제**
2. 새 키 발급
3. 모든 서버/로컬 환경 업데이트
4. Git 히스토리에 키가 있다면:
   ```bash
   # Git 히스토리에서 완전 제거 (신중하게!)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch app/obs_deploy/.env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # 원격 저장소 강제 푸시 (팀원과 협의 필요)
   git push origin --force --all
   ```

### 예방 조치
- Pre-commit hook 설정 (키 검사)
- GitHub Secret Scanning 활성화
- 정기적 키 교체 (3개월마다)

---

## 📝 체크리스트

**배포 전:**
- [ ] `.gitignore`에 `.env` 포함 확인
- [ ] Git status에서 `.env` 안 나타나는지 확인
- [ ] 로컬 `.env`는 테스트 키만 사용

**배포 시:**
- [ ] SSH로 서버 접속
- [ ] 서버에서 직접 `.env` 생성
- [ ] 파일 권한 600 설정
- [ ] Docker Compose 재시작
- [ ] 로그에서 정상 작동 확인

**테스트 완료 후:**
- [ ] API 키 즉시 재발급
- [ ] 모든 환경 업데이트
- [ ] 구 키 완전 삭제

---

## 🎯 요약

**가장 안전한 방법:**
1. SSH로 서버 직접 접속
2. nano/vi로 .env 파일 직접 생성
3. chmod 600 권한 설정
4. 절대 파일 전송/복사 금지
5. Git 커밋 금지

**파일 위치:**
- VM: `~/observer-deploy/.env`
- 로컬: `app/obs_deploy/.env`
- 둘 다 Git에 커밋되면 안됨!

**테스트 완료 후 즉시:**
- 한국투자증권에서 새 키 발급
- 모든 환경 업데이트
- 구 키 삭제

---

**Last Updated**: 2026-01-22  
**Version**: 1.0
