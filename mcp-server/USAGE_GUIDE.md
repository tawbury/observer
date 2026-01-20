# AI Tool MCP Server - Usage Guide

Complete guide for using the AI Tool MCP Server with Claude Code.

## Quick Start

### Installation (One-Time Setup)

```bash
# Navigate to the mcp-server directory
cd mcp-server

# Install dependencies
npm install

# Run automated setup
npm run setup

# Restart Claude Code
```

That's it! The MCP server is now available in Claude Code.

## How to Use in Claude Code

Once installed, you can interact with the `.ai` folder resources directly through natural language in Claude Code.

### Example Conversations

#### 1. Exploring Available Resources

```
You: "What workflows are available?"

Claude: [Uses list_available tool]
"Here are the available workflows:
- software_development
- contents_creation
- financial_management
- project_management
- hr_evaluation
- integrated_development
..."
```

#### 2. Starting a Software Development Project

```
You: "I want to start a new software project. Execute the software development workflow."

Claude: [Uses execute_workflow]
"I've loaded the software development workflow along with the related agents (PM, Developer, Finance).

The workflow has 8 stages:
1. Anchor Document Creation
2. Requirements Analysis
3. Architecture Design
...

Let's begin with stage 1: Anchor Document Creation. This involves the PM and Developer agents working together to establish the strategic foundation..."
```

#### 3. Using Specific Skills

```
You: "I need help designing a REST API. Load the API design skill."

Claude: [Uses get_skill with category="developer", name="dev_api_design"]
"I've loaded the API Design skill. This skill covers:
- RESTful principles
- Resource modeling
- Endpoint design patterns
- Authentication strategies
...

What kind of API are you building?"
```

#### 4. Checking Agent Capabilities

```
You: "What can the developer agent do?"

Claude: [Uses get_agent with name="developer"]
"The Developer Agent has the following capabilities:
- System architecture design
- Technical implementation
- Code review and quality assurance
- Deployment and operations
...

The agent can work at both L1 (junior) and L2 (senior) levels."
```

#### 5. Getting a Template

```
You: "I need to create an architecture document. Get me the architecture template."

Claude: [Uses get_template with name="architecture_template"]
"Here's the architecture template structure:

# Meta
- Document Name:
- File Name:
- Status:
...

You can now fill this in with your project details."
```

#### 6. Working with Multiple Skills

```
You: "Show me all developer skills related to backend development."

Claude: [Uses list_available with type="skills", category="developer"]
"Here are the developer skills available:
- dev_backend
- dev_api_design
- dev_database_design
- dev_microservices
- dev_security
...

Which one would you like to explore?"
```

## Advanced Usage Patterns

### Pattern 1: End-to-End Project Setup

```
You: "I'm starting a new e-commerce platform. Help me set it up using the proper workflow."

Claude:
1. [execute_workflow: software_development]
2. [get_template: anchor_template]
3. [get_agent: developer]
4. [get_agent: pm]

"Let's set up your e-commerce platform systematically:

STEP 1: Anchor Document Creation
I'll use the anchor template to help you define:
- Project vision and objectives
- Technical constraints
- Success metrics
...

STEP 2: Requirements Analysis
The PM agent will help identify:
- User stories
- Functional requirements
- Non-functional requirements
..."
```

### Pattern 2: Skill Combination for Complex Tasks

```
You: "I need to optimize our application's performance."

Claude:
1. [get_skill: developer/dev_performance_optimization]
2. [get_skill: developer/dev_monitoring]
3. [get_validator: architecture_validator]

"For performance optimization, I'll combine multiple skills:

1. Performance Optimization Skill:
   - Profiling and benchmarking
   - Code optimization techniques
   - Database query optimization

2. Monitoring Skill:
   - Metrics collection
   - Performance tracking
   - Alert configuration

Let's start by profiling your application..."
```

### Pattern 3: Quality Assurance with Validators

```
You: "Review this architecture document for completeness."

Claude:
1. [get_validator: architecture_validator]
2. [get_template: architecture_template]

"I'll validate your architecture document against the standard template and validation rules:

Checking:
✓ Meta information completeness
✓ System architecture section
✓ Technology stack documentation
✓ Scalability considerations
..."
```

## Tool Reference

### list_available

**Purpose:** Discover what resources are available

**Usage:**
```
"List all workflows"
"Show me all developer skills"
"What agents are available?"
"List everything in the AI system"
```

**Parameters:**
- `type`: "all" | "workflows" | "skills" | "agents" | "validators" | "templates"
- `category` (for skills): "developer" | "pm" | "finance" | "hr" | "contents-creator"

### get_workflow

**Purpose:** Load a complete workflow definition

**Usage:**
```
"Load the software development workflow"
"Get the contents creation workflow"
"Show me the HR evaluation workflow"
```

**Parameters:**
- `name`: workflow name (without .workflow.md extension)

### get_skill

**Purpose:** Load a specific skill for detailed guidance

**Usage:**
```
"Get the backend development skill"
"Load the API design skill from developer category"
"Show me the budget management skill"
```

**Parameters:**
- `category`: skill category folder name
- `name`: skill name (without .skill.md extension)

### get_agent

**Purpose:** Load an agent definition to understand its capabilities

**Usage:**
```
"Load the developer agent"
"What can the PM agent do?"
"Show me the finance agent definition"
```

**Parameters:**
- `name`: agent name (without .agent.md extension)

### get_validator

**Purpose:** Load validation rules for quality assurance

**Usage:**
```
"Get the architecture validator"
"Load the L2 review validator"
"Show me validation rules for specifications"
```

**Parameters:**
- `name`: validator name (without .md extension)

### get_template

**Purpose:** Load a document template

**Usage:**
```
"Get the architecture template"
"Load the PRD template"
"Show me the decision template"
```

**Parameters:**
- `name`: template name (without .md extension)

### execute_workflow

**Purpose:** Start a complete workflow with all related resources

**Usage:**
```
"Execute the software development workflow"
"Start the financial management workflow"
"Run the integrated development workflow"
```

**Parameters:**
- `name`: workflow name
- `load_agents`: true/false (default: true)
- `load_templates`: true/false (default: true)

## Tips for Effective Use

### 1. Start with Workflows
For structured processes, always start by executing the relevant workflow. This ensures you follow best practices.

```
✅ "Execute the software development workflow"
❌ "Help me build software" (too vague)
```

### 2. Be Specific with Skills
When you need focused expertise, request specific skills.

```
✅ "Get the dev_api_design skill"
❌ "Help me with APIs" (Claude might not use the skill)
```

### 3. Combine Resources
Don't hesitate to ask for multiple resources in one request.

```
✅ "Load the software development workflow and the developer agent"
✅ "Get the backend skill and the architecture template"
```

### 4. Use Validators for Quality
Always use validators when reviewing or creating documents.

```
✅ "Validate this architecture using the architecture validator"
✅ "Check my PRD against the validator"
```

### 5. Explore First
If unsure what's available, start with list_available.

```
✅ "List all available workflows"
✅ "Show me all finance skills"
```

## Common Workflows

### New Software Project
```
1. "Execute the software development workflow"
2. "Get the anchor template"
3. Create anchor document
4. "Get the architecture template"
5. Design architecture
6. "Get relevant developer skills" (backend, api_design, etc.)
7. Implement
```

### Code Review
```
1. "Load the dev_code_review skill"
2. "Get the L2 review validator"
3. Perform review using the skill guidelines
4. Validate using the validator
```

### Performance Optimization
```
1. "Get the dev_performance_optimization skill"
2. "Load the dev_monitoring skill"
3. Profile and optimize
4. Set up monitoring
```

### Document Creation
```
1. "Get the [type]_template"
2. Create document following template
3. "Get the [type]_validator"
4. Validate document
```

## Troubleshooting

### "Tool not found" or "Resource not available"

**Solution:** List available resources first
```
"List all available [workflows/skills/agents/etc]"
```

### Not sure which skill to use

**Solution:** List skills by category
```
"List all developer skills"
"Show me finance skills"
```

### Workflow not executing properly

**Solution:** Load it explicitly
```
"Execute the [workflow_name] workflow with all agents and templates"
```

### Template not formatting correctly

**Solution:** Request the raw template
```
"Get the [template_name] template in full"
```

## Best Practices

1. **Always start structured tasks with a workflow**
2. **Use validators to ensure quality**
3. **Combine skills for complex tasks**
4. **Request templates before creating documents**
5. **Load agent definitions to understand capabilities**
6. **Be explicit about what you need**

## Next Steps

- Explore all available workflows: `"List all workflows"`
- Understand agent capabilities: `"Show me all agents"`
- Browse skill library: `"List all skills by category"`
- Review templates: `"List all templates"`

## Support

If you encounter issues:
1. Check [README.md](README.md) for installation and configuration
2. Verify `.ai` folder structure is intact
3. Ensure Claude Code was restarted after setup
4. Check the MCP server logs for errors
