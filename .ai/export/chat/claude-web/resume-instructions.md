# Claude Web Resume Instructions

**Use this to resume work in Claude Web after session interruption.**

---

## Session Context Restoration

### System Context

Working with **mcp OS v0.1** - Multi-agent AI operating system.

**Quick Facts**:
- 5 Agents (Developer, HR, PM, Finance, Contents-Creator)
- 90+ Skills (L1/L2)
- 24+ Validators
- 8 Workflows
- 15 Templates
- SSoT in `.ai/` directory

### File System is the Source of Truth

**Permanent state** is stored in:
- `.ai/` - System definitions (authoritative)
- `docs/` - Project documents
- `vault/` - AI drafts
- `ops/` - Execution logs
- `backup/` - Backups

**This conversation** - temporary, not persistent.

### Resuming Work

When resuming, do this first:

1. **Check Last Execution**
   ```
   Read: ops/run_records/
   Look for: Most recent JSON file
   Extract: Last stage completed, status, timestamp
   ```

2. **Review Roadmap**
   - Find current Roadmap file
   - Check current phase/session
   - Identify next task

3. **Read Task Definition**
   - Find docs/tasks/ file
   - Understand what needs to be done
   - Identify applicable skills

4. **Continue from Checkpoint**
   - Resume at point of interruption
   - Use previous outputs as inputs
   - Record new execution evidence

### Current Project State

**Workflow**: [Name]
**Last Stage Completed**: [Stage]
**Last Run Record**: [File path, e.g., ops/run_records/run_WF-002_RUN-20260121-140000.json]
**Status**: [In Progress / Awaiting Review / etc.]

**Recent Documents**:
- Decision: [File path]
- Task: [File path]
- Report: [File path]
- Architecture: [File path]
- Specification: [File path]

**Pending Approvals**:
- [List any items awaiting approval]

**Next Milestone**:
1. [Immediate next task]
2. [Subsequent tasks]

### Helpful Quick Reference

**Document Location Mapping**:
- Decisions → `docs/decisions/`
- Tasks → `docs/tasks/`
- Reports → `docs/reports/`
- Architecture → `docs/dev/archi/`
- Specs → `docs/dev/spec/`
- PRDs → `docs/dev/PRD/`

**Key Files to Consult**:
- `.ai/spec/MCP_OS_Operational_Spec_v0_1.md` - Full specification
- `.ai/README.md` - System overview
- `.ai/workflows/workflow_index.md` - All workflows
- `.ai/agents/` - Agent definitions

### When You're Unsure

1. Check `.ai/` for authoritative definitions
2. Review relevant workflow definition
3. Consult appropriate agent definition
4. Look at similar completed documents
5. Apply relevant validators

### Important Reminders

✓ Always check `.ai/` for system definitions
✓ Use templates for creating documents
✓ Apply validators before finalizing
✓ Record execution in ops/run_records/
✓ Update roadmaps before session ends

✗ Don't manually edit Generated files
✗ Don't bypass the SSoT principle
✗ Don't delete ops/ entries
✗ Don't skip validation

---

## Instructions for Claude Web

Please:

1. **Acknowledge** you understand the mcp OS system and this project's context
2. **Confirm** the current project state listed above
3. **Identify** the next immediate action to take
4. **Check** if any validators are needed before proceeding
5. **Help me** complete the next step in the workflow

---

**Session Started**: [Current timestamp]
**Previous Session Ended**: [Date/time of last session]
**Work Duration Since Last Session**: [How long ago]
