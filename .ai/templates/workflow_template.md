# Meta
- Workflow Name: [Workflow Name]
- File Name: [filename].workflow.md
- Document ID: WF-[CATEGORY]-[NUMBER]
- Status: [Active/Draft/Deprecated]
- Created Date: {{CURRENT_DATE}}
- Last Updated: {{CURRENT_DATE}}
- Author: {{USER}}
- Reviewer: {{REVIEWER}}
- Parent Document: [[workflow_base.md]]
- Related Reference: [[anchor_template.md]], [[roadmap_template.md]], [[task_template.md]], [[run_record_template.md]]
- Version: 1.0.0

---

# Workflow Template

## Purpose
Workflow for systematic management of [workflow_type] processes while maintaining the continuous operational loop: Roadmap → Task → Run Record → Roadmap.

## Workflow Goal
Maintain operational loop continuity by ensuring:
- All work is traceable through metadata-linked documents
- Session interruptions do not break continuity
- IDE AI can resume from repository state at any time
- Run Records enable the next Roadmap/Session selection

## Base Workflow
This workflow extends: [[workflow_base.md]]
Inherits: L1/L2 definitions, Standard stages 1-4, Constraint categories, Operational loop

---

## Workflow Overview
[Provide comprehensive overview of the entire workflow lifecycle from start to finish]

**Operational Loop Integration**:
- This workflow operates within the standard loop: Anchor → Decision → Roadmap → Session → Task → Run Record
- Roadmap items track phase/session structure with three states: Work Not Started, In Progress, Done
- Tasks are the smallest executable units linked to Roadmap items via metadata
- Run Records close the loop after any meaningful work

---

## Workflow Stages

### 1. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or Anchor

### 2. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output

### 3. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output

### 4. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output

### 5. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output

### 6. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output

### 7. [Stage Name]
- **Responsible**: [Agent/Role Name]
- **Input**: [Input description]
- **Output**: [Output description]
- **Template**: [[template_name.md]]
- **Deliverable**: docs/dev/[category]/[filename]_<project>.md (version information managed in Meta section)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output

---

## Roadmap Item Template

Each roadmap item must rely on metadata for linkage.

### Roadmap Item Structure
```markdown
## Phase/Session: [Name]

**Status**: [Work Not Started | In Progress | Done]

**Linked Tasks**:
- [[task_001.md]]
- [[task_002.md]]

**Related Run Records**:
- [[run_record_20260121_session01.md]]
- [[run_record_20260121_session02.md]]

**Description**: [Brief description of this phase/session]
```

### Status Derivation Rules
- **Work Not Started**: No linked Tasks exist or all linked Tasks are incomplete
- **In Progress**: At least one linked Task is active or in progress
- **Done**: All linked Tasks are complete and deliverables are verified

**Critical**: Task linkage MUST be expressed in Task metadata (Parent Document field), not only in Roadmap body text. Body text may summarize, but metadata is authoritative.

---

## Session Planning Block

### Session Objective
Define the objective for this operational work slice:
- What will be accomplished in this session?
- Which Roadmap items will be addressed?
- Which Tasks will be selected or created?

### Selected Tasks
List tasks to be executed in this session (linked via metadata):
- [[task_001.md]] - [Brief description]
- [[task_002.md]] - [Brief description]

### Session Completion Requirement
**Critical**: Session completion requires a Run Record.
- Run Record must be created after any meaningful work
- Run Record documents what happened, what changed, what comes next
- Run Record proposes Roadmap updates (status changes, new tasks)

---

## Task Expectations

Task documents MUST:

### 1. Metadata Requirements
```markdown
# Meta
- Parent Document: [[roadmap.md]]
- Related Reference: (optional: other related Tasks or Decisions)
```

### 2. Done Criteria
Each Task must define clear, verifiable Done criteria:
- What deliverable will be produced?
- What quality standard must be met?
- What validation/review is required?

### 3. Template Compliance
Tasks must follow [[task_template.md]] structure

---

## Run Record Expectations

Run Records MUST:

### 1. Metadata Requirements
```markdown
# Meta
- Parent Document: [[roadmap.md]]
- Related Reference: [[task_001.md]], [[decision_api_design.md]]
```

### 2. Content Requirements
1. **What Happened**: Summary of work performed
2. **What Changed**: Files/artifacts created or modified (with links)
3. **What Comes Next**: Proposed next actions
4. **Roadmap Updates**: Status update proposals (proposal only, not authoritative)

### 3. Timing
Run Records are created:
- After completing one or more Tasks
- After making progress on a Task (partial work)
- After discovering blockers or changing direction
- After any work that moves the project forward

**Key Distinction**: Run Records replace chat session closing declarations. They are evidence, not commands.

---

## Agent Roles

### [Primary Agent Name]
- [Role description and responsibilities]
- [Key functions and duties]
- [Decision making authority]
- **L1/L2 Capability**: [Can serve as L1 author / L2 reviewer / Both]

### [Secondary Agent Name]
- [Role description and responsibilities]
- [Key functions and duties]
- [Collaboration scope]
- **L1/L2 Capability**: [Can serve as L1 author / L2 reviewer / Both]

### [Optional Agent Name]
- [Role description and responsibilities]
- [Key functions and duties]
- [Participation conditions]
- **L1/L2 Capability**: [Can serve as L1 author / L2 reviewer / Both]

---

## Related Documents

### Templates
- [[prd_template.md]] - Stage 1 Planning
- [[architecture_template.md]] - Stage 2 Design
- [[spec_template.md]] - Stage 3 Specification
- [[decision_template.md]] - Stage 4 Decision
- [[task_template.md]] - Task creation
- [[roadmap_template.md]] - Roadmap structure (operational loop driver)
- [[run_record_template.md]] - Run Record format (execution evidence)
- [[report_template.md]] - Final reporting

### Operational Loop Integration Note
**Workflow와 Roadmap/Run Record 연계**:
- 이 Workflow 문서는 도메인별 단계와 역할을 정의합니다
- 실제 실행 추적은 [[roadmap_template.md]]와 [[run_record_template.md]]를 사용합니다
- Workflow Meta의 Related Reference에 활성 Roadmap과 주요 Run Records를 링크하세요
- Roadmap은 Workflow 단계를 phase/session으로 구체화하고, Run Records는 실행 증거를 제공합니다

### Agents
- [[pm.agent.md]] - PM agent
- [[developer.agent.md]] - Development agent
- [[finance.agent.md]] - Finance agent
- [[contents-creator.agent.md]] - Contents creation agent
- [[hr.agent.md]] - HR agent

### Skills
- .ai/skills/pm/ - PM related skills
- .ai/skills/developer/ - Development related skills
- .ai/skills/finance/ - Finance related skills
- .ai/skills/contents-creator/ - Contents creation related skills
- .ai/skills/hr/ - HR related skills

### Validators
- [[meta_validator.md]] - Metadata validation
- [[structure_validator.md]] - Document structure validation
- Domain-specific validators as needed

---

## Constraint Conditions

### 1. Quality Standards
- All deliverables must comply with templates
- Quality thresholds must be met
- Review processes must be followed
- Metadata linkage is mandatory for all workflow artifacts

### 2. Metadata Integrity
- All document relationships MUST be declared in metadata
- Parent Document and Related Reference fields are mandatory
- Body text may explain, but metadata is authoritative
- If a relationship is not in metadata, it does not exist

### 3. Domain-Specific Compliance
- [Domain-specific requirements]
- [Regulatory compliance if applicable]
- [Industry standards adherence]

### 4. Security/Legal Requirements
- Security review at appropriate stages
- Sensitive information handling
- Legal compliance verification

### 5. Performance Requirements
- Performance standards satisfaction
- Efficiency metrics achievement
- Optimization targets

---

## Success Indicators

### 1. Operational Continuity
- Session interruptions do not break workflow continuity: 100% target
- All work is resumable from repository state: 100% target
- Metadata linkage is complete and accurate: 100% target

### 2. Quality Metrics
- Template compliance: 100% target
- Pass rate: 95%+ target
- Satisfaction: Target value or higher

### 3. Efficiency Metrics
- Period compliance: Target adherence
- Budget compliance: Target adherence
- Reuse/optimization rate: Improving trend

### 4. Performance Metrics
- ROI/Impact achievement: Target or higher
- Stakeholder satisfaction: Target or higher
- System/process stability: Target or higher

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | {{CURRENT_DATE}} | Initial workflow template |
| 2.0 | 2026-01-21 | Added operational loop, metadata requirements, Run Record model |
