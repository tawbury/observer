# Gemini Session Resume Prompt

**Use this when resuming work on the AI Tool System after your Gemini conversation ends.**

---

## Context Recovery

I am working within the **mcp OS** - a multi-agent AI operating system for complex projects.

### Quick System Summary

| Component | Count | Purpose |
|-----------|-------|---------|
| Agents | 5 | Developer, HR, PM, Finance, Contents-Creator |
| Skills | 90+ | Domain-specific capabilities by agent |
| Validators | 24+ | Quality assurance |
| Workflows | 8 | Execution patterns |
| Templates | 15 | Standardized documents |

### Key Architecture

**SSoT Principle**: `.ai/` directory contains all authoritative definitions
- Agents, skills, validators, workflows, templates all defined there
- Generated files (`.cursorrules`, `.claude/project.md`) are auto-created
- Manual edits to `.ai/` propagate to all tools

**Directory Roles**:
- `.ai/` → System definitions (read-only without proper process)
- `docs/` → Official project documents
- `vault/` → AI drafts and experiments
- `ops/` → Execution logs (AI not visible)
- `backup/` → Recovery (AI not visible)

### Session Continuity

**Critical**: This conversation will end. All permanent state goes in the filesystem:
- Tasks → `docs/tasks/`
- Decisions → `docs/decisions/`
- Reports → `docs/reports/`
- Execution → `ops/run_records/`

To resume next time:
1. Check `ops/run_records/` for last execution
2. Read current Roadmap
3. Review Task definitions
4. Continue from checkpoint

### Current Project State

**Workflow**: [Workflow name and ID]
**Current Stage**: [Stage number and name]
**Completion**: [% complete]

**Last Execution**:
- Timestamp: [Date/time]
- Run Record: [File path]
- Status: [Last known status]

**Artifacts Generated**:
- Decisions: [List files]
- Tasks: [List files]
- Reports: [List files]
- Other: [List files]

**Pending Items**:
- [Approvals waiting]
- [Validations pending]
- [Decisions needed]

### Next Steps

1. [Immediate next action]
2. [Following action]
3. [Final milestone]

### My Question

[What you need help with]

---

## Instructions

Please:
1. Confirm you understand the mcp OS system
2. Acknowledge the current project state
3. Validate against `.ai/` definitions
4. Recommend next steps
5. Identify any issues or gaps

---

Remember: The file system is authoritative, not this conversation.
