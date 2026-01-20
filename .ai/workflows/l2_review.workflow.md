# Meta
- Workflow Name: L2 Review Workflow
- File Name: l2_review.workflow.md
- Document ID: WF-L2REVIEW-001
- Status: Active
- Created Date: 2026-01-16
- Last Updated: 2026-01-16
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# L2 Review Workflow

## Purpose
Workflow for systematic management of L2 review and validation processes

## Workflow Overview
Entire L2 review cycle management from work submission through final validation and certification

## Workflow Stages

### 1. L2 Work Submission
- **Responsible**: L2 Agent
- **Input**: L2-level work submission
- **Output**: Work categorization and review requirements
- **Template**: `.ai/templates/task_template.md`
- **Deliverable**: `docs/dev/review/l2_submission_<agent>_<date>.md` (version information managed in Meta section)

### 2. Technical Review
- **Responsible**: Senior Technical Validator
- **Input**: Categorized L2 work
- **Output**: Technical review results
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/review/technical_review_<agent>_<date>.md` (version information managed in Meta section)

### 3. Business Impact Review
- **Responsible**: Business Validator
- **Input**: Technical review results
- **Output**: Business impact assessment
- **Template**: `.ai/templates/prd_template.md`
- **Deliverable**: `docs/dev/review/business_review_<agent>_<date>.md` (version information managed in Meta section)

### 4. Leadership Review
- **Responsible**: Leadership Validator
- **Input**: Business impact assessment
- **Output**: Leadership evaluation results
- **Template**: `.ai/templates/decision_template.md`
- **Deliverable**: `docs/dev/review/leadership_review_<agent>_<date>.md` (version information managed in Meta section)

### 5. Cross-Agent Integration
- **Responsible**: Integration Validator
- **Input**: Leadership evaluation results
- **Output**: Integration assessment results
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/review/integration_review_<agent>_<date>.md` (version information managed in Meta section)

### 6. Final Validation
- **Responsible**: Senior Validator
- **Input**: All review results
- **Output**: Final validation and certification
- **Template**: `.ai/templates/report_template.md`
- **Deliverable**: `docs/dev/review/final_validation_<agent>_<date>.md` (version information managed in Meta section)
- **Meta Update**: Reviewer field auto-populated with Senior Validator designation

## Agent Roles

### L1 Agent (Author)
- Document creation and initial development
- Basic quality assurance and self-review
- Submission for L2 review process
- **Meta Role**: Author field in document metadata

### L2 Agent (Reviewer)
- Senior-level work review and validation
- Technical excellence assessment
- Leadership and mentorship evaluation
- **Meta Role**: Reviewer field in document metadata
- Final approval and certification authority

### Senior Technical Validator
- Architecture and design assessment
- Technical innovation evaluation
- Code review leadership validation

### Business Validator
- Strategic value assessment
- Business goal alignment verification
- ROI and impact measurement

### Leadership Validator
- Decision-making authority assessment
- Cross-functional coordination evaluation
- Mentorship and guidance quality verification

### Integration Validator
- Inter-agent collaboration assessment
- Integration quality verification
- Shared standards compliance validation

### Senior Validator
- Comprehensive quality assessment
- L2 competency confirmation
- Final certification and approval

## Related Documents

### Templates
- `.ai/templates/task_template.md` - L2 work submission
- `.ai/templates/architecture_template.md` - Technical review
- `.ai/templates/prd_template.md` - Business impact review
- `.ai/templates/decision_template.md` - Leadership review
- `.ai/templates/spec_template.md` - Integration review
- `.ai/templates/report_template.md` - Final validation

### Agents
- `.ai/agents/developer.agent.md` - Development agent
- `.ai/agents/pm.agent.md` - PM agent
- `.ai/agents/finance.agent.md` - Finance agent
- `.ai/agents/contents-creator.agent.md` - contents creation agent

### Skills
- `.ai/skills/developer/` - Development related skills
- `.ai/skills/pm/` - PM related skills
- `.ai/skills/finance/` - Finance related skills
- `.ai/skills/contents-creator/` - contents creation related skills

## Constraint Conditions

### Review Standards
- All L2 work must undergo complete review process
- Review criteria must be consistently applied
- Validation results must be documented

### Quality Requirements
- Technical excellence threshold mandatory
- Business impact minimum requirements
- Leadership competency standards compliance

### Integration Standards
- Cross-agent collaboration quality assessment
- Shared standards compliance verification
- Integration effectiveness measurement

## Success Indicators

### Review Quality
- Technical review pass rate: 95% or higher
- Business impact validation rate: 90% or higher
- Leadership review approval rate: 85% or higher

### Integration Efficiency
- Cross-agent collaboration effectiveness: Target value or higher
- Integration quality compliance rate: 95% or higher
- Standards adherence rate: 100%

### Certification Performance
- L2 competency confirmation rate: 90% or higher
- Final validation success rate: 95% or higher
- Improvement recommendation implementation: 80% or higher

## Review Criteria by Agent

### Developer L2 Review
- Architecture design quality
- Technical innovation level
- Code review leadership
- System optimization impact

### PM L2 Review
- Strategic planning quality
- Market analysis depth
- Stakeholder coordination effectiveness
- Product vision clarity

### Finance L2 Review
- Strategic financial planning
- Risk management sophistication
- Investment analysis quality
- Business advisory impact

### contents-Creator L2 Review
- contents strategy innovation
- Brand guideline development
- Cross-media integration quality
- Revenue model effectiveness

## Integration Points
- Connect to l2_review_validator
- Link to mentorship_validator
- Integrate with cross_agent_validator
- Align with senior_decision_validator

## Quality Gates
- Technical excellence threshold
- Business impact minimum
- Leadership competency standard
- Integration quality requirement
