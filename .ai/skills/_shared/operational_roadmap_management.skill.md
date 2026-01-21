# Operational Roadmap Management

**Skill Name**: Operational Roadmap Management  
**Skill ID**: SKILL-OPS-ROADMAP-v1

---

## Purpose

This skill enables operators and agents to create or update a Roadmap instance that maintains operational loop continuity. The Roadmap serves as the central coordination artifact, linking to Tasks and Run Records via metadata-first relationships. Status updates are derived from linked Task states and evidenced by Run Record citations, ensuring any IDE-based AI or operator can resume work from the current repository state.

---

## When to Use / When NOT to Use

**When to Use:**
- Creating a new Roadmap for a project phase or work cycle
- Updating Roadmap status when Tasks are added, completed, or changed
- Recording Roadmap changes based on Run Record evidence
- Establishing phase/session structure for operational work

**When NOT to Use:**
- For creating individual Tasks (use task creation skills instead)
- For execution logging (use Run Record creation instead)
- For strategic planning without operational Task linkage (use Anchor or Decision docs)

---

## Inputs (Contract)

### Required Inputs
- **Roadmap Template**: Reference to [[roadmap_template.md]] or equivalent
- **Anchor Document**: Link to project anchor for Parent Document metadata
- **Update Trigger**: Reason for Roadmap creation/update (new Task, Task completion, Run Record proposal, Decision change)

### Optional Inputs
- **Existing Roadmap**: If updating, path to current Roadmap file
- **Task Links**: List of Task filenames to link in metadata
- **Run Record Links**: List of Run Record filenames for change evidence
- **Decision Links**: Related Decision documents

### Input Format
```
Update Trigger: [New Task | Task Status Change | Run Record Proposal | Decision Change]
Anchor Document: [[anchor.md]]
Task Links: [[task_001.md]], [[task_002.md]]
Run Record Links: [[run_record_20260121.md]]
```

### Preconditions
- Anchor document exists and is accessible
- All referenced Task and Run Record files exist with proper metadata
- No wildcard link patterns are used (no `task_*.md` patterns)

---

## Process (Step-by-step)

### Core Process

1. **Identify Update Trigger** - Determine why the Roadmap needs creation or update (see Roadmap Update Triggers below)

2. **Locate or Create Roadmap File** - If creating new, use [[roadmap_template.md]] as base; if updating, open existing Roadmap

3. **Update Metadata Section** - Ensure metadata contains:
   - Parent Document: `[[anchor.md]]`
   - Related Reference: All linked Tasks and Run Records using real filenames

4. **Review Linked Task States** - For each Task in Related Reference, check current status (not started, in progress, done)

5. **Derive Roadmap Item Status** - Apply Status Derivation Rule (see below) to each Roadmap phase/session based on linked Task states

6. **Record Change in 변경 이력 (Change History)** - Add new row with:
   - Date/Time
   - What changed (status, new Task added, etc.)
   - Run Record citation as evidence (if applicable)

7. **Update Phase/Session Links** - Ensure each phase/session item lists its linked Tasks in contents body (not just metadata)

8. **Validate Link Hygiene** - Confirm no wildcard patterns (`*`) exist in any Obsidian links

9. **Verify Metadata-First Principle** - All Task and Run Record relationships must appear in metadata fields before being mentioned in body text

10. **Save Roadmap** - Write changes to file with proper formatting

### Roadmap Update Triggers

- **New Task Added**: Link new Task in metadata Related Reference, update relevant phase/session status
- **Task Status Changes**: Re-derive Roadmap status based on updated Task states
- **New Run Record Created**: Add Run Record link to metadata, cite in 변경 이력 if Roadmap status changes
- **Decision Changes**: Link Decision document in Related Reference; Run Records are primary evidence for Roadmap changes

### Status Derivation Rule

Roadmap phases/sessions use exactly three states:

- **Work Not Started**: No linked Tasks exist OR all linked Tasks are incomplete
- **In Progress**: At least one linked Task is active or in progress
- **Done**: All linked Tasks are complete and deliverables are verified

**Important**: Status is derived from Task linkage expressed in metadata. Do NOT use percentage progress. Roadmap stores status + links, NOT execution logs (those belong in Run Records).

**Task Status Derivation Guard**: If a Task does not have an explicit Status field, derive its state from completion of checklist items or done criteria. The 3-state model (Work Not Started / In Progress / Done) applies regardless.

---

## Outputs (Contract)

### Primary Outputs
- **Updated Roadmap File**: `roadmap.md` in `docs/roadmaps/` (default) or `docs/drafts/` (alternative)
- **Metadata Section**: Contains current Parent Document and all Related Reference links
- **변경 이력 (Change History)**: Updated with new row(s) citing evidence

Note: 프로젝트별 폴더 규칙이 있으면 그 규칙을 우선합니다.

### Output Format

**Required Metadata Fields:**
```markdown
# Meta
- Parent Document: [[anchor.md]]
- Related Reference: [[task_001.md]], [[task_002.md]], [[run_record_20260121.md]]
```

**Required Contents Sections:**
- Phase/Session structure with status indicators
- 변경 이력 (Change History) table with columns: Date, Change, Evidence (Run Record link)

### Evidence Requirements
- Every status change must cite a Run Record link in 변경 이력
- Task completion claims must reference completed Task files
- All links must use real filenames (no wildcards)

---

## Quality Checklist

- [ ] Roadmap metadata includes Parent Document: [[anchor.md]]
- [ ] Roadmap metadata Related Reference lists all Tasks and Run Records (real filenames only)
- [ ] No wildcard link patterns (task_*.md) exist anywhere in the document
- [ ] Each phase/session status is one of: Work Not Started, In Progress, Done
- [ ] Status derivation aligns with linked Task states
- [ ] 변경 이력 includes at least one entry for this update
- [ ] Every status change in 변경 이력 cites a Run Record link as evidence
- [ ] Metadata-first principle maintained: all relationships declared in metadata before body mentions
- [ ] All Obsidian links use proper format: [[filename.md]]
- [ ] Roadmap does not contain execution logs (those belong in Run Records)
- [ ] File is saved in proper location (docs/roadmaps/ or docs/drafts/)
- [ ] Document is readable by both humans (Obsidian navigation) and IDE AI (metadata parsing)

---

## Failure Modes & Recovery

**Failure Mode 1: Wildcard Links Used**  
**Symptom**: Links like `[[task_*.md]]` appear in metadata or body  
**Recovery**: Replace with real Task filenames or explicit example markers

**Failure Mode 2: Status Not Derived from Tasks**  
**Symptom**: Roadmap shows "In Progress" but no linked Tasks exist or are active  
**Recovery**: Review linked Tasks, update Task links in metadata, re-derive status

**Failure Mode 3: Missing Run Record Evidence**  
**Symptom**: 변경 이력 shows status change but no Run Record citation  
**Recovery**: Create Run Record for the work that triggered the change, then cite it

**Failure Mode 4: Metadata Missing or Incomplete**  
**Symptom**: Parent Document or Related Reference fields are empty  
**Recovery**: Add [[anchor.md]] as Parent, add all Task and Run Record links to Related Reference

**Failure Mode 5: Body-Only Relationships**  
**Symptom**: Tasks mentioned in body text but not in metadata Related Reference  
**Recovery**: Add all Task links to metadata first, then body mentions are acceptable

**Failure Mode 6: Execution Logs in Roadmap**  
**Symptom**: Roadmap contains detailed "what we did" logs instead of status + links  
**Recovery**: Move execution details to Run Records, keep only status and links in Roadmap

**Failure Mode 7: Percentage Progress Used**  
**Symptom**: Roadmap shows "75% complete" or similar metrics  
**Recovery**: Replace with 3-state status (Work Not Started / In Progress / Done) derived from Tasks

**Failure Mode 8: Broken Links**  
**Symptom**: Linked Task or Run Record files do not exist  
**Recovery**: Create missing files or remove broken links from metadata

---

## Minimal Example (Text-only)

**Scenario**: Updating Roadmap after completing Task 001 and creating a Run Record.

**Roadmap Meta Snippet (Before Update):**
```markdown
# Meta
- Parent Document: [[anchor.md]]
- Related Reference: [[task_001.md]], [[task_002.md]]

---

## Phase 1: System Setup
- Status: In Progress
- Linked Tasks: [[task_001.md]], [[task_002.md]]
```

**Run Record Evidence:**
```markdown
File: run_record_20260121_system_setup.md
# Meta
- Parent Document: [[task_001.md]]
- Related Reference: [[roadmap.md]], [[archi_design.md]]

## What Happened
Completed Task 001 (System architecture design). Created architecture document.

## 다음 액션 (Next Actions)
Propose Roadmap update: Mark Task 001 as Done. Phase 1 remains In Progress (Task 002 not complete).
```

**Roadmap Meta Snippet (After Update):**
```markdown
# Meta
- Parent Document: [[anchor.md]]
- Related Reference: [[task_001.md]], [[task_002.md]], [[run_record_20260121_system_setup.md]]

---

## Phase 1: System Setup
- Status: In Progress
- Linked Tasks: [[task_001.md]] (Done), [[task_002.md]] (In Progress)

## 변경 이력 (Change History)
| Date | Change | Evidence |
|------|--------|----------|
| 2026-01-21 14:30 | Task 001 completed, added Run Record link | [[run_record_20260121_system_setup.md]] |
```

**Key Observations:**
- Metadata now includes Run Record link in Related Reference
- Phase 1 status remains "In Progress" (derived rule: at least one Task in progress)
- 변경 이력 cites Run Record as evidence
- No wildcard links used
- Real filenames only
