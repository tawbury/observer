# Validator Index - Complete Validator Reference

Central index mapping all validators with their dependencies and purposes.

---

## Quick Navigation

- [Base Validators](#base-validators)
- [Document Validators](#document-validators)
- [Skill Validators](#skill-validators)
- [Advanced Validators](#advanced-validators)

---

## Base Validators

**Location**: `.ai/validators/_base/`

| Validator | Purpose | Consolidates |
|-----------|---------|--------------|
| [document_base_validator.md](_base/document_base_validator.md) | Document meta & structure | meta_validator + structure_validator |
| [agent_skill_base_validator.md](_base/agent_skill_base_validator.md) | Skill structure & content | skill_validator patterns |

---

## Foundation Validators

**Location**: `.ai/validators/`

| Validator | Purpose | Used By |
|-----------|---------|---------|
| [meta_validator.md](meta_validator.md) | Meta section validation | All document validators |
| [structure_validator.md](structure_validator.md) | Document structure | All document validators |
| [skill_validator.md](skill_validator.md) | General skill validation | All skill validators |

---

## Document Validators

**Location**: `.ai/validators/`

All document validators extend `_base/document_base_validator.md`.

| Validator | Document Type | Unique Validation |
|-----------|---------------|-------------------|
| [task_validator.md](task_validator.md) | Task documents | Department, Role, Expected Level sections |
| [report_validator.md](report_validator.md) | Report documents | Evaluation Result, Decision Basis sections |
| [anchor_validator.md](anchor_validator.md) | Anchor documents | Strategic foundation, Vision sections |
| [architecture_validator.md](architecture_validator.md) | Architecture docs | Technical architecture, System design |
| [spec_validator.md](spec_validator.md) | Specification docs | Technical specifications, API definitions |
| [prd_validator.md](prd_validator.md) | PRD documents | Product requirements, User stories |
| [decision_validator.md](decision_validator.md) | Decision records | Decision rationale, Alternatives |

### Document Validator Dependency Map
```
document_base_validator.md
    ├── task_validator.md
    ├── report_validator.md
    ├── anchor_validator.md
    ├── architecture_validator.md
    ├── spec_validator.md
    ├── prd_validator.md
    └── decision_validator.md
```

---

## Skill Validators

**Location**: `.ai/validators/`

All agent skill validators extend `_base/agent_skill_base_validator.md`.

### General Skill Validators
| Validator | Purpose | Scope |
|-----------|---------|-------|
| [skill_validator.md](skill_validator.md) | General skill structure | All skills |
| [skill_loading_validator.md](skill_loading_validator.md) | Skill loading process | Runtime validation |
| [skill_execution_validator.md](skill_execution_validator.md) | Skill execution quality | Runtime validation |

### Agent-Specific Skill Validators
| Validator | Agent | Unique Validation |
|-----------|-------|-------------------|
| [pm_skill_validator.md](pm_skill_validator.md) | PM | PM skill matrix (11 skills) |
| [developer_skill_validator.md](developer_skill_validator.md) | Developer | Tech skills, dependencies (15+ skills) |
| [finance_skill_validator.md](finance_skill_validator.md) | Finance | Financial skills (11 skills) |
| [hr_skill_validator.md](hr_skill_validator.md) | HR | HR skills (10+ skills) |
| [contents_creator_skill_validator.md](contents_creator_skill_validator.md) | Contents-Creator | Creative skills (10 skills) |

### Skill Validator Dependency Map
```
agent_skill_base_validator.md
    ├── pm_skill_validator.md
    ├── developer_skill_validator.md
    ├── finance_skill_validator.md
    ├── hr_skill_validator.md
    └── contents_creator_skill_validator.md

skill_validator.md
    ├── skill_loading_validator.md
    └── skill_execution_validator.md
```

---

## Advanced Validators

**Location**: `.ai/validators/`

| Validator | Purpose | When Used |
|-----------|---------|-----------|
| [l2_review_validator.md](l2_review_validator.md) | Senior-level work validation | L2 review process |
| [senior_decision_validator.md](senior_decision_validator.md) | Senior decision quality | Strategic decisions |
| [mentorship_validator.md](mentorship_validator.md) | Mentorship quality | L2→L1 knowledge transfer |
| [cross_agent_validator.md](cross_agent_validator.md) | Inter-agent collaboration | Multi-agent workflows |

### Advanced Validator Dependencies
```
l2_review_validator.md ←── report_validator.md
senior_decision_validator.md ←── decision_validator.md
mentorship_validator.md ←── l2_review_validator.md
cross_agent_validator.md ←── all validators
```

---

## Validation Categories

### By Validation Target
| Category | Validators | Count |
|----------|------------|-------|
| Document structure | meta, structure, document_base | 3 |
| Document content | task, report, anchor, arch, spec, prd, decision | 7 |
| Skill structure | skill, agent_skill_base | 2 |
| Skill agent-specific | pm, developer, finance, hr, contents_creator | 5 |
| Skill lifecycle | loading, execution | 2 |
| Advanced/Cross-cutting | l2_review, senior_decision, mentorship, cross_agent | 4 |

### By Validation Stage
| Stage | Validators | When |
|-------|------------|------|
| Creation | meta, structure, skill | Document/skill creation |
| Review | l2_review, senior_decision | Review process |
| Execution | skill_loading, skill_execution | Runtime |
| Collaboration | cross_agent, mentorship | Multi-agent work |

---

## Quality Standards Summary

### Document Validation Standards
| Metric | Target |
|--------|--------|
| Meta completeness | 100% |
| Structure compliance | 100% |
| Content completeness | 95%+ |

### Skill Validation Standards
| Metric | Target |
|--------|--------|
| Block completeness | 100% |
| Content completeness | 95%+ |
| L1/L2 differentiation | 100% |
| Integration quality | 90%+ |

### Advanced Validation Standards
| Metric | Target |
|--------|--------|
| L2 review thoroughness | 95%+ |
| Cross-agent alignment | 90%+ |
| Decision quality | 95%+ |

---

## Migration Notes

### Consolidated Validators (v1.0)
The following patterns were consolidated into base validators:
- Meta validation logic → `document_base_validator.md`
- Structure validation logic → `document_base_validator.md`
- Skill block validation → `agent_skill_base_validator.md`
- L1/L2 level definitions → `agent_skill_base_validator.md`

### Recommended Updates
Existing validators should be updated to:
1. Add "Base Validation" section referencing base validator
2. Remove duplicate validation rules
3. Keep only document/agent-specific validation

---

## Version

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial index with base validators |
