# Meta
- Workflow Name: HR Evaluation Workflow
- File Name: hr_evaluation.workflow.md
- Document ID: WF-HR-001
- Status: Active
- Created Date: 2026-01-16
- Last Updated: 2026-01-16
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# HR Evaluation Workflow

## Workflow Overview
Automated process sequence definition for HR role evaluation

## Process Stages

### 1. Task Creation
- **Input**: User request ("create a new role" or "evaluate a position")
- **Action**: Create Task Template based document in `docs/tasks/` directory
- **Template**: `.ai/templates/task_template.md`
- **Output**: `task_<role>_<dept>.md` file

### 2. Structure Validation
- **Input**: Created Task document
- **Validator**: `.ai/validators/task_validator.md`
- **Skill**: `hr_onboarding.skill.md`
- **Output**: PASS/FAIL result + missing fields list

### 3. Level Judgment
- **Input**: Structure validated Task document
- **Skill**: `hr_level_check.skill.md`
- **Logic**: Department keyword-based L1/L2/PENDING judgment
- **Output**: Level result + judgment basis

### 4. Report Generation
- **Input**: Task information + Level judgment result
- **Skill**: `hr_report_emit.skill.md`
- **Template**: `.ai/templates/report_template.md`
- **Output**: `report_<role>_<dept>_<YYYYMMDD>.md`

## Agent Coordination
- **Primary Management**: HR Agent (`.ai/agents/hr.agent.md`)
- **Distribution**: Development/contents/Other department specialized agents
- **Result Collection**: Final report integration

## L1/L2 Role Definitions

### L1 Agent (Author) Responsibilities
- Task document creation and initial role definition
- Basic quality assurance and self-review
- Submission for L2 review process
- **Meta Field**: Author field assignment

### L2 Agent (Reviewer) Responsibilities
- Senior-level role evaluation and validation
- Level determination (L1/L2/PENDING)
- Final report generation and certification
- **Meta Field**: Reviewer field assignment

## Constraint Conditions
- **Meta Isolation**: Prohibit evaluation result influence by Meta section data
- **Pending Protocol**: PENDING status + improvement feedback mandatory when criteria insufficient
- **Structured Output**: Comply with format for other agent consumption

## Related Documents
- `.ai/.cursorrules` - Global workflow rules
- `.ai/agents/hr.agent.md` - HR agent details
- `.ai/skills/hr/` - HR related skills
