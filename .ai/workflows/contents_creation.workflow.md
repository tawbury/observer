# Meta
- Workflow Name: contents Creation Workflow
- File Name: contents_creation.workflow.md
- Document ID: WF-CONTENTS-001
- Status: Active
- Created Date: 2026-01-16
- Last Updated: 2026-01-16
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# contents Creation Workflow

## Purpose
Workflow for systematic management of contents creation processes

## Workflow Overview
Entire contents production lifecycle management from contents planning through creation and distribution

## Workflow Stages

### 1. contents Planning
- **Responsible**: PM Agent
- **Input**: Business objectives, market research results
- **Output**: contents strategy document
- **Template**: `.ai/templates/prd_template.md`
- **Deliverable**: `docs/dev/PRD/prd_<contents>.md` (version information managed in Meta section)

### 2. contents Design
- **Responsible**: contents Creator Agent
- **Input**: contents strategy document
- **Output**: contents design document
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/contents_design_<project>.md` (version information managed in Meta section)

### 3. Production Specification
- **Responsible**: contents Creator Agent
- **Input**: contents design document, brand guidelines
- **Output**: contents production specification
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/spec/contents_spec_<module>.md` (version information managed in Meta section)

### 4. Production Decision Making
- **Responsible**: contents Creator Agent, PM Agent
- **Input**: contents production specification, constraint conditions
- **Output**: Production direction decision record
- **Template**: `.ai/templates/decision_template.md`
- **Deliverable**: `docs/dev/decision/decision_<contents>_<date>.md`

### 5. contents Production
- **Responsible**: contents Creator Agent
- **Input**: contents production specification, brand guidelines
- **Output**: Visual contents, text contents
- **Verification**: Quality review, brand consistency check

### 6. Quality Verification
- **Responsible**: contents Creator Agent
- **Input**: Produced contents, quality standards
- **Output**: Verified contents, modification requests
- **Verification**: Brand guideline compliance, quality standard satisfaction

### 7. Final Deliverables
- **Responsible**: contents Creator Agent
- **Input**: Verified contents
- **Output**: Final contents assets
- **Verification**: Final quality review, distribution readiness

## Agent Roles

### PM Agent
- contents strategy establishment & goal setting
- Market research & competitive analysis
- Stakeholder communication & expectation management
- **L1/L2 Role**: Can serve as L1 author for strategy documents, L2 reviewer for content quality

### contents Creator Agent
- contents design & production
- Brand guideline compliance
- Visual/text contents quality assurance
- **L1 Role**: Primary author for content creation documents
- **L2 Role**: Senior reviewer for content standards and brand guidelines

### Finance Agent (Optional)
- contents production cost analysis
- ROI evaluation & budget management
- Revenue model optimization
- **L1/L2 Role**: Can serve as L1 author for financial documents, L2 reviewer for content ROI analysis

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
- `.ai/templates/prd_template.md` - contents strategy
- `.ai/templates/architecture_template.md` - contents design
- `.ai/templates/spec_template.md` - Production specification
- `.ai/templates/decision_template.md` - Decision making

### Agents
- `.ai/agents/pm.agent.md` - PM agent
- `.ai/agents/contents-creator.agent.md` - contents creation agent
- `.ai/agents/finance.agent.md` - Finance agent

### Skills
- `.ai/skills/pm/` - PM related skills
- `.ai/skills/contents-creator/` - contents creation related skills
- `.ai/skills/finance/` - Finance related skills

## Constraint Conditions

### Quality Standards
- All deliverables must comply with templates
- Brand guideline compliance: 100%
- contents quality standard satisfaction

### Brand Consistency
- Visual identity maintenance
- Tone & manner consistency
- Message uniformity

### Legal Requirements
- Copyright compliance
- Trademark review
- Privacy protection compliance

## Success Indicators

### contents Quality
- Brand guideline compliance rate: 100%
- Quality review pass rate: 95% or higher
- User satisfaction: Target value or higher

### Production Efficiency
- Production period compliance
- Budget compliance
- Reuse rate improvement

### Business Performance
- contents reach rate: Target value or higher
- Engagement rate: Target value or higher
- Conversion rate: Target value or higher
