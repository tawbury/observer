# Meta
- Workflow Name: Project Management Workflow
- File Name: project_management.workflow.md
- Document ID: WF-PROJECT-001
- Status: Active
- Created Date: 2026-01-16
- Last Updated: 2026-01-16
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# Project Management Workflow

## Purpose
Workflow for systematic management of project management processes

## Workflow Overview
Entire project lifecycle management from project planning through execution and performance management

## Workflow Stages

### 1. Project Planning
- **Responsible**: PM Agent
- **Input**: Business objectives, market research results
- **Output**: Project strategy document
- **Template**: `.ai/templates/prd_template.md`
- **Deliverable**: `docs/dev/PRD/prd_<project>.md` (version information managed in Meta section)

### 2. Project Design
- **Responsible**: PM Agent
- **Input**: Project strategy document
- **Output**: Project structure design document
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/project_architecture_<project>.md` (version information managed in Meta section)

### 3. Requirements Specification
- **Responsible**: PM Agent
- **Input**: Project design document, stakeholder requirements
- **Output**: Project requirements specification document
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/spec/project_spec_<module>.md` (version information managed in Meta section)

### 4. Project Decision Making
- **Responsible**: PM Agent, related agents
- **Input**: Requirements specification document, constraint conditions
- **Output**: Project decision making record
- **Template**: `.ai/templates/decision_template.md`
- **Deliverable**: `docs/dev/decision/decision_<project>_<date>.md`

### 5. Project Execution
- **Responsible**: PM Agent, related agents
- **Input**: Approved project plan
- **Output**: Project execution results
- **Verification**: Progress tracking, quality management

### 6. Project Monitoring
- **Responsible**: PM Agent
- **Input**: Project execution data, performance indicators
- **Output**: Project monitoring report
- **Verification**: Schedule compliance rate, quality indicators

### 7. Project Performance Management
- **Responsible**: PM Agent
- **Input**: Project data, performance indicators
- **Output**: Project performance analysis report
- **Verification**: Goal achievement rate, ROI analysis

## Agent Roles

### PM Agent
- Project strategy establishment & roadmap management
- Stakeholder communication & expectation management
- Project progress tracking & management
- Performance analysis & reporting
- **L1 Role**: Primary author for project documents
- **L2 Role**: Senior reviewer for project quality and compliance

### Developer Agent
- Technical requirements provision
- Development schedule & resource estimation
- Technical constraint condition analysis
- Technical decision making support
- **L1/L2 Role**: Can serve as L1 author for technical documents, L2 reviewer for project feasibility

### Finance Agent
- Project budget analysis
- Cost efficiency evaluation
- Financial feasibility verification
- ROI analysis support
- **L1/L2 Role**: Can serve as L1 author for financial documents, L2 reviewer for project ROI

### contents Creator Agent
- contents requirements provision
- contents creation schedule estimation
- Brand guideline compliance
- contents quality assurance
- **L1/L2 Role**: Can serve as L1 author for content documents, L2 reviewer for project content quality

## L1/L2 Role Definitions

### L1 Agent (Author) Responsibilities
- Document creation and initial development
- Basic quality assurance and self-review
- Submission for L2 review process
- **Meta Field**: Author field assignment

### L2 Agent (Reviewer) Responsibilities
- Senior-level work review and validation
- Technical excellence assessment
- Final approval and certification
- **Meta Field**: Reviewer field assignment

## Related Documents

### Templates
- `.ai/templates/prd_template.md` - Project strategy
- `.ai/templates/architecture_template.md` - Project design
- `.ai/templates/spec_template.md` - Requirements specification
- `.ai/templates/decision_template.md` - Project decision making

### Agents
- `.ai/agents/pm.agent.md` - PM agent
- `.ai/agents/developer.agent.md` - Development agent
- `.ai/agents/finance.agent.md` - Finance agent
- `.ai/agents/contents-creator.agent.md` - contents creation agent

### Skills
- `.ai/skills/pm/` - PM related skills
- `.ai/skills/developer/` - Development related skills
- `.ai/skills/finance/` - Finance related skills
- `.ai/skills/contents-creator/` - contents creation related skills

## Constraint Conditions

### Quality Standards
- All deliverables must comply with templates
- Project goal achievement measurement
- Stakeholder expectation management

### Schedule Management
- Project schedule compliance
- Milestone management
- Risk management

### Communication
- Regular stakeholder communication
- Progress transparency guarantee
- Problem solving rapid response

## Success Indicators

### Project Quality
- Goal achievement rate: 90% or higher
- Quality standard satisfaction rate: 95% or higher
- Stakeholder satisfaction: Target value or higher

### Execution Efficiency
- Schedule compliance rate: 85% or higher
- Budget compliance rate: 90% or higher
- Resource utilization rate: Target value or higher

### Performance Management
- ROI: Target value or higher
- Team productivity: Improvement
- Project success rate: Target value or higher
