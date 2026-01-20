# Meta
- Workflow Name: Integrated Development Workflow
- File Name: integrated_development.workflow.md
- Document ID: WF-INTEGRATED-001
- Status: Active
- Created Date: 2026-01-16
- Last Updated: 2026-01-16
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# Integrated Development Workflow

## Purpose
Workflow for integrated management of multi-agent collaboration processes

## Workflow Overview
Integrated project management from product planning through development, contents creation, and financial management

## Workflow Stages

### 1. Business Planning
- **Lead**: PM Agent
- **Collaboration**: Finance Agent
- **Input**: Business objectives, market research
- **Output**: Business strategy document
- **Template**: `.ai/templates/prd_template.md`
- **Deliverable**: `docs/dev/PRD/business_strategy_<project>.md` (version information managed in Meta section)

### 2. Product Definition
- **Lead**: PM Agent
- **Collaboration**: contents Creator Agent
- **Input**: Business strategy document
- **Output**: Product requirements document
- **Template**: `.ai/templates/prd_template.md`
- **Deliverable**: `docs/dev/PRD/product_requirements_<project>.md` (version information managed in Meta section)

### 3. Technical Architecture
- **Lead**: Developer Agent
- **Collaboration**: PM Agent
- **Input**: Product requirements document
- **Output**: Technical architecture document
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/tech_architecture_<project>.md` (version information managed in Meta section)

### 4. contents Strategy
- **Lead**: contents Creator Agent
- **Collaboration**: PM Agent
- **Input**: Product requirements document
- **Output**: contents strategy document
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/contents_strategy_<project>.md` (version information managed in Meta section)

### 5. Feature Specification
- **Lead**: Developer Agent
- **Collaboration**: PM Agent, contents Creator Agent
- **Input**: Technical architecture, contents strategy
- **Output**: Integrated feature specification
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/spec/integrated_spec_<project>.md` (version information managed in Meta section)

### 6. Financial Planning
- **Lead**: Finance Agent
- **Collaboration**: PM Agent
- **Input**: Integrated feature specification
- **Output**: Financial execution plan
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/spec/financial_plan_<project>.md` (version information managed in Meta section)

### 7. Integrated Decision Making
- **Lead**: PM Agent
- **Collaboration**: All agents
- **Input**: All specifications, constraint conditions
- **Output**: Integrated decision making record
- **Template**: `.ai/templates/decision_template.md`
- **Deliverable**: `docs/dev/decision/integrated_decision_<project>_<date>.md`

### 8. Parallel Execution
#### Technical Development
- **Lead**: Developer Agent
- **Output**: Source code, technical documentation

#### contents Creation
- **Lead**: contents Creator Agent
- **Output**: contents assets, designs

#### Financial Management
- **Lead**: Finance Agent
- **Output**: Financial reports, budget management

#### Project Management
- **Lead**: PM Agent
- **Output**: Progress status, risk management

### 9. Integrated Testing
- **Lead**: Developer Agent
- **Collaboration**: contents Creator Agent, PM Agent
- **Input**: Developed features, created contents
- **Output**: Integrated test results
- **Verification**: System integration, user experience

### 10. Deployment and Launch
- **Lead**: PM Agent
- **Collaboration**: All agents
- **Input**: Integrated test results
- **Output**: Deployed product, operational plan
- **Verification**: Deployment success, operational stability

## Agent Roles

### PM Agent
- Overall project coordination and leadership
- Business planning and product definition
- Stakeholder management and communication
- **L1 Role**: Primary author for business and strategy documents
- **L2 Role**: Senior reviewer for integrated project quality

### Developer Agent
- Technical architecture and system design
- Feature specification and implementation
- Integration testing and deployment
- **L1 Role**: Primary author for technical documents
- **L2 Role**: Senior reviewer for technical excellence and integration

### contents Creator Agent
- Content strategy and design
- Brand guideline compliance
- Content creation and quality assurance
- **L1 Role**: Primary author for content documents
- **L2 Role**: Senior reviewer for content standards and brand consistency

### Finance Agent
- Financial planning and budget management
- ROI analysis and cost optimization
- Financial risk assessment
- **L1 Role**: Primary author for financial documents
- **L2 Role**: Senior reviewer for financial accuracy and compliance

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

## Agent Collaboration Matrix

| Stage | PM | Developer | contents Creator | Finance |
|---|---|---|---|---|
| Business Planning | Lead | Collaborate | - | Collaborate |
| Product Definition | Lead | Collaborate | Collaborate | - |
| Technical Architecture | Collaborate | Lead | - | - |
| contents Strategy | Collaborate | - | Lead | - |
| Feature Specification | Collaborate | Lead | Collaborate | - |
| Financial Planning | Collaborate | - | - | Lead |
| Integrated Decision Making | Lead | Collaborate | Collaborate | Collaborate |
| Parallel Execution | Lead | Lead | Lead | Lead |
| Integrated Testing | Collaborate | Lead | Collaborate | - |
| Deployment & Launch | Lead | Collaborate | Collaborate | Collaborate |

## Related Documents

### Templates
- `.ai/templates/prd_template.md` - Business/Product strategy
- `.ai/templates/architecture_template.md` - Architecture/Strategy
- `.ai/templates/spec_template.md` Specifications/Plans
- `.ai/templates/decision_template.md` - Decision making

### Agents
- `.ai/agents/pm.agent.md` - PM agent
- `.ai/agents/developer.agent.md` - Development agent
- `.ai/agents/contents-creator.agent.md` - contents creation agent
- `.ai/agents/finance.agent.md` - Finance agent

### Workflows
- `.ai/workflows/software_development.workflow.md` - Software development
- `.ai/workflows/contents_creation.workflow.md` - contents creation
- `.ai/workflows/financial_management.workflow.md` - Financial management
- `.ai/workflows/project_management.workflow.md` - Project management

## Constraint Conditions

### Collaboration Standards
- All agents must comply with templates
- Regular synchronization meetings required
- Clear role & responsibility definition

### Integration Requirements
- System interface standardization
- Data format uniformity
- Document management (version information managed in Meta section)

### Quality Assurance
- Stage-by-stage quality verification
- Integrated testing mandatory
- Rollback plan establishment

## Success Indicators

### Collaboration Efficiency
- Inter-agent communication efficiency: Target value or higher
- Parallel work efficiency: Target value or higher
- Decision making speed: Within target value

### Integration Quality
- System integration success rate: 95% or higher
- Final product quality: Target value or higher
- User satisfaction: Target value or higher

### Project Performance
- Schedule compliance rate: 85% or higher
- Budget compliance rate: 90% or higher
- ROI: Target value or higher
