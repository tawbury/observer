# Operational Run Record Creation

**Skill Name**: Operational Run Record Creation  
**Skill ID**: SKILL-OPS-RUNRECORD-v1

---

## Purpose

This skill enables operators and agents to create Run Record instances that capture execution evidence, close the operational loop, and enable session-resilient work continuity. Run Records document what happened, what changed, and what comes next, while proposing (not commanding) Roadmap updates. They serve as evidence artifacts that any IDE-based AI or operator can read to understand work history and resume from the last recorded state.

---

## When to Use / When NOT to Use

**When to Use:**
- After completing one or more Tasks
- After making progress on a Task (partial work)
- After discovering blockers or changing direction
- After any meaningful work that moves the project forward
- When execution evidence is needed for Roadmap update proposals

**When NOT to Use:**
- For strategic planning (use Anchor or Decision documents)
- For defining work structure (use Roadmap)
- For creating new Tasks (use task creation workflows)
- For chat session declarations without actual work performed

---

## Inputs (Contract)

### Required Inputs
- **Run Record Template**: Reference to [[run_record_template.md]] or equivalent
- **Parent Document**: Task that was executed (preferred) OR Roadmap if no specific Task
- **Work Summary**: What happened during this execution session
- **Changed Artifacts**: List of files/documents created or modified

### Optional Inputs
- **Related Reference Links**: Roadmap, Decisions, or other artifacts relevant to this work
- **Blocker Information**: If work was blocked or direction changed
- **Next Action Proposals**: Suggested updates for Roadmap or next Task priorities

### Input Format
```
Parent Document: [[task_001.md]] (or [[roadmap.md]] if no task)
Work Summary: Completed system architecture design
Changed Artifacts: docs/dev/archi/system_architecture.md (created)
Related Reference: [[roadmap.md]], [[decision_tech_stack.md]]
Next Actions: Propose marking Task 001 as Done, start Task 002
```

### Preconditions
- Work has actually been performed (Run Records are evidence, not plans)
- Parent Document (Task or Roadmap) exists and is accessible
- Changed artifact files exist and can be verified
- No wildcard link patterns are used

---

## Process (Step-by-step)

### Core Process

1. **Confirm Work Evidence** - Verify that actual work was performed (files changed, deliverables created, progress made)

2. **Select Parent Document** - Determine if this Run Record closes a specific Task or relates to general Roadmap work:
   - If Task exists: Use `[[task_xxx.md]]` as Parent Document
   - If no specific Task: Use `[[roadmap.md]]` as Parent Document

3. **Create Run Record File** - Use [[run_record_template.md]] as base, name with date/descriptor: `run_record_YYYYMMDD_<short_slug>.md`

4. **Write Metadata Section** - Fill metadata fields:
   - Parent Document: `[[task_xxx.md]]` or `[[roadmap.md]]`
   - Related Reference: Include Roadmap link + all key artifacts modified/created

5. **Document What Happened** - Write concise summary of work performed (2-6 lines, factual, no interpretation)

6. **List What Changed** - Enumerate files/artifacts created or modified with paths or links

7. **Record Evidence First** - Prioritize factual evidence over narrative (see Evidence First subsection)

8. **Propose Next Actions (다음 액션)** - Suggest Roadmap updates, Task status changes, or next priorities (proposals only, not commands)

9. **Apply Metadata Linking Rule** - Ensure all relationships declared in metadata before body mentions (see subsection below)

10. **Validate Link Hygiene** - Confirm no wildcard patterns (`*`) exist in any Obsidian links

11. **Check IDE Paste Safety** - Ensure formatting works in both Obsidian and IDE contexts (see subsection below)

12. **Save Run Record** - Write file to `ops/run_records/` or equivalent location

### Evidence First

Run Records prioritize evidence over narrative:

- **What Changed (Files)**: List specific files created, modified, or deleted with paths
- **What Happened (Steps)**: Concise factual summary of actions taken
- **What Comes Next (Proposals)**: Suggested Roadmap/Task updates based on this evidence

**Key Principle**: Run Records are evidence artifacts, not execution commands. The operator or next session decides whether to accept proposed updates.

### Metadata Linking Rule

**Parent Document Selection:**
- **Preferred**: `[[task_xxx.md]]` if Run Record closes or advances a specific Task
- **Fallback**: `[[roadmap.md]]` if work is general or spans multiple Tasks

**Related Reference Requirements:**
- **Must include**: Roadmap link (for loop continuity)
- **Should include**: Any artifacts created/modified (architecture docs, specs, code files)
- **May include**: Decision documents, other Run Records, Dependencies

**No Wildcards**: Use real filenames only (`[[task_001.md]]`), never patterns (`[[task_*.md]]`)

### IDE Paste Safety

Run Records may be read/written in VS Code, Cursor, or other IDEs without Obsidian rendering:

- **Minimize Complex Formatting**: Avoid nested code blocks or heavy markdown that breaks in plain text
- **Use Simple Tables**: Prefer bullet lists over complex tables when possible
- **Test Readability**: Ensure Run Record is readable in both Obsidian preview and IDE plain text view
- **Provide Alternatives**: If using code blocks for file contents, also provide plain text summary

---

## Outputs (Contract)

### Primary Outputs
- **Run Record File**: `run_record_YYYYMMDD_<short_slug>.md` in `ops/run_records/` (default)
- **Alternative** (if project policy requires): docs/run_records/
- **Metadata Section**: Contains Parent Document and Related Reference links
- **Evidence Sections**: What Happened, What Changed, What Comes Next

Note: 프로젝트별 폴더 규칙이 있으면 그 규칙을 우선합니다.

### Output Format

**Required Metadata Fields:**
```markdown
# Meta
- Parent Document: [[task_001.md]] (or [[roadmap.md]])
- Related Reference: [[roadmap.md]], [[archi_design.md]], [[decision_db.md]]
```

**Required Contents Sections:**
- **What Happened**: 2-6 line summary of work performed
- **What Changed**: Bullet list of files/artifacts with paths or links
- **다음 액션 (Next Actions)**: Proposals for Roadmap updates or next Task priorities

### Evidence Requirements
- All changed files must be verifiable (exist in repository)
- Parent Document must exist and be linkable
- Roadmap link must be present in Related Reference for loop continuity
- Proposals in 다음 액션 must be specific (not vague "continue work")

---

## Quality Checklist

- [ ] Run Record metadata includes Parent Document (Task or Roadmap)
- [ ] Run Record metadata Related Reference includes Roadmap link
- [ ] All changed artifacts are listed in What Changed section
- [ ] What Happened section is concise and factual (2-6 lines)
- [ ] 다음 액션 proposes specific Roadmap or Task updates
- [ ] No wildcard link patterns (task_*.md) exist anywhere
- [ ] All Obsidian links use proper format: [[filename.md]]
- [ ] Metadata-first principle maintained: relationships declared in metadata
- [ ] Run Record does not command actions (only proposes)
- [ ] Evidence is verifiable (files exist, work can be confirmed)
- [ ] File is saved in proper location (docs/run_records/ or docs/ops/run_records/)
- [ ] Document is readable in both Obsidian and IDE plain text contexts

---

## Failure Modes & Recovery

**Failure Mode 1: No Actual Work Performed**  
**Symptom**: Run Record created but no files changed or deliverables produced  
**Recovery**: Do not create Run Record without evidence. Work first, record second.

**Failure Mode 2: Missing Roadmap Link**  
**Symptom**: Related Reference does not include Roadmap link  
**Recovery**: Add `[[roadmap.md]]` to Related Reference for loop continuity

**Failure Mode 3: Parent Document Ambiguity**  
**Symptom**: Unclear whether to link Task or Roadmap as Parent  
**Recovery**: If specific Task exists, use Task. Otherwise use Roadmap. Default to Task when available.

**Failure Mode 4: Wildcard Links Used**  
**Symptom**: Links like `[[task_*.md]]` appear in metadata or body  
**Recovery**: Replace with real Task filenames from the current work

**Failure Mode 5: Command Language in 다음 액션**  
**Symptom**: "Update Roadmap to X" instead of "Propose Roadmap update: X"  
**Recovery**: Reframe as proposals. Run Records suggest, operators/agents decide.

**Failure Mode 6: Vague Next Actions**  
**Symptom**: "Continue work on system" instead of specific proposals  
**Recovery**: Be specific. "Propose marking Task 001 Done, start Task 002 (API design)"

**Failure Mode 7: Body-Only Relationships**  
**Symptom**: Artifacts mentioned in body but not in Related Reference metadata  
**Recovery**: Add artifact links to metadata first

**Failure Mode 8: IDE Formatting Breaks**  
**Symptom**: Run Record unreadable in VS Code due to complex formatting  
**Recovery**: Simplify markdown. Use bullet lists instead of complex tables. Test in plain text view.

---

## Minimal Example (Text-only)

**Scenario**: After completing Task 001 (system architecture design), creating Run Record to close loop and propose Roadmap update.

**Run Record File**: `run_record_20260121_system_arch.md`

```markdown
# Run Record: System Architecture Design

# Meta
- Parent Document: [[task_001.md]]
- Related Reference: [[roadmap.md]], [[archi_system_design.md]], [[decision_db_choice.md]]

---

## What Happened

Completed Task 001 by designing the system architecture. Created high-level component diagram with three tiers (frontend, API, database). Documented technology stack decisions and data flow patterns. Aligned architecture with PRD requirements from Phase 0.

## What Changed

**Created:**
- `docs/dev/archi/archi_system_design.md` - System architecture document with component diagrams
- `docs/dev/decision/decision_db_choice.md` - Decision record for PostgreSQL selection

**Modified:**
- None

## 다음 액션 (Next Actions)

**Roadmap Update Proposal:**
- Mark Task 001 as Done in Roadmap
- Add this Run Record link to Roadmap metadata Related Reference
- Update Phase 1 status: remains "In Progress" (Task 002 not yet complete)
- Record change in 변경 이력: "Task 001 completed, architecture designed" with evidence link to this Run Record

**Next Task Proposal:**
- Start Task 002: API Specification Design
- Input: Use `archi_system_design.md` as reference for API endpoints

**Blockers:**
- None identified
```

**Key Observations:**
- Parent Document is specific Task (preferred)
- Related Reference includes Roadmap (loop continuity), architecture doc (artifact), decision doc (related)
- What Changed lists real files with paths
- 다음 액션 proposes specific Roadmap updates (not commands)
- No wildcard links
- Readable in both Obsidian and plain text IDE view
