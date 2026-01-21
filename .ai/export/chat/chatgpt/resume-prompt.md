# ChatGPT Session Resume Prompt

**Copy this entire section and paste into ChatGPT when resuming work after a session interruption.**

---

## Session Context Recovery

I am working on the **AI Tool System** (mcp OS) - a multi-agent AI operating system for complex project management.

### System Overview

The system consists of:
- **5 Specialized Agents**: Developer, HR, PM, Finance, Contents-Creator
- **90+ Skills**: Organized by agent and proficiency level (L1 Junior, L2 Senior)
- **24+ Validators**: Quality assurance framework
- **8 Workflows**: Different execution patterns
- **15 Document Templates**: Standardized document formats

### Single Source of Truth (SSoT)

The `.ai/` directory is the authoritative source for all system definitions:
- `.ai/agents/` - Agent definitions
- `.ai/skills/` - Skill implementations
- `.ai/validators/` - Validation rules
- `.ai/workflows/` - Workflow definitions
- `.ai/templates/` - Document templates
- `.ai/spec/MCP_OS_Operational_Spec_v0_1.md` - Operational specification

### Directory Structure

```
.ai/          - System definitions (SSoT)
docs/         - Official project documents (AI visible)
vault/        - AI drafts and experiments (AI visible)
ops/          - Operations logs (AI not visible)
backup/       - Disaster recovery (AI not visible)
```

### Key Principle: Session Resilience

**Critical**: All state is stored in the file system, NOT in conversation context.

When resuming:
1. Check `ops/run_records/` for last execution state
2. Review the current Roadmap for task sequencing
3. Read relevant Task definitions
4. Continue from the last completion point

### Current Workflow State

**Workflow ID**: [Paste workflow ID, e.g., WF-INTEGRATED-001]

**Current Stage**: [Paste current stage, e.g., Stage 5 - Feature Specification]

**Last Run Record**: [Paste file path, e.g., ops/run_records/run_WF-INTEGRATED-001_RUN-20260121-143000.json]

**Completion Status**:
- [ ] Stage 1 - Complete
- [ ] Stage 2 - Complete
- [ ] Stage 3 - Complete
- [ ] Stage 4 - Complete
- [ ] Current Stage - In Progress

### Recent Artifacts Generated

- **Decisions**: [List docs/decisions/ files]
- **Tasks**: [List docs/tasks/ files]
- **Reports**: [List docs/reports/ files]
- **Architecture**: [List docs/dev/archi/ files]
- **Specifications**: [List docs/dev/spec/ files]
- **PRDs**: [List docs/dev/PRD/ files]

### Pending Approvals

- [List any items awaiting approval from ops/approvals/]

### Next Actions

1. [Describe the next step to complete]
2. [List any blockers or decisions needed]
3. [Identify any missing information]

### Questions for AI

1. What is the current state of the [Workflow Name]?
2. What artifacts have been generated so far?
3. What is the next step in the workflow?
4. Are there any pending approvals or validations needed?
5. What validators should be applied to the next stage?

---

## Instructions for AI Assistant

Please:
1. Acknowledge the session context above
2. Confirm understanding of the current state
3. Identify any gaps or issues in the current state
4. Recommend next steps
5. Validate against .ai/ definitions if needed

You are working within the mcp OS framework. Always:
- Reference `.ai/` files for authoritative definitions
- Check validator requirements before finalizing deliverables
- Record execution evidence in appropriate files
- Maintain the SSoT principle
- Consider session continuity for future resumption

---

**Last Updated**: [Paste date when session was interrupted]
**Session Duration**: [Note any relevant timing information]
**Key Decisions Made**: [Summarize important decisions]
**Outstanding Issues**: [List any blockers or questions]
