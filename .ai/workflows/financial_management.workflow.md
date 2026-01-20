# Meta
- Workflow Name: Financial Management Workflow
- File Name: financial_management.workflow.md
- Document ID: WF-FINANCE-001
- Status: Active
- Created Date: 2026-01-16
- Last Updated: 2026-01-16
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# Financial Management Workflow

## Purpose
Workflow for systematic management of project financial management processes

## Workflow Overview
Entire financial management cycle management from financial planning through budget management and performance analysis

## Workflow Stages

### 1. Financial Planning
- **Responsible**: Finance Agent, PM Agent
- **Input**: Business objectives, project plans
- **Output**: Financial strategy document
- **Template**: `.ai/templates/prd_template.md`
- **Deliverable**: `docs/dev/PRD/prd_<financial>.md` (version information managed in Meta section)

### 2. Budget Establishment
- **Responsible**: Finance Agent
- **Input**: Financial strategy document, project requirements
- **Output**: Budget plan document
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/budget_architecture_<project>.md` (version information managed in Meta section)

### 3. Financial Specification
- **Responsible**: Finance Agent
- **Input**: Budget plan document, cost structure
- **Output**: Financial specification document
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/spec/financial_spec_<module>.md` (version information managed in Meta section)

### 4. Financial Decision Making
- **Responsible**: Finance Agent, PM Agent
- **Input**: Financial specification document, constraint conditions
- **Output**: Financial decision making record
- **Template**: `.ai/templates/decision_template.md`
- **Deliverable**: `docs/dev/decision/decision_<financial>_<date>.md`

### 5. Budget Execution
- **Responsible**: Finance Agent
- **Input**: Approved budget, execution plan
- **Output**: Budget execution record
- **Verification**: Budget compliance rate, cost efficiency

### 6. Financial Monitoring
- **Responsible**: Finance Agent
- **Input**: Budget execution data, performance indicators
- **Output**: Financial monitoring report
- **Verification**: Budget variance analysis, actual performance evaluation

### 7. Performance Analysis
- **Responsible**: Finance Agent
- **Input**: Financial data, performance indicators
- **Output**: Financial performance analysis report
- **Verification**: ROI analysis, efficiency evaluation

## Agent Roles

### Finance Agent
- Financial strategy establishment & budget management
- Cost efficiency analysis & optimization
- Financial risk assessment & management
- Performance analysis & reporting
- **L1 Role**: Primary author for financial documents
- **L2 Role**: Senior reviewer for financial accuracy and compliance

### PM Agent
- Business objectives provision
- Project priority setting
- Stakeholder communication
- Financial data-based decision making support
- **L1/L2 Role**: Can serve as L1 author for project documents, L2 reviewer for financial integration

### Developer Agent (Optional)
- Technical financial requirements provision
- Development cost estimation
- Technology investment efficiency analysis
- **L1/L2 Role**: Can serve as L1 author for technical financial documents, L2 reviewer for cost efficiency

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
- `.ai/templates/prd_template.md` - Financial strategy
- `.ai/templates/architecture_template.md` - Budget structure
- `.ai/templates/spec_template.md` - Financial specification
- `.ai/templates/decision_template.md` - Financial decision making

### Agents
- `.ai/agents/finance.agent.md` - Finance agent
- `.ai/agents/pm.agent.md` - PM agent
- `.ai/agents/developer.agent.md` - Development agent

### Skills
- `.ai/skills/finance/` - Finance related skills
- `.ai/skills/pm/` - PM related skills
- `.ai/skills/developer/` - Development related skills

## Constraint Conditions

### Financial Standards
- All financial decisions must be documented
- Budget overage requires approval process
- Financial data must be regularly verified

### Regulatory Compliance
- Internal control policy compliance
- Financial reporting standard satisfaction
- Audit traceability guarantee

### Security Requirements
- Financial information security compliance
- Access permission management
- Data encryption

## Success Indicators

### Financial Efficiency
- Budget compliance rate: 95% or higher
- Cost efficiency: Target value or higher
- Financial risk: Managed level or lower

### Decision Making Quality
- Financial decision making accuracy: 90% or higher
- Prediction accuracy: Target value or higher
- Decision making speed: Within target value

### Performance Management
- ROI: Target value or higher
- Cash flow: Favorable
- Financial health: Stable
