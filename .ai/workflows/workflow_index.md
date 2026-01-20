# Workflow Index - Complete Workflow Reference

Central index mapping all workflows with their stages, agents, and dependencies.

---

## Quick Navigation

- [Base Workflows](#base-workflows)
- [Domain Workflows](#domain-workflows)
- [Specialized Workflows](#specialized-workflows)
- [Orchestration](#orchestration)

---

## Base Workflows

**Location**: `.ai/workflows/_base/`

| Base | Purpose | Consolidates |
|------|---------|--------------|
| [workflow_base.md](_base/workflow_base.md) | Standard pattern, L1/L2 definitions | L1/L2 roles, 4-stage pattern |

---

## Domain Workflows

All domain workflows extend `_base/workflow_base.md`.

### Stock Trading System Development
**File**: [stock_trading_system.workflow.md](stock_trading_system.workflow.md)
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

---

### Software Development (Archived)
**File**: [backup/software_development.workflow.md.backup_20260120](backup/software_development.workflow.md.backup_20260120)
**ID**: WF-SOFTWARE-001 (DEPRECATED)
**Status**: Replaced by stock_trading_system.workflow.md

*Note: This general-purpose software development workflow has been replaced with a trading-specific workflow. The original file has been archived in the backup directory.*

---

### Contents Creation
**File**: [contents_creation.workflow.md](contents_creation.workflow.md)
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

---

### Financial Management
**File**: [financial_management.workflow.md](financial_management.workflow.md)
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

---

### Project Management
**File**: [project_management.workflow.md](project_management.workflow.md)
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

---

### HR Evaluation
**File**: [hr_evaluation.workflow.md](hr_evaluation.workflow.md)
**ID**: WF-HR-001

| Stage | Responsible | Template |
|-------|-------------|----------|
| 1. Task Creation | HR | task_template |
| 2. Structure Validation | HR | - |
| 3. Level Judgment | HR | - |
| 4. Report Generation | HR | report_template |

**Primary Agent**: HR
**Scope**: Agent level assessment (L1/L2/PENDING)

---

## Specialized Workflows

### L2 Review Workflow
**File**: [l2_review.workflow.md](l2_review.workflow.md)
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

### Skill Consolidation Workflow
**File**: [skill_consolidation_workflow.md](skill_consolidation_workflow.md)

**Purpose**: Governs skill file consolidation and SSoT management
**Key Principles**:
- 1 step = 1 prompt (review/execution separation)
- Backup required before execution
- Non-destructive until deletion gate

---

## Orchestration

### Integrated Development Workflow
**File**: [integrated_development.workflow.md](integrated_development.workflow.md)
**ID**: WF-INTEGRATED-001

**Purpose**: Orchestrates multiple domain workflows in parallel

| Stage | PM | Developer | Contents-Creator | Finance |
|-------|----|-----------|--------------------|---------|
| 1. Business Planning | Lead | Support | Support | Lead (Financial) |
| 2. Product Definition | Lead | - | Lead (Contents) | Support |
| 3-6. Parallel Execution | Orchestrate | Technical Lead | Content Lead | Financial Lead |
| 7-8. Integration | Coordinate | Integrate | Integrate | Verify |
| 9-10. Deployment | Approve | Execute | Deliver | Audit |

---

## Workflow Dependencies

### Template Dependencies
```
All Workflows → Templates
├── prd_template.md (Stage 1: Planning)
├── architecture_template.md (Stage 2: Design)
├── spec_template.md (Stage 3: Specification)
├── decision_template.md (Stage 4: Decision)
├── task_template.md (HR, L2 Review)
└── report_template.md (HR, L2 Review final)
```

### Validator Dependencies
```
Domain Workflows → Validators
├── meta_validator.md (all documents)
├── structure_validator.md (all documents)
├── prd_validator.md (Stage 1 outputs)
├── architecture_validator.md (Stage 2 outputs)
├── spec_validator.md (Stage 3 outputs)
└── decision_validator.md (Stage 4 outputs)

L2 Review Workflow → Advanced Validators
├── l2_review_validator.md
├── senior_decision_validator.md
├── mentorship_validator.md
└── cross_agent_validator.md
```

### Orchestration Dependencies
```
integrated_development.workflow.md
├── orchestrates → software_development.workflow.md
├── orchestrates → contents_creation.workflow.md
├── orchestrates → financial_management.workflow.md
└── orchestrates → project_management.workflow.md

l2_review.workflow.md
└── validates → all domain workflow outputs
```

---

## Common Patterns

### Standard 4-Stage Pattern
| Stage | Name | Template | Output Type |
|-------|------|----------|-------------|
| 1 | [Domain] Planning | prd_template | Strategy |
| 2 | [Domain] Design | architecture_template | Design |
| 3 | [Domain] Specification | spec_template | Spec |
| 4 | [Domain] Decision | decision_template | Decision |

### L1/L2 Role Pattern (Inherited from base)
| Role | Responsibility | Meta Field |
|------|----------------|------------|
| L1 (Author) | Create, self-review, submit | Author |
| L2 (Reviewer) | Review, validate, certify | Reviewer |

---

## Success Metrics Summary

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
