# Workflow Base

**Purpose**: Unified base workflow pattern defining the continuous operational loop that all domain workflows inherit from. This base establishes the metadata-first linking approach and artifact relationships that enable session-resilient work continuity.

---

## Version & Status
- Version: v2.0
- Status: Stable
- Core Loop: Roadmap → Task → Run Record → Roadmap update
- Enforcement: metadata-first linking; no wildcard Obsidian links
- Key Templates: [[roadmap_template.md]], [[run_record_template.md]]
- Key Shared Skills:
  - [[operational_roadmap_management.skill.md]]
  - [[operational_run_record_creation.skill.md]]

---

## Core Operational Loop

The workflow system maintains a continuous operational loop that enables any IDE-based AI or operator to resume work from the current repository state:

```
Anchor → Decision → Roadmap → Session → Task → Run Record
                        ↑                            ↓
                        └────────── (loop) ──────────┘
```

**Loop Continuity Principles**:
- **Anchor** establishes project purpose and goals (created once, rarely updated)
- **Decision** records what changed and why (created when decisions are made)
- **Roadmap** defines phases/sessions and current position (continuously updated)
- **Session** is an operational work slice containing one or more Tasks
- **Task** is the smallest executable unit of work
- **Run Record** closes the loop after any meaningful work, enabling next Roadmap/Session selection

**Continuity Guarantee**: Run Records ensure that work can always resume from the last recorded state. The IDE AI reads the repository state (Roadmap + Run Records) to understand what was done and what comes next.

---

## Artifact Roles and Relationships

### Anchor
- **Purpose**: Project purpose and goals only
- **Created**: Once at project initiation
- **Updated**: Rarely (major pivots only)
- **Metadata Links**: None (root document)
- **Location**: docs/anchor/

### Decision
- **Purpose**: Records changes only (what changed and why)
- **Created**: When significant decisions are made
- **Metadata Links**: Parent Document (Anchor or Roadmap)
- **Location**: docs/decisions/

### Roadmap
- **Purpose**: Phase/session structure + current position
- **Created**: After Anchor and initial Decisions
- **Updated**: Continuously based on Run Record proposals
- **Metadata Links**:
  - Parent Document: [[anchor.md]]
  - Related Reference: [[task_001.md]], [[run_record_20260121.md]]
- **Status Model**: See "Roadmap Status Model" section below
- **Location**: docs/roadmap/ or vault/drafts/

### Task
- **Purpose**: Smallest executable unit with done criteria
- **Created**: During session planning
- **Metadata Links**:
  - Parent Document: [[roadmap.md]]
- **Location**: docs/tasks/

### Run Record
- **Purpose**: Operational execution record replacing chat session declarations
- **Created**: After any meaningful work (not only at task/session end)
- **Metadata Links**:
  - Parent Document: [[roadmap.md]]
  - Related Reference: [[task_001.md]], other artifacts modified
- **Content**: What happened, what changed, what comes next, Roadmap update proposals
- **Location**: ops/run_records/

---

## Roadmap Status Model

Roadmap items must use exactly three states:

### Status Definitions
- **Work Not Started**: No linked Tasks exist or all linked Tasks are incomplete
- **In Progress**: At least one linked Task is active or in progress
- **Done**: All linked Tasks are complete and deliverables are verified

### Status Derivation Rules
1. Roadmap status is derived from linked Task states
2. Task linkage is expressed in metadata (Parent Document / Related Reference)
3. Roadmap stores status + links, NOT execution logs
4. Execution details belong in Run Records, not Roadmap

**Percentage Progress**: Not implemented in this phase. Status is binary per item.

---

## Metadata-First Linking Rule (MANDATORY)

**Critical Principle**: All document relationships MUST be declared in metadata.

### Why Metadata-First
- **AI Continuity**: IDE AI can parse metadata to understand document graph
- **Operator Continuity**: Humans can navigate via Obsidian links
- **Session Resilience**: Relationships survive chat session interruptions
- **Structural Integrity**: Body text may change; metadata relationships are stable

### Enforcement
- Body text MUST NOT be the sole place where relationships are defined
- Body sections may explain or summarize, but metadata is authoritative
- If a relationship is not in metadata, it does not exist for operational purposes

### Standard Metadata Fields
All workflow artifacts must include:
- **Parent Document**: Primary parent in document hierarchy
- **Related Reference**: Other related documents (Tasks, Run Records, Decisions)

---

## Run Record as Session Closure Replacement

**Old Pattern (Chat-Based)**: Session ends when chat declares "session closed"
**New Pattern (Repository-Based)**: Run Record created after any meaningful work

### When to Create Run Records
- After completing one or more Tasks
- After making progress on a Task (partial work)
- After discovering blockers or changing direction
- After any work that moves the project forward

### Run Record Content Requirements
1. **What Happened**: Summary of work performed
2. **What Changed**: Files/artifacts created or modified
3. **What Comes Next**: Proposed next actions
4. **Roadmap Updates**: Status update proposals (proposal only, not authoritative update)

**Key Distinction**: Run Records are evidence, not commands. The operator or next session decides whether to accept proposed Roadmap updates.

---

## Minimal Metadata Expectations

### Roadmap Metadata
```markdown
# Meta
- Parent Document: [[anchor.md]]
- Related Reference: [[task_001.md]], [[task_002.md]], [[run_record_20260121.md]]
```

### Task Metadata
```markdown
# Meta
- Parent Document: [[roadmap.md]]
- Related Reference: (optional: other related Tasks or Decisions)
```

### Run Record Metadata
```markdown
# Meta
- Parent Document: [[roadmap.md]]
- Related Reference: [[task_001.md]], [[decision_api_design.md]]
```

---

## Standard 4-Stage Pattern (Stages 1-4)

All domain workflows use these 4 base stages with domain-specific context:

### Stage 1: Planning/Strategy
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Planning |
| Responsible | PM Agent + Domain Agent |
| Input | Business objectives, market research |
| Output | Strategy document |
| Template | [[prd_template.md]] |
| Deliverable | docs/dev/PRD/prd_<domain>.md |

### Stage 2: Design/Architecture
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Design |
| Responsible | Domain Agent |
| Input | Strategy document |
| Output | Design document |
| Template | [[architecture_template.md]] |
| Deliverable | docs/dev/archi/<domain>_design_<project>.md |

### Stage 3: Specification
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Specification |
| Responsible | Domain Agent |
| Input | Design document, requirements |
| Output | Specification document |
| Template | [[spec_template.md]] |
| Deliverable | docs/dev/spec/<domain>_spec_<module>.md |

### Stage 4: Decision Making
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Decision Making |
| Responsible | Domain Agent + PM Agent |
| Input | Specification, constraints |
| Output | Decision record |
| Template | [[decision_template.md]] |
| Deliverable | docs/decisions/decision_<domain>_<date>.md |

---

## Domain-Specific Stages (Stages 5-7)

Stages 5-7 vary by domain:

### Software Development
- Stage 5: Development Implementation
- Stage 6: Testing and Verification
- Stage 7: Deployment and Operations

### Contents Creation
- Stage 5: Contents Production
- Stage 6: Quality Verification
- Stage 7: Final Deliverables

### Financial Management
- Stage 5: Budget Execution
- Stage 6: Financial Monitoring
- Stage 7: Performance Analysis

### Project Management
- Stage 5: Project Execution
- Stage 6: Project Monitoring
- Stage 7: Performance Management

---

## L1/L2 Role Definitions (SINGLE SOURCE OF TRUTH)

**IMPORTANT**: All workflows inherit these definitions. DO NOT duplicate in individual workflows.

### L1 Agent (Author) Responsibilities
- Document creation and initial development
- Basic quality assurance and self-review
- Submission for L2 review process
- **Meta Field**: Author field assignment
- **Skill Level**: Junior-level skills (basic implementation, standard procedures)

### L2 Agent (Reviewer) Responsibilities
- Senior-level work review and validation
- Technical excellence assessment
- Final approval and certification
- **Meta Field**: Reviewer field assignment
- **Skill Level**: Senior-level skills (strategic, leadership, complex analysis)

### L1/L2 Collaboration Pattern
```
L1 Agent (Author) → Creates initial work
         ↓
L2 Agent (Reviewer) → Reviews and validates
         ↓
Final Approval → Meta Reviewer field populated
```

---

## Standard Agent Roles by Domain

### Domain-Agent Mapping
| Domain | Primary Agent | Supporting Agents |
|--------|---------------|-------------------|
| Software Development | Developer | PM, Finance (optional) |
| Contents Creation | Contents-Creator | PM, Finance (optional) |
| Financial Management | Finance | PM, Developer (optional) |
| Project Management | PM | All agents as needed |
| HR Evaluation | HR | All agents as subjects |

### Standard PM Agent Role
- Strategy establishment & goal setting
- Market research & competitive analysis
- Stakeholder communication & expectation management
- **L1/L2**: Can serve as L1 author, L2 reviewer

### Standard Finance Agent Role (Optional)
- Cost budget analysis
- ROI evaluation & financial feasibility
- Resource allocation optimization
- **L1/L2**: Can serve as L1 author, L2 reviewer

---

## Standard Constraint Categories

All workflows should include these constraint categories:

### 1. Quality Standards
- All deliverables must comply with templates
- Quality thresholds must be met
- Review processes must be followed

### 2. Domain-Specific Compliance
- [Domain-specific requirements]
- [Regulatory compliance if applicable]
- [Industry standards adherence]

### 3. Security/Legal Requirements
- Security review at appropriate stages
- Sensitive information handling
- Legal compliance verification

### 4. Performance Requirements
- Performance standards satisfaction
- Efficiency metrics achievement
- Optimization targets

---

## Standard Success Indicators

All workflows should include these metric categories:

### 1. Quality Metrics
- Pass rate: 95%+ target
- Compliance rate: 100% target
- Satisfaction: Target value or higher

### 2. Efficiency Metrics
- Period compliance
- Budget compliance
- Reuse/optimization rate

### 3. Performance Metrics
- ROI/Impact achievement
- Stakeholder satisfaction
- System/process stability

---

## Integration Points

### Template References
All workflows use these standard templates:
- [[prd_template.md]] - Stage 1 (Planning)
- [[architecture_template.md]] - Stage 2 (Design)
- [[spec_template.md]] - Stage 3 (Specification)
- [[decision_template.md]] - Stage 4 (Decision)
- [[task_template.md]] - Task creation
- [[roadmap_template.md]] - Roadmap structure
- [[run_record_template.md]] - Run Record format

### Operational Loop Templates
The continuous operational loop is supported by these key templates:
- [[roadmap_template.md]] - Defines phases/sessions, tracks status, links to Tasks and Run Records
- [[task_template.md]] - Smallest executable unit, Parent Document references Roadmap
- [[run_record_template.md]] - Execution evidence, proposes Roadmap updates

**Loop Flow**: Roadmap → Task → Run Record → Roadmap update
- Roadmap drives what work needs to be done
- Tasks execute the work (one or more per session)
- Run Records document what happened and propose next steps
- Roadmap is updated based on Run Record proposals

### Validator References
- [[meta_validator.md]] - All document meta validation
- [[structure_validator.md]] - All document structure validation
- Domain-specific validators as needed

### L2 Review Integration
All workflows connect to:
- [[l2_review.workflow.md]] - For L2 work validation
- [[l2_review_validator.md]] - For L2 quality assessment

### Agents/Skills 연계 규칙
- **Skills 산출물 기록**: Skills가 생성하는 산출물은 Run Record에 기록됨
- **Agent 실행 추적**: Agents가 Skills를 실행하며, Run Record는 agent/skill 식별자 또는 문서를 참조
- **메타데이터 우선**: 복잡한 크로스링크 확산보다 Meta 링크와 간단한 규칙 선호
- **템플릿 기반 일관성**: 모든 artifact는 해당 템플릿을 따라 생성되어 구조 일관성 유지

---

## Usage Instructions

### For Domain Workflow Authors

1. **Reference this base**:
```markdown
## Base Workflow
This workflow extends: [[workflow_base.md]]
Inherits: L1/L2 definitions, Standard stages 1-4, Constraint categories, Operational loop
```

2. **Define only domain-specific elements**:
- Domain-specific stages 5-7
- Domain-specific agent role details
- Domain-specific success indicators

3. **Do NOT duplicate**:
- L1/L2 role definitions (reference this base)
- Operational loop structure (reference this base)
- Metadata-first linking rules (reference this base)
- Standard 4-stage pattern (customize names only)
- Standard constraint categories (add domain-specific)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial base workflow creation |
| 2.0 | 2026-01-21 | Added operational loop, metadata-first linking, Run Record model |
