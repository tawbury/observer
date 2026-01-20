# 빠른 시작 가이드 (Quick Start)

MCP 서버를 **5분 안에** 새 프로젝트에 적용하는 방법입니다.

## 🚀 3단계로 시작하기

### 1단계: 폴더 복사 (1분)

```bash
# 새 프로젝트 폴더로 이동
cd D:\projects\my-new-project

# 템플릿에서 필요한 폴더 2개만 복사
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server
```

**Mac/Linux:**
```bash
cd ~/projects/my-new-project
cp -r ~/templates/aI_tool/.ai ./.ai
cp -r ~/templates/aI_tool/mcp-server ./mcp-server
```

### 2단계: 설치 및 설정 (2분)

```bash
cd mcp-server
npm install
npm run setup
```

### 3단계: Claude Code 재시작 (1분)

Claude Code를 완전히 종료하고 다시 시작합니다.

## ✅ 테스트

Claude Code에서 다음과 같이 입력:

```
"사용 가능한 워크플로우를 보여줘"
```

또는

```
"List all available workflows"
```

응답이 오면 성공! 🎉

---

## 📁 복사된 파일 구조

```
my-new-project/
├── .ai/              ← AI 시스템 (워크플로우, 스킬, 에이전트)
├── mcp-server/       ← MCP 서버
│   ├── node_modules/ ← npm install로 생성됨
│   ├── index.js
│   ├── setup.js
│   └── package.json
└── (여기에 프로젝트 파일 작성)
```

---

## 🔧 자동으로 설정되는 것들

`npm run setup` 실행 시:

1. ✅ **프로젝트 이름 자동 감지**
   - 폴더 이름에서 자동 추출
   - 예: `my-new-project` → MCP 서버 이름: `my-new-project-ai`

2. ✅ **경로 자동 설정**
   - MCP 서버 경로: 절대 경로로 자동 설정
   - .ai 폴더 경로: 절대 경로로 자동 설정

3. ✅ **Claude 설정 파일 자동 업데이트**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/claude/claude_desktop_config.json`

4. ✅ **충돌 방지**
   - 같은 이름의 MCP 서버가 있으면 번호 추가
   - 예: `my-project-ai` → `my-project-ai-1`

---

## 💡 자주 묻는 질문 (FAQ)

### Q1: .ai 폴더가 없다고 나옵니다

**A:** 템플릿에서 .ai 폴더를 복사했는지 확인하세요.

```bash
# 다시 복사
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
```

### Q2: npm install 에러가 납니다

**A:** Node.js 버전을 확인하세요 (18 이상 필요).

```bash
node --version

# 18 미만이면 Node.js 업데이트 필요
# https://nodejs.org
```

### Q3: Claude Code에서 도구가 안 보입니다

**A:** 다음을 확인하세요:
1. Claude Code를 **완전히 종료**했나요? (작업 관리자 확인)
2. **재시작**했나요?
3. 설정 파일이 올바른가요?

```bash
# Windows - 설정 파일 확인
notepad %APPDATA%\Claude\claude_desktop_config.json

# Mac
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Q4: 여러 프로젝트에서 사용하려면?

**A:** 각 프로젝트에서 1-3단계를 반복하면 됩니다.

자동으로 프로젝트별 고유 이름이 생성됩니다:
- `ecommerce-ai`
- `blog-platform-ai`
- `mobile-app-ai`

---

## 🎯 다음 단계

설정이 완료되었다면:

1. **워크플로우 실행해보기**
   ```
   "Execute the software development workflow"
   ```

2. **스킬 탐색하기**
   ```
   "Show me all developer skills"
   ```

3. **에이전트 확인하기**
   ```
   "Load the developer agent"
   ```

---

## 📚 더 알아보기

- [README.md](README.md) - 전체 기능 소개
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - 상세 사용법
- [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md) - 시나리오별 가이드

---

## 🆘 문제 해결

문제가 계속되면:

1. [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md)의 트러블슈팅 섹션 확인
2. 설정 파일 직접 수정 (setup.js가 출력한 내용 복사)
3. GitHub 이슈 등록

---

**축하합니다! 이제 모든 프로젝트에서 AI 도움을 받을 수 있습니다!** 🎉
