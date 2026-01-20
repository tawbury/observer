# AI Tool MCP Server

Local private MCP (Model Context Protocol) server for integrating `.ai` folder workflows, skills, agents, validators, and templates with Claude Code.

## Features

- 🔒 **100% Local & Private** - No external network calls, runs entirely on your machine
- 🎯 **Template-Based** - Designed to be copied to any project that uses the `.ai` folder structure
- 🚀 **Easy Setup** - Automated configuration script for Claude Code
- 📦 **Comprehensive** - Access workflows, skills, agents, validators, and templates
- 🔄 **Reusable** - Use across all your projects with the same `.ai` structure

## Project Structure

```
aI_tool/
├── .ai/                          # AI system resources
│   ├── agents/                   # Agent definitions
│   ├── skills/                   # Skill libraries
│   │   ├── developer/
│   │   ├── pm/
│   │   ├── finance/
│   │   ├── hr/
│   │   └── contents-creator/
│   ├── workflows/                # Workflow definitions
│   ├── validators/               # Validation rules
│   └── templates/                # Document templates
└── mcp-server/                   # This MCP server
    ├── index.js                  # Main server implementation
    ├── setup.js                  # Automated setup script
    ├── package.json
    └── README.md
```

## Installation

### 1. Install Dependencies

```bash
cd mcp-server
npm install
```

### 2. Run Setup Script

This will automatically configure Claude Code to use this MCP server:

```bash
npm run setup
```

The setup script will:
- Detect your operating system
- Locate your Claude Code configuration file
- Add this MCP server to the configuration
- Set the correct paths automatically

### 3. Restart Claude Code

After setup, restart Claude Code for the changes to take effect.

## Manual Configuration

If the automated setup doesn't work, you can manually add this configuration to your Claude Code config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ai-tool-workflows": {
      "command": "node",
      "args": ["D:\\development\\_templates\\aI_tool\\mcp-server\\index.js"],
      "env": {
        "AI_FOLDER_PATH": "D:\\development\\_templates\\aI_tool\\.ai"
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

**Note:** Replace the paths with your actual absolute paths.

## Available Tools

Once configured, you can use these tools in Claude Code:

### 1. `list_available`
List all available resources from the `.ai` folder.

**Parameters:**
- `type` (optional): "all", "workflows", "skills", "agents", "validators", or "templates"
- `category` (optional): For skills, filter by category (e.g., "developer", "pm")

**Example:**
```
"List all available workflows and skills"
```

### 2. `get_workflow`
Get the full content of a specific workflow.

**Parameters:**
- `name` (required): Workflow name (e.g., "software_development")

**Example:**
```
"Load the software development workflow"
```

### 3. `get_skill`
Get the full content of a specific skill.

**Parameters:**
- `category` (required): Skill category (e.g., "developer", "pm", "finance")
- `name` (required): Skill name (e.g., "dev_backend", "api_design")

**Example:**
```
"Get the backend development skill"
```

### 4. `get_agent`
Get the full content of a specific agent definition.

**Parameters:**
- `name` (required): Agent name (e.g., "developer", "pm", "finance")

**Example:**
```
"Load the developer agent definition"
```

### 5. `get_validator`
Get the full content of a specific validator.

**Parameters:**
- `name` (required): Validator name

**Example:**
```
"Get the architecture validator"
```

### 6. `get_template`
Get the full content of a specific template.

**Parameters:**
- `name` (required): Template name (e.g., "architecture_template")

**Example:**
```
"Load the architecture template"
```

### 7. `execute_workflow`
Execute a workflow by loading its content and related resources.

**Parameters:**
- `name` (required): Workflow name
- `load_agents` (optional, default: true): Load related agent definitions
- `load_templates` (optional, default: true): Load related templates

**Example:**
```
"Execute the software development workflow"
```

## Usage Examples

### Example 1: Starting a New Software Project

```
User: "Execute the software development workflow"
Claude: [Loads workflow, agents, and templates]
        "I've loaded the software development workflow. Let's start with
        the Anchor Document Creation stage. I'll use the PM and Developer
        agents to help create the project foundation..."
```

### Example 2: Getting Specific Skills

```
User: "Show me all developer skills"
Claude: [Uses list_available with type="skills" and category="developer"]
        "Here are all available developer skills:
        - dev_backend
        - dev_frontend
        - dev_api_design
        - dev_database_design
        ..."
```

### Example 3: Using a Specific Skill

```
User: "I need to design an API. Load the API design skill"
Claude: [Uses get_skill with category="developer" and name="dev_api_design"]
        "I've loaded the API design skill. This skill covers:
        - RESTful API design principles
        - API versioning strategies
        - Authentication/Authorization patterns
        ..."
```

## Using as a Template

To use this in another project:

1. **Copy the entire `mcp-server` folder** to your new project
2. **Ensure your project has a `.ai` folder** with the same structure
3. **Run the setup** again in the new location:
   ```bash
   cd your-project/mcp-server
   npm install
   npm run setup
   ```
4. **Update the server name** (optional) in `index.js` and `setup.js` if you want multiple projects to have separate MCP servers

## Security & Privacy

- ✅ **100% Local** - All data stays on your machine
- ✅ **No Network Calls** - The server only reads local files
- ✅ **Private** - Your workflows and skills are never sent to external servers
- ✅ **Version Control Safe** - Can be committed to private Git repositories
- ✅ **Sandboxed** - Only accesses files within the `.ai` folder

## Troubleshooting

### Server Not Showing Up in Claude Code

1. Check that Claude Code is completely restarted
2. Verify the configuration file has the correct paths
3. Check the MCP server logs (stderr output)

### "AI folder not found" Error

- Verify the `AI_FOLDER_PATH` in the configuration points to the correct location
- Ensure the `.ai` folder exists and has the required subdirectories

### Changes Not Reflecting

- The MCP server caches are cleared on each tool call
- If you modify `.ai` files, they'll be loaded fresh on the next tool call
- No need to restart the server for content changes

### Running the Server Manually for Testing

```bash
node index.js
```

This will start the server in stdio mode. You can check the logs in stderr.

## Development

### Running in Development Mode

```bash
npm run dev
```

This uses Node's `--watch` flag to automatically restart on file changes.

### Logging

The server logs to stderr. All logs include timestamps and are prefixed with `[timestamp]`.

## License

MIT

## Support

For issues related to:
- **MCP Server**: Check the server logs and configuration
- **Claude Code**: Visit the Claude Code documentation
- **.ai Folder Structure**: Refer to `.ai/README.md`
