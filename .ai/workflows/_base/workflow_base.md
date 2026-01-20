# Workflow Base Template

**Purpose**: Unified base workflow pattern that all domain workflows inherit from. Eliminates duplicate stage definitions and L1/L2 role descriptions.

---

## Standard Workflow Structure

All domain workflows follow this parameterized structure:

```
# Meta
- Workflow Name: [Domain] Workflow
- File Name: [domain]_[function].workflow.md
- Document ID: WF-[DOMAIN]-001
- Status: Active
- Created Date: [YYYY-MM-DD]
- Last Updated: [YYYY-MM-DD]
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: .ai/templates/anchor_template.md
- Version: 1.0.0

---

# [Domain] Workflow

## Purpose
[Domain-specific purpose]

## Workflow Overview
[Domain-specific overview]

## Workflow Stages
[4-7 stages following standard pattern]

## Agent Roles
[Domain-specific agent assignments]

## L1/L2 Role Definitions
[Inherited from this base - DO NOT DUPLICATE]

## Related Documents
[Domain-specific references]

## Constraint Conditions
[Domain-specific constraints]

## Success Indicators
[Domain-specific metrics]
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
| Template | `.ai/templates/prd_template.md` |
| Deliverable | `docs/dev/PRD/prd_<domain>.md` |

### Stage 2: Design/Architecture
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Design |
| Responsible | Domain Agent |
| Input | Strategy document |
| Output | Design document |
| Template | `.ai/templates/architecture_template.md` |
| Deliverable | `docs/dev/archi/<domain>_design_<project>.md` |

### Stage 3: Specification
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Specification |
| Responsible | Domain Agent |
| Input | Design document, requirements |
| Output | Specification document |
| Template | `.ai/templates/spec_template.md` |
| Deliverable | `docs/dev/spec/<domain>_spec_<module>.md` |

### Stage 4: Decision Making
| Element | Value |
|---------|-------|
| Stage Name | [Domain] Decision Making |
| Responsible | Domain Agent + PM Agent |
| Input | Specification, constraints |
| Output | Decision record |
| Template | `.ai/templates/decision_template.md` |
| Deliverable | `docs/dev/decision/decision_<domain>_<date>.md` |

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
- `.ai/templates/prd_template.md` - Stage 1 (Planning)
- `.ai/templates/architecture_template.md` - Stage 2 (Design)
- `.ai/templates/spec_template.md` - Stage 3 (Specification)
- `.ai/templates/decision_template.md` - Stage 4 (Decision)

### Validator References
- `meta_validator.md` - All document meta validation
- `structure_validator.md` - All document structure validation
- Domain-specific validators as needed

### L2 Review Integration
All workflows connect to:
- `l2_review.workflow.md` - For L2 work validation
- `l2_review_validator.md` - For L2 quality assessment

---

## Usage Instructions

### For Domain Workflow Authors

1. **Reference this base**:
```markdown
## Base Workflow
This workflow extends: `_base/workflow_base.md`
Inherits: L1/L2 definitions, Standard stages 1-4, Constraint categories
```

2. **Define only domain-specific elements**:
- Domain-specific stages 5-7
- Domain-specific agent role details
- Domain-specific success indicators

3. **Do NOT duplicate**:
- L1/L2 role definitions (reference this base)
- Standard 4-stage pattern (customize names only)
- Standard constraint categories (add domain-specific)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial base workflow creation |
