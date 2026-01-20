# MCP 서버 적용 완벽 가이드

실제 프로젝트에 MCP 서버를 적용하는 과정을 단계별로 상세히 설명합니다.

## 📋 목차
1. [프로젝트 유형별 적용 방법](#프로젝트-유형별-적용-방법)
2. [파일 이동 및 설정](#파일-이동-및-설정)
3. [설정 후 변경이 필요한 사항](#설정-후-변경이-필요한-사항)
4. [실전 예제](#실전-예제)
5. [트러블슈팅](#트러블슈팅)

---

## 프로젝트 유형별 적용 방법

### 시나리오 1: 완전히 새로운 프로젝트 시작

#### 상황
```
내 컴퓨터에 새로운 e-commerce 프로젝트를 시작하려고 합니다.
템플릿의 .ai 시스템을 모두 활용하고 싶습니다.
```

#### 단계별 실행

**1단계: 프로젝트 폴더 생성**
```bash
# Windows
mkdir D:\projects\my-ecommerce
cd D:\projects\my-ecommerce

# Mac/Linux
mkdir ~/projects/my-ecommerce
cd ~/projects/my-ecommerce
```

**2단계: 템플릿에서 필요한 폴더 복사**
```bash
# Windows
xcopy /E /I D:\development\_templates\aI_tool\.ai D:\projects\my-ecommerce\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server D:\projects\my-ecommerce\mcp-server

# Mac/Linux
cp -r ~/templates/aI_tool/.ai ~/projects/my-ecommerce/.ai
cp -r ~/templates/aI_tool/mcp-server ~/projects/my-ecommerce/mcp-server
```

**3단계: MCP 서버 설치**
```bash
cd mcp-server
npm install
```

**4단계: 설정 실행**
```bash
npm run setup
```

**5단계: 생성된 프로젝트 구조 확인**
```
my-ecommerce/
├── .ai/                          ← 복사됨
│   ├── agents/
│   ├── skills/
│   ├── workflows/
│   ├── validators/
│   └── templates/
├── mcp-server/                   ← 복사됨
│   ├── node_modules/            ← npm install로 생성됨
│   ├── index.js
│   ├── setup.js
│   └── package.json
└── (여기에 프로젝트 코드 작성)
```

**6단계: Claude Code 설정 확인**

setup.js가 자동으로 다음 파일을 수정했습니다:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/claude/claude_desktop_config.json`

내용 확인:
```json
{
  "mcpServers": {
    "ai-tool-workflows": {
      "command": "node",
      "args": ["D:\\projects\\my-ecommerce\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\my-ecommerce\\.ai"
      },
      "disabled": false,
      "alwaysAllow": [
        "list_available",
        "get_workflow",
        "get_skill",
        "get_agent",
        "get_validator",
        "get_template",
        "execute_workflow"
      ]
    }
  }
}
```

**7단계: Claude Code 재시작**

**8단계: 테스트**
```
Claude Code에서:
"사용 가능한 워크플로우를 보여줘"
```

---

### 시나리오 2: 기존 프로젝트에 추가

#### 상황
```
이미 진행 중인 blog-platform 프로젝트가 있습니다.
여기에 .ai 시스템을 추가하고 싶습니다.
```

#### 단계별 실행

**1단계: 기존 프로젝트로 이동**
```bash
cd D:\projects\blog-platform
```

**2단계: .ai 폴더와 mcp-server 추가**
```bash
# 템플릿에서 복사
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server
```

**3단계: MCP 서버 설치 및 설정**
```bash
cd mcp-server
npm install
npm run setup
```

**4단계: .gitignore 업데이트 (Git 사용시)**
```bash
# 프로젝트 루트의 .gitignore에 추가
echo "" >> ../.gitignore
echo "# AI Tool MCP Server" >> ../.gitignore
echo "mcp-server/node_modules/" >> ../.gitignore
echo "mcp-server/package-lock.json" >> ../.gitignore
```

**5단계: README 업데이트**
```markdown
# 프로젝트 README.md에 추가

## AI Assistant Setup

This project uses AI Tool MCP Server for AI-assisted development.

### Setup
1. Install MCP server: `cd mcp-server && npm install`
2. Run setup: `npm run setup`
3. Restart Claude Code

See [mcp-server/README.md](mcp-server/README.md) for details.
```

---

### 시나리오 3: 여러 프로젝트에서 동시 사용 (추천)

#### 상황
```
프로젝트가 여러 개 있고, 프로젝트를 전환하면서 사용하고 싶습니다.
- my-ecommerce
- blog-platform
- mobile-app
```

#### 방법 A: 각 프로젝트마다 별도 MCP 서버 (추천)

**각 프로젝트별 설정**
```bash
# 프로젝트 1
cd D:\projects\my-ecommerce
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server
cd mcp-server && npm install && npm run setup

# 프로젝트 2
cd D:\projects\blog-platform
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server
cd mcp-server && npm install && npm run setup

# 프로젝트 3
cd D:\projects\mobile-app
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server
cd mcp-server && npm install && npm run setup
```

**설정 파일 (claude_desktop_config.json) - 각 프로젝트마다 이름 변경**

첫 번째 프로젝트 후:
```json
{
  "mcpServers": {
    "ecommerce-ai": {
      "command": "node",
      "args": ["D:\\projects\\my-ecommerce\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\my-ecommerce\\.ai"
      }
    }
  }
}
```

두 번째 프로젝트 후 (기존 설정에 추가):
```json
{
  "mcpServers": {
    "ecommerce-ai": {
      "command": "node",
      "args": ["D:\\projects\\my-ecommerce\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\my-ecommerce\\.ai"
      }
    },
    "blog-ai": {
      "command": "node",
      "args": ["D:\\projects\\blog-platform\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\blog-platform\\.ai"
      }
    }
  }
}
```

**프로젝트별 MCP 서버 활성화/비활성화**

사용하지 않는 프로젝트는 비활성화:
```json
{
  "mcpServers": {
    "ecommerce-ai": {
      "command": "node",
      "args": ["D:\\projects\\my-ecommerce\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\my-ecommerce\\.ai"
      },
      "disabled": false    // ← 현재 작업 중인 프로젝트
    },
    "blog-ai": {
      "command": "node",
      "args": ["D:\\projects\\blog-platform\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\blog-platform\\.ai"
      },
      "disabled": true     // ← 사용하지 않는 프로젝트
    }
  }
}
```

#### 방법 B: 하나의 MCP 서버로 여러 프로젝트 관리

**1단계: 중앙 위치에 MCP 서버 설치**
```bash
# Windows
mkdir D:\tools\ai-mcp-server
xcopy /E /I D:\development\_templates\aI_tool\mcp-server D:\tools\ai-mcp-server
cd D:\tools\ai-mcp-server
npm install
```

**2단계: 각 프로젝트에 .ai 폴더만 복사**
```bash
xcopy /E /I D:\development\_templates\aI_tool\.ai D:\projects\my-ecommerce\.ai
xcopy /E /I D:\development\_templates\aI_tool\.ai D:\projects\blog-platform\.ai
xcopy /E /I D:\development\_templates\aI_tool\.ai D:\projects\mobile-app\.ai
```

**3단계: 프로젝트 전환 스크립트 생성**

`D:\tools\switch-project.bat` 파일 생성:
```batch
@echo off
setlocal

set PROJECT_NAME=%1
set PROJECTS_DIR=D:\projects
set AI_FOLDER=%PROJECTS_DIR%\%PROJECT_NAME%\.ai
set CONFIG_FILE=%APPDATA%\Claude\claude_desktop_config.json

if not exist "%AI_FOLDER%" (
    echo Error: Project not found: %PROJECT_NAME%
    exit /b 1
)

echo Switching to project: %PROJECT_NAME%
echo AI Folder: %AI_FOLDER%

:: PowerShell로 JSON 파일 수정
powershell -Command "(Get-Content '%CONFIG_FILE%' | ConvertFrom-Json) | ForEach-Object { $_.mcpServers.'ai-tool-workflows'.env.AI_FOLDER_PATH = '%AI_FOLDER%'; $_ } | ConvertTo-Json -Depth 10 | Set-Content '%CONFIG_FILE%'"

echo Done! Please restart Claude Code.
```

**4단계: 프로젝트 전환**
```bash
# 커맨드 프롬프트에서
D:\tools\switch-project.bat my-ecommerce
# Claude Code 재시작

# 다른 프로젝트로 전환
D:\tools\switch-project.bat blog-platform
# Claude Code 재시작
```

---

## 파일 이동 및 설정

### 반드시 이동해야 하는 폴더/파일

#### 필수 (Mandatory)
```
✅ .ai/                    # AI 시스템 전체
✅ mcp-server/index.js     # MCP 서버 메인 파일
✅ mcp-server/setup.js     # 설정 스크립트
✅ mcp-server/package.json # 의존성 정의
```

#### 선택 (Optional)
```
📄 mcp-server/README.md              # 설명서 (팀원용)
📄 mcp-server/USAGE_GUIDE.md         # 사용 가이드
📄 mcp-server/TEMPLATE_DEPLOYMENT.md # 배포 가이드
📄 mcp-server/.env.example           # 환경 변수 예제
📄 mcp-server/.gitignore             # Git 제외 파일
```

### 이동하지 말아야 할 것들

```
❌ mcp-server/node_modules/     # npm install로 생성됨
❌ .ai의 개별 수정된 파일       # 프로젝트별로 커스터마이징
❌ 템플릿 전체                   # 원본 유지
```

---

## 설정 후 변경이 필요한 사항

### 1. setup.js 실행 후 자동 설정되는 내용

`npm run setup` 실행 시 자동으로:
- ✅ Claude Code 설정 파일 찾기
- ✅ MCP 서버 경로 자동 설정
- ✅ .ai 폴더 경로 자동 설정
- ✅ 도구 권한 자동 허용

### 2. 수동으로 확인/변경해야 하는 내용

#### A. Claude Code 설정 파일 확인

위치:
```
Windows: %APPDATA%\Claude\claude_desktop_config.json
Mac:     ~/Library/Application Support/Claude/claude_desktop_config.json
Linux:   ~/.config/claude/claude_desktop_config.json
```

확인할 내용:
```json
{
  "mcpServers": {
    "ai-tool-workflows": {
      "command": "node",           // ← Node.js 경로 (보통 자동)
      "args": ["절대경로"],         // ← 반드시 절대 경로여야 함
      "env": {
        "AI_FOLDER_PATH": "절대경로" // ← 반드시 절대 경로여야 함
      }
    }
  }
}
```

#### B. 여러 프로젝트 사용 시 서버 이름 변경

**변경 전 (기본값):**
```json
{
  "mcpServers": {
    "ai-tool-workflows": { ... }  // ← 모든 프로젝트가 같은 이름
  }
}
```

**변경 후 (프로젝트별):**
```json
{
  "mcpServers": {
    "ecommerce-ai": { ... },      // ← 프로젝트별 고유 이름
    "blog-ai": { ... },
    "mobile-ai": { ... }
  }
}
```

setup.js를 수정하여 프로젝트 이름 자동 감지:

```javascript
// setup.js 수정 예시
import path from "path";

const projectName = path.basename(path.resolve(__dirname, ".."));
const serverName = `${projectName}-ai`;

// 설정에서 사용
claudeConfig.mcpServers[serverName] = mcpConfig;
```

#### C. Node.js 경로 문제 (특히 nvm 사용자)

**문제:** nvm으로 여러 Node 버전 사용 시 경로 문제

**해결:**
```json
{
  "mcpServers": {
    "ai-tool-workflows": {
      "command": "C:\\Program Files\\nodejs\\node.exe",  // ← 명시적 경로
      // 또는
      "command": "/usr/local/bin/node",                  // ← Mac/Linux
      "args": ["..."]
    }
  }
}
```

Node.js 경로 찾기:
```bash
# Windows
where node

# Mac/Linux
which node
```

#### D. 환경 변수 커스터마이징

`.env` 파일 생성 (선택사항):
```bash
# mcp-server/.env
AI_FOLDER_PATH=D:\projects\my-ecommerce\.ai
NODE_ENV=production
DEBUG=false
```

index.js에서 환경 변수 사용:
```javascript
import dotenv from 'dotenv';
dotenv.config();

const AI_FOLDER = process.env.AI_FOLDER_PATH || path.resolve(__dirname, "../.ai");
```

---

## 실전 예제

### 예제 1: 신규 React 프로젝트에 적용

```bash
# 1. React 프로젝트 생성
npx create-react-app my-react-app
cd my-react-app

# 2. AI 시스템 추가
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server

# 3. MCP 서버 설치
cd mcp-server
npm install

# 4. 설정 (프로젝트 이름 반영)
npm run setup

# 5. .gitignore 업데이트
echo "mcp-server/node_modules/" >> ../.gitignore

# 6. Claude Code 재시작

# 7. 테스트
# Claude Code에서: "Execute the software development workflow"
```

**프로젝트 구조:**
```
my-react-app/
├── .ai/
├── mcp-server/
├── public/
├── src/
├── package.json
└── README.md
```

### 예제 2: 팀 프로젝트 설정

**프로젝트 리더 (초기 설정):**
```bash
# 1. 프로젝트 생성
mkdir team-project
cd team-project

# 2. Git 초기화
git init

# 3. AI 시스템 추가
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server

# 4. .gitignore 설정
echo "mcp-server/node_modules/" > .gitignore
echo "mcp-server/package-lock.json" >> .gitignore

# 5. README에 설정 방법 추가
cat > README.md << EOF
# Team Project

## AI Assistant Setup

팀원들은 다음 단계를 따라주세요:

1. 리포지토리 클론
2. MCP 서버 설정:
   \`\`\`bash
   cd mcp-server
   npm install
   npm run setup
   \`\`\`
3. Claude Code 재시작
4. 테스트: "List all available workflows"

자세한 사용법: [mcp-server/USAGE_GUIDE.md](mcp-server/USAGE_GUIDE.md)
EOF

# 6. Git 커밋
git add .
git commit -m "Add AI system with MCP server"
git push
```

**팀원 (클론 후 설정):**
```bash
# 1. 리포지토리 클론
git clone https://github.com/team/team-project.git
cd team-project

# 2. MCP 서버 설정
cd mcp-server
npm install
npm run setup

# 3. Claude Code 재시작

# 4. 테스트
# Claude Code에서: "List all available skills"
```

### 예제 3: 모노레포 (Monorepo) 구조

```
my-monorepo/
├── .ai/                    # 전체 모노레포 공통 AI 시스템
├── mcp-server/             # 루트 레벨 MCP 서버
├── packages/
│   ├── frontend/
│   │   └── .ai/           # (선택) 프론트엔드 전용 AI 설정
│   ├── backend/
│   │   └── .ai/           # (선택) 백엔드 전용 AI 설정
│   └── mobile/
│       └── .ai/           # (선택) 모바일 전용 AI 설정
└── package.json
```

**설정:**
```bash
# 루트 레벨 MCP 서버 (전체 프로젝트용)
cd my-monorepo
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
xcopy /E /I D:\development\_templates\aI_tool\mcp-server .\mcp-server
cd mcp-server && npm install && npm run setup

# 개별 패키지용 (선택)
cd packages/frontend
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai
# (MCP 서버는 루트 것을 사용, AI 폴더만 따로)
```

---

## 트러블슈팅

### 문제 1: setup.js 실행 시 "AI folder not found" 에러

**원인:** .ai 폴더가 없거나 경로가 잘못됨

**해결:**
```bash
# 1. .ai 폴더 존재 확인
dir .ai  # Windows
ls -la .ai  # Mac/Linux

# 2. 없으면 다시 복사
xcopy /E /I D:\development\_templates\aI_tool\.ai .\.ai

# 3. setup.js 다시 실행
cd mcp-server
npm run setup
```

### 문제 2: Claude Code에서 도구가 보이지 않음

**원인:** 설정 파일 경로 문제 또는 Claude Code 미재시작

**해결:**
```bash
# 1. 설정 파일 확인
# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json

# Mac
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 2. 경로가 절대 경로인지 확인
# ❌ 잘못된 예: "./mcp-server/index.js"
# ✅ 올바른 예: "D:\\projects\\my-project\\mcp-server\\index.js"

# 3. Claude Code 완전히 종료 후 재시작
# (작업 관리자에서 프로세스 확인)
```

### 문제 3: 여러 프로젝트 간 전환이 안됨

**원인:** 같은 서버 이름 사용

**해결:**
수동으로 설정 파일 수정:
```json
{
  "mcpServers": {
    "project-a-ai": {
      "command": "node",
      "args": ["D:\\projects\\project-a\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\project-a\\.ai"
      },
      "disabled": true    // ← 사용 안 함
    },
    "project-b-ai": {
      "command": "node",
      "args": ["D:\\projects\\project-b\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\projects\\project-b\\.ai"
      },
      "disabled": false   // ← 현재 사용 중
    }
  }
}
```

### 문제 4: npm install 에러

**원인:** Node.js 버전 호환성 또는 네트워크 문제

**해결:**
```bash
# 1. Node.js 버전 확인 (18+ 필요)
node --version

# 2. npm 캐시 클리어
npm cache clean --force

# 3. 재설치
rm -rf node_modules package-lock.json  # Mac/Linux
del /F /S node_modules package-lock.json  # Windows

npm install

# 4. 여전히 문제면 yarn 사용
npm install -g yarn
yarn install
```

### 문제 5: 권한 문제 (Windows)

**원인:** 관리자 권한 필요

**해결:**
```bash
# PowerShell을 관리자 권한으로 실행 후
cd D:\projects\my-project\mcp-server
npm install
npm run setup
```

---

## 체크리스트

### 초기 설정 체크리스트

- [ ] .ai 폴더가 프로젝트에 복사됨
- [ ] mcp-server 폴더가 프로젝트에 복사됨
- [ ] `cd mcp-server && npm install` 실행
- [ ] `npm run setup` 실행 성공
- [ ] Claude Code 설정 파일에 올바른 경로 확인
- [ ] Claude Code 재시작
- [ ] "List all workflows" 테스트 성공

### 멀티 프로젝트 체크리스트

- [ ] 각 프로젝트마다 고유한 서버 이름 사용
- [ ] 현재 작업하지 않는 프로젝트는 disabled: true
- [ ] 프로젝트 전환 시 Claude Code 재시작
- [ ] 각 프로젝트의 .ai 폴더 경로 확인

### 팀 협업 체크리스트

- [ ] README에 설정 방법 문서화
- [ ] .gitignore에 node_modules 추가
- [ ] mcp-server 폴더를 Git에 커밋 (node_modules 제외)
- [ ] 팀원들에게 설정 가이드 공유
- [ ] 첫 테스트: "List all available resources"

---

## 빠른 참조

### 명령어 요약

```bash
# 새 프로젝트 설정
xcopy /E /I <template>\.ai .\.ai
xcopy /E /I <template>\mcp-server .\mcp-server
cd mcp-server && npm install && npm run setup

# 설정 파일 위치
# Windows: %APPDATA%\Claude\claude_desktop_config.json
# Mac:     ~/Library/Application Support/Claude/claude_desktop_config.json
# Linux:   ~/.config/claude/claude_desktop_config.json

# Claude Code 테스트
"List all available workflows"
```

### 디렉토리 구조

```
프로젝트/
├── .ai/              ← 필수: AI 시스템
├── mcp-server/       ← 필수: MCP 서버
│   ├── index.js
│   ├── setup.js
│   └── package.json
└── (프로젝트 파일들)
```
