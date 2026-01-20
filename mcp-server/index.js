#!/usr/bin/env node

/**
 * AI Tool MCP Server
 * Local private MCP server for .ai workflows, skills, and agents
 * Designed to be used as a template across multiple projects
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get the .ai folder path from environment or use default relative to this server
const AI_FOLDER = process.env.AI_FOLDER_PATH || path.resolve(__dirname, "../.ai");

// Logging utility
function log(message, data = null) {
  const timestamp = new Date().toISOString();
  console.error(`[${timestamp}] ${message}`, data ? JSON.stringify(data, null, 2) : "");
}

/**
 * Load all workflows from .ai/workflows directory
 */
async function loadWorkflows() {
  try {
    const workflowsPath = path.join(AI_FOLDER, "workflows");
    const files = await fs.readdir(workflowsPath);

    const workflows = await Promise.all(
      files
        .filter(f => f.endsWith(".workflow.md"))
        .map(async (f) => {
          const content = await fs.readFile(path.join(workflowsPath, f), "utf-8");
          return {
            name: f.replace(".workflow.md", ""),
            filename: f,
            content
          };
        })
    );

    log(`Loaded ${workflows.length} workflows`);
    return workflows;
  } catch (error) {
    log(`Error loading workflows: ${error.message}`);
    return [];
  }
}

/**
 * Load all skills from .ai/skills directory (recursive)
 */
async function loadSkills() {
  try {
    const skillsPath = path.join(AI_FOLDER, "skills");
    const result = {};

    async function walkDir(dir, category = "") {
      const files = await fs.readdir(dir);

      for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = await fs.stat(fullPath);

        if (stat.isDirectory() && !file.startsWith("_")) {
          // Recursively walk subdirectories (category folders)
          await walkDir(fullPath, file);
        } else if (file.endsWith(".skill.md")) {
          const skillName = file.replace(".skill.md", "");
          const content = await fs.readFile(fullPath, "utf-8");

          if (!result[category]) {
            result[category] = {};
          }
          result[category][skillName] = {
            name: skillName,
            category,
            filename: file,
            content
          };
        }
      }
    }

    await walkDir(skillsPath);

    const totalSkills = Object.values(result).reduce(
      (sum, cat) => sum + Object.keys(cat).length,
      0
    );
    log(`Loaded ${totalSkills} skills across ${Object.keys(result).length} categories`);

    return result;
  } catch (error) {
    log(`Error loading skills: ${error.message}`);
    return {};
  }
}

/**
 * Load all agents from .ai/agents directory
 */
async function loadAgents() {
  try {
    const agentsPath = path.join(AI_FOLDER, "agents");
    const files = await fs.readdir(agentsPath);

    const agents = await Promise.all(
      files
        .filter(f => f.endsWith(".agent.md"))
        .map(async (f) => {
          const content = await fs.readFile(path.join(agentsPath, f), "utf-8");
          return {
            name: f.replace(".agent.md", ""),
            filename: f,
            content
          };
        })
    );

    log(`Loaded ${agents.length} agents`);
    return agents;
  } catch (error) {
    log(`Error loading agents: ${error.message}`);
    return [];
  }
}

/**
 * Load all validators from .ai/validators directory
 */
async function loadValidators() {
  try {
    const validatorsPath = path.join(AI_FOLDER, "validators");
    const files = await fs.readdir(validatorsPath);

    const validators = await Promise.all(
      files
        .filter(f => f.endsWith(".md") && !f.startsWith("_"))
        .map(async (f) => {
          const content = await fs.readFile(path.join(validatorsPath, f), "utf-8");
          return {
            name: f.replace(".md", ""),
            filename: f,
            content
          };
        })
    );

    log(`Loaded ${validators.length} validators`);
    return validators;
  } catch (error) {
    log(`Error loading validators: ${error.message}`);
    return [];
  }
}

/**
 * Load all templates from .ai/templates directory
 */
async function loadTemplates() {
  try {
    const templatesPath = path.join(AI_FOLDER, "templates");
    const files = await fs.readdir(templatesPath);

    const templates = await Promise.all(
      files
        .filter(f => f.endsWith(".md"))
        .map(async (f) => {
          const content = await fs.readFile(path.join(templatesPath, f), "utf-8");
          return {
            name: f.replace(".md", ""),
            filename: f,
            content
          };
        })
    );

    log(`Loaded ${templates.length} templates`);
    return templates;
  } catch (error) {
    log(`Error loading templates: ${error.message}`);
    return [];
  }
}

/**
 * Create and configure the MCP server
 */
async function createServer() {
  const server = new Server(
    {
      name: "ai-tool-workflows",
      version: "1.0.0"
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // Tool: list_available - List all available resources
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "list_available",
          description: "List all available workflows, skills, agents, validators, and templates from the .ai folder",
          inputSchema: {
            type: "object",
            properties: {
              type: {
                type: "string",
                enum: ["all", "workflows", "skills", "agents", "validators", "templates"],
                description: "What type of resources to list (default: all)"
              },
              category: {
                type: "string",
                description: "For skills: filter by category (e.g., 'developer', 'pm', 'finance', 'hr')"
              }
            }
          }
        },
        {
          name: "get_workflow",
          description: "Get the full content of a specific workflow",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Name of the workflow (e.g., 'software_development')"
              }
            },
            required: ["name"]
          }
        },
        {
          name: "get_skill",
          description: "Get the full content of a specific skill",
          inputSchema: {
            type: "object",
            properties: {
              category: {
                type: "string",
                description: "Skill category (e.g., 'developer', 'pm', 'finance', 'hr')"
              },
              name: {
                type: "string",
                description: "Name of the skill"
              }
            },
            required: ["category", "name"]
          }
        },
        {
          name: "get_agent",
          description: "Get the full content of a specific agent definition",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Name of the agent (e.g., 'developer', 'pm', 'finance')"
              }
            },
            required: ["name"]
          }
        },
        {
          name: "get_validator",
          description: "Get the full content of a specific validator",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Name of the validator"
              }
            },
            required: ["name"]
          }
        },
        {
          name: "get_template",
          description: "Get the full content of a specific template",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Name of the template (e.g., 'architecture_template', 'workflow_template')"
              }
            },
            required: ["name"]
          }
        },
        {
          name: "execute_workflow",
          description: "Execute a workflow by loading its content and related resources",
          inputSchema: {
            type: "object",
            properties: {
              name: {
                type: "string",
                description: "Name of the workflow to execute"
              },
              load_agents: {
                type: "boolean",
                description: "Whether to also load related agent definitions (default: true)"
              },
              load_templates: {
                type: "boolean",
                description: "Whether to also load related templates (default: true)"
              }
            },
            required: ["name"]
          }
        }
      ]
    };
  });

  // Tool execution handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case "list_available": {
          const type = args.type || "all";
          const category = args.category;

          let output = "# AI Tool Resources\n\n";

          if (type === "all" || type === "workflows") {
            const workflows = await loadWorkflows();
            output += "## Available Workflows\n";
            workflows.forEach(w => {
              output += `- **${w.name}** (${w.filename})\n`;
            });
            output += "\n";
          }

          if (type === "all" || type === "skills") {
            const skills = await loadSkills();
            output += "## Available Skills\n";

            const categories = category ? [category] : Object.keys(skills);

            for (const cat of categories) {
              if (skills[cat]) {
                output += `### ${cat}\n`;
                Object.keys(skills[cat]).forEach(s => {
                  output += `- **${s}** (${skills[cat][s].filename})\n`;
                });
                output += "\n";
              }
            }
          }

          if (type === "all" || type === "agents") {
            const agents = await loadAgents();
            output += "## Available Agents\n";
            agents.forEach(a => {
              output += `- **${a.name}** (${a.filename})\n`;
            });
            output += "\n";
          }

          if (type === "all" || type === "validators") {
            const validators = await loadValidators();
            output += "## Available Validators\n";
            validators.forEach(v => {
              output += `- **${v.name}** (${v.filename})\n`;
            });
            output += "\n";
          }

          if (type === "all" || type === "templates") {
            const templates = await loadTemplates();
            output += "## Available Templates\n";
            templates.forEach(t => {
              output += `- **${t.name}** (${t.filename})\n`;
            });
            output += "\n";
          }

          return {
            content: [{ type: "text", text: output }]
          };
        }

        case "get_workflow": {
          const workflows = await loadWorkflows();
          const workflow = workflows.find(w => w.name === args.name);

          if (!workflow) {
            return {
              content: [{
                type: "text",
                text: `Workflow not found: ${args.name}\n\nAvailable workflows:\n${workflows.map(w => `- ${w.name}`).join("\n")}`
              }],
              isError: true
            };
          }

          return {
            content: [{ type: "text", text: workflow.content }]
          };
        }

        case "get_skill": {
          const skills = await loadSkills();
          const skill = skills[args.category]?.[args.name];

          if (!skill) {
            const availableCategories = Object.keys(skills);
            return {
              content: [{
                type: "text",
                text: `Skill not found: ${args.category}/${args.name}\n\nAvailable categories: ${availableCategories.join(", ")}`
              }],
              isError: true
            };
          }

          return {
            content: [{ type: "text", text: skill.content }]
          };
        }

        case "get_agent": {
          const agents = await loadAgents();
          const agent = agents.find(a => a.name === args.name);

          if (!agent) {
            return {
              content: [{
                type: "text",
                text: `Agent not found: ${args.name}\n\nAvailable agents:\n${agents.map(a => `- ${a.name}`).join("\n")}`
              }],
              isError: true
            };
          }

          return {
            content: [{ type: "text", text: agent.content }]
          };
        }

        case "get_validator": {
          const validators = await loadValidators();
          const validator = validators.find(v => v.name === args.name);

          if (!validator) {
            return {
              content: [{
                type: "text",
                text: `Validator not found: ${args.name}\n\nAvailable validators:\n${validators.map(v => `- ${v.name}`).join("\n")}`
              }],
              isError: true
            };
          }

          return {
            content: [{ type: "text", text: validator.content }]
          };
        }

        case "get_template": {
          const templates = await loadTemplates();
          const template = templates.find(t => t.name === args.name);

          if (!template) {
            return {
              content: [{
                type: "text",
                text: `Template not found: ${args.name}\n\nAvailable templates:\n${templates.map(t => `- ${t.name}`).join("\n")}`
              }],
              isError: true
            };
          }

          return {
            content: [{ type: "text", text: template.content }]
          };
        }

        case "execute_workflow": {
          const loadAgentsFlag = args.load_agents !== false;
          const loadTemplatesFlag = args.load_templates !== false;

          const workflows = await loadWorkflows();
          const workflow = workflows.find(w => w.name === args.name);

          if (!workflow) {
            return {
              content: [{
                type: "text",
                text: `Workflow not found: ${args.name}`
              }],
              isError: true
            };
          }

          let output = `# Executing Workflow: ${workflow.name}\n\n`;
          output += "## Workflow Definition\n\n";
          output += workflow.content;
          output += "\n\n---\n\n";

          if (loadAgentsFlag) {
            const agents = await loadAgents();
            output += "## Related Agents\n\n";
            for (const agent of agents) {
              output += `### ${agent.name}\n\n`;
              output += agent.content;
              output += "\n\n---\n\n";
            }
          }

          if (loadTemplatesFlag) {
            const templates = await loadTemplates();
            output += "## Available Templates\n\n";
            templates.forEach(t => {
              output += `- **${t.name}**: Use \`get_template\` to load this template\n`;
            });
            output += "\n";
          }

          return {
            content: [{ type: "text", text: output }]
          };
        }

        default:
          return {
            content: [{ type: "text", text: `Unknown tool: ${name}` }],
            isError: true
          };
      }
    } catch (error) {
      log(`Error executing tool ${name}:`, error);
      return {
        content: [{
          type: "text",
          text: `Error executing ${name}: ${error.message}`
        }],
        isError: true
      };
    }
  });

  return server;
}

/**
 * Main entry point
 */
async function main() {
  log("Starting AI Tool MCP Server");
  log(`AI Folder Path: ${AI_FOLDER}`);

  // Verify .ai folder exists
  try {
    await fs.access(AI_FOLDER);
    log(".ai folder found");
  } catch (error) {
    log("ERROR: .ai folder not found at " + AI_FOLDER);
    process.exit(1);
  }

  const server = await createServer();
  const transport = new StdioServerTransport();

  await server.connect(transport);
  log("MCP Server connected and ready");
}

main().catch((error) => {
  log("Fatal error:", error);
  process.exit(1);
});
