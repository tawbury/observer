#!/usr/bin/env node

/**
 * Setup script for AI Tool MCP Server
 * Automatically configures Claude Code to use this MCP server
 */

import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import os from "os";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 색상 코드 (터미널 출력용)
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function colorize(text, color) {
  return `${color}${text}${colors.reset}`;
}

// Determine Claude config path based on OS
function getClaudeConfigPath() {
  const platform = os.platform();
  const homeDir = os.homedir();

  switch (platform) {
    case "win32":
      return path.join(process.env.APPDATA || path.join(homeDir, "AppData", "Roaming"), "Claude", "claude_desktop_config.json");
    case "darwin":
      return path.join(homeDir, "Library", "Application Support", "Claude", "claude_desktop_config.json");
    case "linux":
      return path.join(homeDir, ".config", "claude", "claude_desktop_config.json");
    default:
      throw new Error(`Unsupported platform: ${platform}`);
  }
}

// 프로젝트 이름 자동 감지
function detectProjectName() {
  const projectRoot = path.resolve(__dirname, "..");
  return path.basename(projectRoot);
}

// 기존 설정에서 충돌하는 서버 이름 찾기
function findConflictingServerName(existingServers, preferredName) {
  if (!existingServers[preferredName]) {
    return preferredName;
  }

  // 충돌 시 번호 추가
  let counter = 1;
  let newName = `${preferredName}-${counter}`;
  while (existingServers[newName]) {
    counter++;
    newName = `${preferredName}-${counter}`;
  }
  return newName;
}

async function setup() {
  console.log(colorize("\n🚀 AI Tool MCP Server Setup\n", colors.bright + colors.cyan));

  // Get paths
  const serverPath = path.resolve(__dirname, "index.js");
  const aiFolderPath = path.resolve(__dirname, "../.ai");
  const configPath = getClaudeConfigPath();
  const projectName = detectProjectName();

  console.log(colorize("📁 감지된 정보:", colors.bright));
  console.log(`   프로젝트명: ${colorize(projectName, colors.yellow)}`);
  console.log(`   MCP 서버: ${colorize(serverPath, colors.blue)}`);
  console.log(`   .ai 폴더: ${colorize(aiFolderPath, colors.blue)}`);
  console.log(`   Claude 설정: ${colorize(configPath, colors.blue)}\n`);

  // Verify .ai folder exists
  try {
    await fs.access(aiFolderPath);
    console.log(colorize("✅ .ai 폴더 확인됨", colors.green));
  } catch (error) {
    console.error(colorize("❌ .ai 폴더를 찾을 수 없습니다:", colors.red), aiFolderPath);
    console.error(colorize("   부모 디렉토리에 .ai 폴더가 있는지 확인해주세요", colors.yellow));
    console.error(colorize("\n💡 해결 방법:", colors.cyan));
    console.error("   1. 템플릿에서 .ai 폴더를 복사:");
    if (os.platform() === 'win32') {
      console.error(`      xcopy /E /I <템플릿경로>\\.ai ${path.dirname(aiFolderPath)}\\.ai`);
    } else {
      console.error(`      cp -r <템플릿경로>/.ai ${path.dirname(aiFolderPath)}/.ai`);
    }
    console.error("   2. 다시 setup 실행: npm run setup\n");
    process.exit(1);
  }

  // MCP 서버 이름 결정 (프로젝트명 기반)
  const baseServerName = `${projectName}-ai`;

  // Prepare MCP server configuration
  const mcpConfig = {
    command: "node",
    args: [serverPath],
    env: {
      AI_FOLDER_PATH: aiFolderPath
    },
    disabled: false,
    alwaysAllow: [
      "list_available",
      "get_workflow",
      "get_skill",
      "get_agent",
      "get_validator",
      "get_template",
      "execute_workflow"
    ]
  };

  // Read or create Claude config
  let claudeConfig = { mcpServers: {} };
  let isNewConfig = false;
  let serverName = baseServerName;

  try {
    const configDir = path.dirname(configPath);
    await fs.mkdir(configDir, { recursive: true });

    try {
      const existingConfig = await fs.readFile(configPath, "utf-8");
      claudeConfig = JSON.parse(existingConfig);
      console.log(colorize("📝 기존 Claude 설정 파일 발견", colors.green));

      // mcpServers가 없으면 추가
      if (!claudeConfig.mcpServers) {
        claudeConfig.mcpServers = {};
      }

      // 충돌하는 서버 이름이 있는지 확인
      if (claudeConfig.mcpServers[baseServerName]) {
        const existingPath = claudeConfig.mcpServers[baseServerName].args?.[0];
        if (existingPath && existingPath !== serverPath) {
          serverName = findConflictingServerName(claudeConfig.mcpServers, baseServerName);
          console.log(colorize(`⚠️  "${baseServerName}" 이름이 이미 사용 중입니다`, colors.yellow));
          console.log(colorize(`   새 이름 사용: "${serverName}"`, colors.yellow));
        } else if (existingPath === serverPath) {
          console.log(colorize(`♻️  기존 설정 업데이트: "${baseServerName}"`, colors.cyan));
        }
      }
    } catch (error) {
      console.log(colorize("📝 새로운 Claude 설정 파일 생성", colors.green));
      isNewConfig = true;
    }

    // Add or update MCP server configuration
    claudeConfig.mcpServers[serverName] = mcpConfig;

    // Write updated config
    await fs.writeFile(configPath, JSON.stringify(claudeConfig, null, 2), "utf-8");

    console.log(colorize("\n✅ MCP 서버 설정 완료!\n", colors.bright + colors.green));

    console.log(colorize("📋 적용된 설정:", colors.bright));
    console.log(colorize(JSON.stringify({ [serverName]: mcpConfig }, null, 2), colors.blue));

    console.log(colorize("\n⚠️  중요: Claude Code를 재시작해야 변경사항이 적용됩니다", colors.bright + colors.yellow));

    console.log(colorize("\n🎉 설정 완료!", colors.bright + colors.green));
    console.log(colorize("\nℹ️  Claude Code에서 사용 가능한 도구:", colors.cyan));
    console.log("   • list_available - 모든 워크플로우, 스킬, 에이전트 목록");
    console.log("   • get_workflow - 특정 워크플로우 로드");
    console.log("   • get_skill - 특정 스킬 로드");
    console.log("   • get_agent - 특정 에이전트 로드");
    console.log("   • execute_workflow - 워크플로우 실행");

    console.log(colorize("\n💡 테스트 방법:", colors.cyan));
    console.log('   Claude Code에서 다음과 같이 입력해보세요:');
    console.log(colorize('   "사용 가능한 워크플로우를 보여줘"', colors.yellow));
    console.log(colorize('   "List all available workflows"', colors.yellow));

    if (!isNewConfig) {
      console.log(colorize("\n📌 참고:", colors.cyan));
      console.log("   기존 설정 파일에 추가되었습니다.");
      console.log(`   다른 MCP 서버가 ${Object.keys(claudeConfig.mcpServers).length - 1}개 있습니다.`);
    }

    console.log(colorize("\n📚 자세한 사용법:", colors.cyan));
    console.log("   README.md - 기본 설정 및 개요");
    console.log("   USAGE_GUIDE.md - 상세한 사용 예제");
    console.log("   STEP_BY_STEP_GUIDE.md - 단계별 적용 가이드\n");

  } catch (error) {
    console.error(colorize("\n❌ 설정 중 오류 발생:", colors.red), error.message);
    console.error(colorize("\n📝 수동 설정이 필요합니다:", colors.yellow));
    console.error(`   설정 파일 위치: ${colorize(configPath, colors.blue)}`);
    console.error("\n   다음 내용을 추가하세요:\n");
    console.error(colorize(JSON.stringify({ mcpServers: { [serverName]: mcpConfig } }, null, 2), colors.yellow));

    console.error(colorize("\n💡 일반적인 오류 해결 방법:", colors.cyan));
    console.error("   1. 파일 권한 확인");
    if (os.platform() === 'win32') {
      console.error("      - 관리자 권한으로 PowerShell 실행");
    } else {
      console.error("      - sudo 권한 또는 파일 소유권 확인");
    }
    console.error("   2. 설정 폴더가 존재하는지 확인");
    console.error(`      ${path.dirname(configPath)}`);
    console.error("   3. JSON 파일이 손상되지 않았는지 확인\n");

    process.exit(1);
  }
}

// 에러 핸들링
process.on('unhandledRejection', (error) => {
  console.error(colorize("\n❌ 예기치 않은 오류:", colors.red), error);
  process.exit(1);
});

setup().catch((error) => {
  console.error(colorize("\n❌ 심각한 오류:", colors.red), error);
  process.exit(1);
});
