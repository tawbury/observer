# Base Workflows Framework

Unified base workflow templates that reduce duplication across workflows.

---

## Overview

This directory contains consolidated base workflow patterns that domain-specific workflows inherit from, eliminating duplicate stage definitions, L1/L2 role descriptions, and constraint categories.

## Available Base Workflows

| Base Workflow | Purpose | Used By |
|---------------|---------|---------|
| [workflow_base.md](workflow_base.md) | Standard 4-stage pattern, L1/L2 definitions | All domain workflows |

## Key Benefits

1. **L1/L2 Definitions**: Single source of truth (was duplicated in 8 workflows = ~120 lines)
2. **Standard 4-Stage Pattern**: Reusable stage template (was duplicated in 5 workflows = ~200 lines)
3. **Constraint Categories**: Standardized structure (reduces inconsistency)
4. **Success Indicators**: Unified metric categories

## Domain Workflow Mapping

### Workflows Using Base Pattern
| Workflow | Stages 1-4 | Stages 5-7 |
|----------|------------|------------|
| software_development.workflow.md | Standard | Dev-specific |
| contents_creation.workflow.md | Standard | Contents-specific |
| financial_management.workflow.md | Standard | Finance-specific |
| project_management.workflow.md | Standard | PM-specific |

### Specialized Workflows
| Workflow | Relationship |
|----------|--------------|
| hr_evaluation.workflow.md | Uses L1/L2 definitions, unique stages |
| l2_review.workflow.md | Uses L1/L2 definitions, review stages |
| integrated_development.workflow.md | Orchestrates other workflows |

## Usage Pattern

### In Domain Workflows
```markdown
<!-- At the top of domain workflow -->
## Base Workflow
This workflow extends: `_base/workflow_base.md`
Inherits: L1/L2 definitions, Standard stages 1-4, Constraint categories

## Domain-Specific Content
[Only domain-specific stages 5-7, constraints, and metrics here]
```

### Do NOT Duplicate
- L1/L2 Agent (Author/Reviewer) Responsibilities
- Standard 4-stage definitions (Planning, Design, Specification, Decision)
- Standard constraint category structure
- Standard success indicator categories

## Standard Pattern Summary

### Stage 1-4 Template Mapping
| Stage | Template | Output |
|-------|----------|--------|
| 1. Planning | prd_template.md | Strategy document |
| 2. Design | architecture_template.md | Design document |
| 3. Specification | spec_template.md | Spec document |
| 4. Decision | decision_template.md | Decision record |

### L1/L2 Quick Reference
| Role | Responsibilities | Meta Field |
|------|------------------|------------|
| L1 (Author) | Create, self-review, submit | Author |
| L2 (Reviewer) | Review, validate, certify | Reviewer |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial base workflow consolidation |
