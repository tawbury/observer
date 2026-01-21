# Workflow Index - Complete Workflow Reference

Central index mapping all workflows with their stages, agents, and dependencies.

**Operational Loop Foundation**: All workflows implement the continuous operational loop (Roadmap → Task → Run Record → Roadmap) with metadata-first linking to ensure session-resilient work continuity.

## Workflow System Version
- This index is aligned to Workflow System v2.0 (Stable).
- Core Loop: Roadmap → Task → Run Record → Roadmap update
- Key Templates: [[roadmap_template.md]], [[run_record_template.md]]

---

## Quick Navigation

- [Operator Guide](#operator-guide)
- [Metadata-First Rule](#metadata-first-rule)
- [Base Workflows](#base-workflows)
- [Domain Workflows](#domain-workflows)
- [Specialized Workflows](#specialized-workflows)
- [Orchestration](#orchestration)

---

## Operator Guide

### Usage Flow
Follow this simple operational pattern for any workflow:

1. **Start with Roadmap**
   - Review current Roadmap state (phases/sessions and their status)
   - Identify next work item (Work Not Started or In Progress)
   - Select or create Tasks for the next operational session

2. **Execute Tasks**
   - Work on selected Tasks (one or more per session)
   - Create or modify artifacts as defined in Task
   - Ensure metadata links are correct (Parent Document, Related Reference)

3. **Create Run Record**
   - After any meaningful work, create a Run Record
   - Document: what happened, what changed, what comes next
   - Propose Roadmap updates (status changes, new tasks)
   - Link Run Record to Roadmap and Tasks via metadata

4. **Update Roadmap**
   - Review Run Record proposals
   - Update Roadmap status based on completed Tasks
   - Plan next session based on Run Record recommendations
   - Return to step 1

### Session Interruption Resilience
- **If session is interrupted**: Next session reads Roadmap + latest Run Records to understand current state
- **If context is lost**: Repository state (metadata-linked documents) is the source of truth
- **If work needs to resume**: IDE AI can parse metadata graph to determine what was done and what comes next

### Roadmap Status Quick Reference
- **Work Not Started**: No Tasks linked or all Tasks incomplete
- **In Progress**: At least one Task is active
- **Done**: All linked Tasks complete, deliverables verified

---

## Metadata-First Rule

**Critical Principle**: If a relationship is not in metadata, it does not exist.

### Why Metadata-First
- **AI Continuity**: IDE AI parses metadata to understand document relationships
- **Operator Continuity**: Humans navigate via Obsidian links ([[filename.md]])
- **Session Resilience**: Relationships survive chat session interruptions
- **Structural Integrity**: Body text may change; metadata is stable

### Enforcement
- Body text is descriptive; metadata is structural
- All Parent Document and Related Reference fields must be populated
- Use Obsidian link syntax: [[filename.md]]
- Metadata is the single source of truth for document linkage

### Example Metadata Block
```markdown
# Meta
- Project Name: Example Project
- File Name: task_001.md
- Document ID: TASK-001
- Status: In Progress
- Created Date: 2026-01-21 14:30
- Last Updated: 2026-01-21 15:45
- Author: Developer Agent
- Reviewer: PM Agent
- Parent Document: [[roadmap_v1.md]]
- Related Reference: [[decision_api_design.md]], [[run_record_20260121.md]]
- Version: 1.0
```

---

## Obsidian Link Convention

All internal document references MUST use Obsidian link syntax:

**Correct**: [[filename.md]]
**Incorrect**: `filename.md` (backticks), filename.md (plain text), ./path/filename.md (relative paths)

**Why Obsidian Links**:
- Enables clickable navigation in Obsidian and compatible editors
- Allows IDE AI to parse document graph programmatically
- Supports bidirectional linking and relationship discovery
- Standard format for metadata-first approach

---

## Base Workflows

**Location**: .ai/workflows/_base/

| Base | Purpose | Consolidates |
|------|---------|--------------|
| [[workflow_base.md]] | Standard pattern, L1/L2 definitions, Operational loop | L1/L2 roles, 4-stage pattern, Metadata-first rules |

**Key Features**:
- Defines continuous operational loop (Roadmap → Task → Run Record → Roadmap)
- Establishes metadata-first linking requirements
- Specifies Roadmap status model (Work Not Started, In Progress, Done)
- Defines Run Record as session closure replacement
- Documents artifact roles and relationships

---

## Domain Workflows

All domain workflows extend [[workflow_base.md]].

### Stock Trading System Development
**File**: [[stock_trading_system.workflow.md]]
**ID**: WF-TRADING-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. Trading Strategy Discovery | PM + Finance | trading_strategy_template |
| 2. Financial Planning & Risk Assessment | Finance + PM | risk_management_template |
| 3. Data Architecture Design | Developer + PM | data_pipeline_spec_template, architecture_template |
| 4. Trading System Architecture | Developer + Finance | architecture_template |
| 5. Integrated Specification | Developer + PM + Finance | spec_template |
| 6. Decision Making | PM + Developer + Finance | decision_template |
| 7. Parallel Implementation | Developer + Finance | - |
| 8. Backtesting & Validation | Developer + Finance | backtesting_report_template |
| 9. Deployment & Monitoring | Developer + Finance + PM | - |
| 10. Live Trading & Analysis | Finance + PM + Developer | report_template |

**Primary Agents**: PM, Developer, Finance (all required)
**Focus**: Trading strategy, data pipeline, automated trading, risk management
**Note**: Hybrid approach - integrated design, parallel development, integrated testing/deployment
**Operational Loop**: Integrated with Roadmap items tracking each stage, Tasks for implementation units, Run Records after each development/testing cycle

---

### Contents Creation
**File**: [[contents_creation.workflow.md]]
**ID**: WF-CONTENTS-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. Contents Planning | PM | prd_template |
| 2. Contents Design | Contents-Creator | architecture_template |
| 3. Production Specification | Contents-Creator | spec_template |
| 4. Production Decision | Contents-Creator + PM | decision_template |
| 5. Contents Production | Contents-Creator | - |
| 6. Quality Verification | Contents-Creator | - |
| 7. Final Deliverables | Contents-Creator | - |

**Primary Agent**: Contents-Creator
**Supporting**: PM, Finance (optional)
**Operational Loop**: Roadmap tracks content phases, Tasks define individual content pieces, Run Records document production progress

---

### Financial Management
**File**: [[financial_management.workflow.md]]
**ID**: WF-FINANCE-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. Financial Planning | Finance + PM | prd_template |
| 2. Budget Establishment | Finance | architecture_template |
| 3. Financial Specification | Finance | spec_template |
| 4. Financial Decision | Finance + PM | decision_template |
| 5. Budget Execution | Finance | - |
| 6. Financial Monitoring | Finance | - |
| 7. Performance Analysis | Finance | - |

**Primary Agent**: Finance
**Supporting**: PM, Developer (optional)
**Operational Loop**: Roadmap tracks financial periods/cycles, Tasks define analysis/reporting units, Run Records document budget execution

---

### Project Management
**File**: [[project_management.workflow.md]]
**ID**: WF-PROJECT-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. Project Planning | PM | prd_template |
| 2. Project Design | PM | architecture_template |
| 3. Requirements Specification | PM | spec_template |
| 4. Project Decision | PM | decision_template |
| 5. Project Execution | PM + Domain Agents | - |
| 6. Project Monitoring | PM | - |
| 7. Performance Management | PM | - |

**Primary Agent**: PM
**Supporting**: All agents as needed
**Operational Loop**: Roadmap tracks project phases/milestones, Tasks define project activities, Run Records document project progress

---

### HR Evaluation
**File**: [[hr_evaluation.workflow.md]]
**ID**: WF-HR-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. Task Creation | HR | task_template |
| 2. Structure Validation | HR | - |
| 3. Level Judgment | HR | - |
| 4. Report Generation | HR | report_template |

**Primary Agent**: HR
**Scope**: Agent level assessment (L1/L2/PENDING)
**Operational Loop**: Roadmap tracks evaluation cycles, Tasks define individual role assessments, Run Records document evaluation results

---

## Specialized Workflows

### L2 Review Workflow
**File**: [[l2_review.workflow.md]]
**ID**: WF-L2REVIEW-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. L2 Work Submission | L2 Agent | task_template |
| 2. Technical Review | Senior Technical Validator | architecture_template |
| 3. Business Impact Review | Business Validator | prd_template |
| 4. Leadership Review | Leadership Validator | decision_template |
| 5. Cross-Agent Integration | Integration Validator | spec_template |
| 6. Final Validation | Senior Validator | report_template |

**Purpose**: Validates L2 (senior) level work across all agents
**Operational Loop**: Roadmap tracks review cycles, Tasks define review items, Run Records document review outcomes

### Skill Consolidation Workflow
**File**: [[skill_consolidation_workflow.md]]

**Purpose**: Governs skill file consolidation and SSoT management
**Key Principles**:
- 1 step = 1 prompt (review/execution separation)
- Backup required before execution
- Non-destructive until deletion gate
**Operational Loop**: Roadmap tracks consolidation phases, Tasks define file migrations, Run Records document changes

---

## Orchestration

### Integrated Development Workflow
**File**: [[integrated_development.workflow.md]]
**ID**: WF-INTEGRATED-001

**Purpose**: Orchestrates multiple domain workflows in parallel

| Stage | PM | Developer | Contents-Creator | Finance |
|-------|----|-----------|--------------------|---------|
| 1. Business Planning | Lead | Support | Support | Lead (Financial) |
| 2. Product Definition | Lead | - | Lead (Contents) | Support |
| 3-6. Parallel Execution | Orchestrate | Technical Lead | Content Lead | Financial Lead |
| 7-8. Integration | Coordinate | Integrate | Integrate | Verify |
| 9-10. Deployment | Approve | Execute | Deliver | Audit |

**Operational Loop**: Master Roadmap orchestrates multiple sub-workflows, Tasks distributed across agents, Run Records from all agents feed into master coordination

---

## Workflow Dependencies

### Template Dependencies
```
All Workflows → Templates
├── [[prd_template.md]] (Stage 1: Planning)
├── [[architecture_template.md]] (Stage 2: Design)
├── [[spec_template.md]] (Stage 3: Specification)
├── [[decision_template.md]] (Stage 4: Decision)
├── [[task_template.md]] (HR, L2 Review, Task creation)
├── [[roadmap_template.md]] (Roadmap structure - 로드맵 구조 및 실행 추적)
├── [[run_record_template.md]] (Run Record format - 실행 증거 기록)
└── [[report_template.md]] (HR, L2 Review final)
```

**Operational Loop Templates**:
- [[roadmap_template.md]] - 프로젝트/워크플로우의 phase/session 구조를 정의하고, Task와 Run Record를 연결하여 실행을 추적합니다
- [[run_record_template.md]] - 작업 실행 후 생성되는 증거 문서로, 무엇을 했는지, 무엇이 변경되었는지, 다음 액션을 제안합니다

### Validator Dependencies
```
Domain Workflows → Validators
├── [[meta_validator.md]] (all documents)
├── [[structure_validator.md]] (all documents)
├── [[prd_validator.md]] (Stage 1 outputs)
├── [[architecture_validator.md]] (Stage 2 outputs)
├── [[spec_validator.md]] (Stage 3 outputs)
└── [[decision_validator.md]] (Stage 4 outputs)

L2 Review Workflow → Advanced Validators
├── [[l2_review_validator.md]]
├── [[senior_decision_validator.md]]
├── [[mentorship_validator.md]]
└── [[cross_agent_validator.md]]
```

### Orchestration Dependencies
```
[[integrated_development.workflow.md]]
├── orchestrates → [[software_development.workflow.md]]
├── orchestrates → [[contents_creation.workflow.md]]
├── orchestrates → [[financial_management.workflow.md]]
└── orchestrates → [[project_management.workflow.md]]

[[l2_review.workflow.md]]
└── validates → all domain workflow outputs
```

---

## Common Patterns

### Standard 4-Stage Pattern
| Stage | Name | Template | Output Type |
|-------|------|----------|-------------|
| 1 | [Domain] Planning | [[prd_template.md]] | Strategy |
| 2 | [Domain] Design | [[architecture_template.md]] | Design |
| 3 | [Domain] Specification | [[spec_template.md]] | Spec |
| 4 | [Domain] Decision | [[decision_template.md]] | Decision |

### L1/L2 Role Pattern (Inherited from base)
| Role | Responsibility | Meta Field |
|------|----------------|------------|
| L1 (Author) | Create, self-review, submit | Author |
| L2 (Reviewer) | Review, validate, certify | Reviewer |

### Operational Loop Pattern
```
Anchor → Decision → Roadmap → Session → Task → Run Record
                        ↑                            ↓
                        └────────── (loop) ──────────┘
```

**Artifacts**:
- **Anchor**: Project goals (created once)
- **Decision**: Change records (created when decisions made)
- **Roadmap**: Phase/session structure + status (continuously updated)
- **Task**: Executable units (created per session)
- **Run Record**: Execution evidence (created after work)

**Status States**: Work Not Started, In Progress, Done

---

## Success Metrics Summary

### Operational Continuity (New)
| Metric | Target | Applies To |
|--------|--------|------------|
| Session interruption resilience | 100% | All workflows |
| Work resumability from repository state | 100% | All workflows |
| Metadata linkage completeness | 100% | All workflows |

### Quality Targets
| Metric | Target | Applies To |
|--------|--------|------------|
| Pass rate | 95%+ | All workflows |
| Compliance | 100% | Templates, standards |
| Satisfaction | Target+ | Stakeholders |

### Efficiency Targets
| Metric | Target | Applies To |
|--------|--------|------------|
| Period compliance | 100% | All workflows |
| Budget compliance | 100% | All workflows |
| Optimization rate | Improving | All workflows |

---

## Version

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial index with base patterns |
| 2.0 | 2026-01-21 | Added operational loop, metadata-first rule, operator guide, session resilience |
