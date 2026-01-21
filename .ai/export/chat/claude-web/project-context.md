# Claude Web Project Context

**Paste this into Claude Web to establish project context.**

---

## Project: AI Tool System (mcp OS v0.1)

### System Overview

I'm working with **mcp OS** - a comprehensive multi-agent AI operating system for project management across:
- Software Development
- Contents Creation (visual, text, video, interactive)
- Financial Analysis
- HR Evaluation
- Product Management

### Architecture

**5 Specialized Agents**
1. Developer Agent - Code, architecture, testing, deployment
2. HR Agent - Role assessment, evaluation
3. PM Agent - Strategy, roadmaps
4. Finance Agent - Budgets, forecasting
5. Contents-Creator Agent - Multi-media content

**90+ Skills** (L1 Junior, L2 Senior)
**24+ Validators** (quality assurance)
**8 Workflows** (execution patterns)
**15 Templates** (document standards)

### Single Source of Truth

All system definitions are in the `.ai/` directory:

```
.ai/
├── agents/              # Agent specifications
├── skills/              # Skill implementations
├── validators/          # Validation rules
├── workflows/           # Workflow patterns
├── templates/           # Document templates
├── spec/                # Operational specifications
├── install/             # Tool integration config
└── export/              # External tool configs
```

This directory is the authoritative source. Generated files in the project root are auto-created from these sources.

### Directory Structure

| Directory | Purpose | AI Access |
|-----------|---------|-----------|
| `.ai/` | System definitions (SSoT) | Yes |
| `docs/` | Official project documents | Yes |
| `vault/` | AI drafts and experiments | Yes |
| `ops/` | Operations logs | No (by default) |
| `backup/` | Disaster recovery | No |

### Document Types

**Standards**:
- **Decisions** → `docs/decisions/decision_{project}_{YYYYMMDD}.md`
- **Tasks** → `docs/tasks/task_{role}_{dept}.md`
- **Reports** → `docs/reports/report_{role}_{dept}_{YYYYMMDD}.md`
- **Architecture** → `docs/dev/archi/architecture_{project}.md`
- **Specifications** → `docs/dev/spec/spec_{module}.md`
- **PRDs** → `docs/dev/PRD/prd_{project}.md`

All use templates from `.ai/templates/`

### Session Resilience

**Important**: Conversation context is ephemeral. Real state lives in files:

1. **Roadmaps** - Phase/session structure
2. **Tasks** - Executable units
3. **Run Records** - Execution evidence in `ops/run_records/`
4. **Approval Packets** - Decision checkpoints in `ops/approvals/`

When resuming: Read ops/run_records/, check Roadmap, continue from checkpoint.

### Workflows

**4-Stage Standard Pattern**
1. Planning (PRD)
2. Design (Architecture)
3. Specification (Technical Spec)
4. Decision (Decision Record)

**Operational Loop**
1. Roadmap (structure)
2. Task (executable unit)
3. Skill Execution (agent work)
4. Run Record (evidence)
5. Roadmap Update (next phase)

### Quality Assurance

**Validators Available**
- Document validators (task, report, decision, spec, prd, architecture)
- Skill validators (execution quality)
- L2 validators (senior review)
- Cross-agent validators (integration)

Always validate before finalizing deliverables.

### Working Practices

### Do's ✓
- Edit files in `.ai/` to change system behavior
- Create documents using `.ai/templates/`
- Run `mcp sync` after structural changes
- Use `[[Obsidian links]]` for document references
- Apply validators before finalizing
- Record execution in ops/run_records/

### Don'ts ✗
- Manually edit Generated files (.cursorrules, .claude/project.md, etc.)
- Bypass the SSoT principle
- Delete or modify ops/ entries
- Create documents without templates
- Skip validation steps

### Helpful Files

- **System Overview**: `.ai/README.md`
- **Full Spec**: `.ai/spec/MCP_OS_Operational_Spec_v0_1.md`
- **Agent Definitions**: `.ai/agents/` (5 files)
- **Skill Index**: `.ai/skills/skill_index.md`
- **Workflow Guide**: `.ai/workflows/workflow_index.md`
- **Validator Guide**: `.ai/validators/validator_index.md`

### Project State

**Current Workflow**: [Workflow name]
**Current Stage**: [Stage description]
**Last Run Record**: [File path if known]
**Recent Artifacts**:
- [List docs/decisions files]
- [List docs/tasks files]
- [List docs/reports files]

### What I Need Help With

[Your specific request]

---

## Context for AI

Please help me work within the mcp OS framework by:
1. Understanding the system architecture
2. Recommending appropriate agents and workflows
3. Suggesting relevant skills and validators
4. Guiding through execution steps
5. Ensuring compliance with SSoT principles
6. Supporting session continuity

Remember: The `.ai/` directory is authoritative. When unsure, reference files there.
