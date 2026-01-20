# Template Deployment Guide

This guide explains how to use this MCP server template across multiple projects.

## Overview

The AI Tool MCP Server is designed to be a **reusable template** that can be deployed to any project using the `.ai` folder structure. This allows you to have consistent AI assistance across all your projects.

## Deployment Strategies

### Strategy 1: Global Installation (Recommended)

Use this template as a **single global MCP server** for all your projects.

#### Advantages
- ✅ One configuration for all projects
- ✅ Centralized updates and maintenance
- ✅ Consistent behavior across projects
- ✅ Less disk space usage

#### Setup

1. **Keep this template in a central location:**
   ```
   ~/ai-tools/mcp-server/
   or
   C:\Development\Templates\ai-tool\mcp-server\
   ```

2. **Run setup once:**
   ```bash
   cd ~/ai-tools/mcp-server
   npm install
   npm run setup
   ```

3. **For each project, create symlinks to the .ai folder:**
   ```bash
   # Linux/Mac
   ln -s /path/to/project/.ai ~/ai-tools/ai-systems/project-name

   # Windows (as Administrator)
   mklink /D C:\ai-tools\ai-systems\project-name C:\path\to\project\.ai
   ```

4. **Update environment variable for each project:**
   Edit your Claude config to switch between projects:
   ```json
   {
     "mcpServers": {
       "ai-tool-workflows": {
         "command": "node",
         "args": ["/home/user/ai-tools/mcp-server/index.js"],
         "env": {
           "AI_FOLDER_PATH": "/home/user/ai-systems/current-project"
         }
       }
     }
   }
   ```

### Strategy 2: Per-Project Installation

Deploy a **separate MCP server instance** for each project.

#### Advantages
- ✅ Project-specific configurations
- ✅ Independent versioning
- ✅ No configuration switching needed
- ✅ Complete isolation

#### Setup

1. **Copy the mcp-server folder to each project:**
   ```bash
   cp -r ~/templates/ai-tool/mcp-server /path/to/your-project/
   ```

2. **Install dependencies in each project:**
   ```bash
   cd /path/to/your-project/mcp-server
   npm install
   ```

3. **Run setup for each project:**
   ```bash
   npm run setup
   ```

4. **Each project gets its own MCP server entry:**
   ```json
   {
     "mcpServers": {
       "project-a-workflows": {
         "command": "node",
         "args": ["/path/to/project-a/mcp-server/index.js"],
         "env": {
           "AI_FOLDER_PATH": "/path/to/project-a/.ai"
         }
       },
       "project-b-workflows": {
         "command": "node",
         "args": ["/path/to/project-b/mcp-server/index.js"],
         "env": {
           "AI_FOLDER_PATH": "/path/to/project-b/.ai"
         }
       }
     }
   }
   ```

### Strategy 3: Hybrid Approach

Use a **shared server template** with **project-specific configurations**.

#### Advantages
- ✅ Central codebase, distributed configs
- ✅ Easy updates
- ✅ Project-specific customization
- ✅ Balanced approach

#### Setup

1. **Keep the server code central:**
   ```
   ~/templates/ai-tool/mcp-server/
   ```

2. **Create project-specific config files:**
   ```bash
   # In each project
   echo "AI_FOLDER_PATH=/path/to/this/project/.ai" > .ai-mcp-config
   ```

3. **Modify index.js to read project config:**
   ```javascript
   // Add to index.js
   import dotenv from 'dotenv';
   import { resolve } from 'path';

   // Try to load .ai-mcp-config from current directory
   const projectConfigPath = resolve(process.cwd(), '.ai-mcp-config');
   dotenv.config({ path: projectConfigPath });
   ```

4. **Configure Claude to use the central server:**
   ```json
   {
     "mcpServers": {
       "ai-tool-workflows": {
         "command": "node",
         "args": ["/home/user/templates/ai-tool/mcp-server/index.js"],
         "cwd": "/path/to/current/project"
       }
     }
   }
   ```

## Step-by-Step: Deploying to a New Project

### Prerequisites

Your new project should have:
```
your-project/
├── .ai/
│   ├── agents/
│   ├── skills/
│   ├── workflows/
│   ├── validators/
│   └── templates/
└── (your project files)
```

### Deployment Steps

#### Option A: Copy Template

```bash
# 1. Navigate to your project
cd /path/to/your-project

# 2. Copy the mcp-server folder
cp -r /path/to/ai-tool-template/mcp-server ./

# 3. Install dependencies
cd mcp-server
npm install

# 4. Run setup
npm run setup

# 5. Restart Claude Code
```

#### Option B: Git Submodule (for version-controlled projects)

```bash
# 1. Navigate to your project
cd /path/to/your-project

# 2. Add as submodule
git submodule add <your-template-repo-url> mcp-server

# 3. Install dependencies
cd mcp-server
npm install

# 4. Run setup
npm run setup

# 5. Restart Claude Code
```

#### Option C: NPM Link (for development)

```bash
# 1. In the template directory
cd /path/to/ai-tool-template/mcp-server
npm link

# 2. In your project directory
cd /path/to/your-project
mkdir mcp-server
cd mcp-server
npm link @ai-tool/mcp-server

# 3. Create a wrapper script
echo '#!/usr/bin/env node
require("@ai-tool/mcp-server");
' > index.js

# 4. Make executable
chmod +x index.js

# 5. Run setup (modify setup.js for linked install)
```

## Managing Multiple Projects

### Switching Between Projects

If using a global installation, create a helper script:

```bash
#!/bin/bash
# switch-ai-project.sh

PROJECT_NAME=$1
AI_FOLDER_PATH="$HOME/projects/$PROJECT_NAME/.ai"

# Update Claude config
CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"

# Use jq to update the config
jq --arg path "$AI_FOLDER_PATH" \
  '.mcpServers["ai-tool-workflows"].env.AI_FOLDER_PATH = $path' \
  "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

echo "Switched to project: $PROJECT_NAME"
echo "AI Folder: $AI_FOLDER_PATH"
echo "Please restart Claude Code"
```

Usage:
```bash
./switch-ai-project.sh my-ecommerce-app
./switch-ai-project.sh my-blog-platform
```

### Project Selector (Advanced)

For Windows PowerShell:

```powershell
# Select-AIProject.ps1

function Select-AIProject {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ProjectName
    )

    $projectsBase = "$env:USERPROFILE\projects"
    $aiFolderPath = "$projectsBase\$ProjectName\.ai"
    $configPath = "$env:APPDATA\Claude\claude_desktop_config.json"

    if (Test-Path $aiFolderPath) {
        $config = Get-Content $configPath | ConvertFrom-Json
        $config.mcpServers.'ai-tool-workflows'.env.AI_FOLDER_PATH = $aiFolderPath
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath

        Write-Host "Switched to project: $ProjectName" -ForegroundColor Green
        Write-Host "AI Folder: $aiFolderPath"
        Write-Host "Please restart Claude Code" -ForegroundColor Yellow
    } else {
        Write-Host "Project not found: $aiFolderPath" -ForegroundColor Red
    }
}

# Usage:
# Select-AIProject "my-ecommerce-app"
```

## Best Practices

### 1. Version Control

**DO:**
- ✅ Commit the `mcp-server` folder to your project repo
- ✅ Include `.gitignore` to exclude `node_modules`
- ✅ Document the setup process in your project README

**DON'T:**
- ❌ Commit `node_modules`
- ❌ Commit sensitive environment variables
- ❌ Modify the core server logic per-project (use configuration instead)

### 2. Updates and Maintenance

When updating the template:

```bash
# 1. Update the central template
cd /path/to/ai-tool-template/mcp-server
git pull  # or however you update

# 2. For each project (if using per-project strategy)
cd /path/to/project/mcp-server
cp /path/to/ai-tool-template/mcp-server/index.js ./
npm install  # in case dependencies changed

# 3. Restart Claude Code
```

### 3. Configuration Management

Create a `.ai-mcp-config.json` in each project:

```json
{
  "projectName": "My E-commerce Platform",
  "aiFolderPath": "./ai",
  "customSettings": {
    "enableValidators": true,
    "defaultWorkflow": "software_development"
  }
}
```

### 4. Team Collaboration

For teams, include setup instructions in your project README:

```markdown
## AI Tool MCP Server Setup

This project uses the AI Tool MCP Server for AI-assisted development.

### Setup
1. Install dependencies: `cd mcp-server && npm install`
2. Run setup: `npm run setup`
3. Restart Claude Code

### Usage
See [mcp-server/USAGE_GUIDE.md](mcp-server/USAGE_GUIDE.md) for detailed usage instructions.
```

## Troubleshooting Multi-Project Setup

### Problem: Claude shows tools from wrong project

**Solution:** Verify `AI_FOLDER_PATH` in config
```bash
# Check current config
cat ~/.config/claude/claude_desktop_config.json | grep AI_FOLDER_PATH
```

### Problem: Multiple MCP servers conflict

**Solution:** Use unique names for each project
```json
{
  "mcpServers": {
    "project-a-ai": { ... },
    "project-b-ai": { ... }
  }
}
```

### Problem: Updates not reflecting

**Solution:** Clear node cache and reinstall
```bash
cd mcp-server
rm -rf node_modules package-lock.json
npm install
```

## Migration Guide

### From Single Project to Multiple Projects

1. **Backup current configuration**
2. **Choose strategy** (Global, Per-Project, or Hybrid)
3. **Deploy to first project** following steps above
4. **Test thoroughly** before deploying to other projects
5. **Deploy incrementally** to remaining projects
6. **Update documentation** for your team

## Summary

| Strategy | Best For | Complexity | Maintenance |
|----------|----------|------------|-------------|
| Global | Personal use, few projects | Low | Easy |
| Per-Project | Teams, many projects | Medium | Medium |
| Hybrid | Power users | High | Complex |

Choose the strategy that best fits your workflow and project structure.
