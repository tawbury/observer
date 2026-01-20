# Base Validators Framework

Unified base validation frameworks that reduce duplication across validators.

---

## Overview

This directory contains consolidated base validators that specific validators inherit from, eliminating duplicate validation logic.

## Available Base Validators

| Base Validator | Purpose | Used By |
|----------------|---------|---------|
| [document_base_validator.md](document_base_validator.md) | Document meta & structure validation | All document validators |
| [agent_skill_base_validator.md](agent_skill_base_validator.md) | Skill structure & content validation | All agent skill validators |

## Inheritance Structure

```
_base/
├── document_base_validator.md
│   ├── Consolidates: meta_validator.md + structure_validator.md
│   └── Used by: task, anchor, architecture, spec, prd, decision, report validators
│
└── agent_skill_base_validator.md
    ├── Consolidates: skill_validator.md common patterns
    └── Used by: pm, developer, finance, hr, contents_creator skill validators
```

## Benefits

1. **Context Reduction**: ~60% reduction in duplicate validation rules
2. **Consistency**: Single source of truth for common validation patterns
3. **Maintenance**: Update once, benefit all validators
4. **Quality**: Unified validation standards

## Usage Pattern

### Document Validators
```markdown
<!-- In document-specific validator (e.g., task_validator.md) -->

## Base Validation
This validator extends: `_base/document_base_validator.md`
Inherits: Meta validation, Structure validation

## Document-Specific Validation
### Task Document Required Sections
- Department section required
- Role Name section required
- Expected Level section required
[Only document-specific rules here]
```

### Skill Validators
```markdown
<!-- In agent skill validator (e.g., pm_skill_validator.md) -->

## Base Validation
This validator extends: `_base/agent_skill_base_validator.md`
Inherits: Block validation, Content validation, Level validation

## PM-Specific Skill Matrix
| Skill | Required | Level |
|-------|----------|-------|
| pm_planning | Yes | L1+ |
[Only agent-specific skill matrix here]
```

## Validation Hierarchy

```
Level 1: Base Validators (_base/)
    ↓ inherit
Level 2: Type Validators (meta_validator, structure_validator, skill_validator)
    ↓ inherit
Level 3: Specific Validators (task_validator, pm_skill_validator, etc.)
```

## Standards Enforced

### Document Standards
- Meta field completeness: 100%
- Structure compliance: 100%
- Date format: YYYY-MM-DD HH:MM
- Version format: X.Y.Z

### Skill Standards
- Block completeness: 100%
- L1/L2 differentiation: Required
- Related skills: Recommended
- Framework references: Recommended

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial consolidation |
