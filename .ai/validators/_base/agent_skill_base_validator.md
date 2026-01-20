# Agent Skill Base Validator

**Purpose**: Unified base validation framework for all agent-specific skill validators. Extracts common skill validation patterns.

---

## Inherited Validators

This base validator consolidates common validation rules from:
- `skill_validator.md` - General skill validation

Agent-specific skill validators (pm, developer, finance, hr, contents_creator) should reference this base instead of duplicating rules.

---

## Section 1: Universal Skill Structure Validation

### 1.1 Required Skill Blocks
| Block | Tag | Required |
|-------|-----|----------|
| Core Logic | `<!-- BLOCK:CORE_LOGIC -->` | Yes |
| Input/Output | `<!-- BLOCK:INPUT_OUTPUT -->` | Yes |
| Execution Logic | `<!-- BLOCK:EXECUTION_LOGIC -->` | Yes |
| Technical Requirements | `<!-- BLOCK:TECHNICAL_REQUIREMENTS -->` | Recommended |
| Constraints | `<!-- BLOCK:CONSTRAINTS -->` | Recommended |
| Related Skills | `<!-- BLOCK:RELATED_SKILLS -->` | Recommended |

### 1.2 Block Validation Rules
```python
def validate_skill_blocks(skill_file):
    """Validate skill block structure"""
    errors = []
    required_blocks = ['CORE_LOGIC', 'INPUT_OUTPUT', 'EXECUTION_LOGIC']
    recommended_blocks = ['TECHNICAL_REQUIREMENTS', 'CONSTRAINTS', 'RELATED_SKILLS']

    content = skill_file.read()

    # Required blocks check
    for block in required_blocks:
        start_tag = f"<!-- BLOCK:{block} -->"
        end_tag = "<!-- END_BLOCK -->"
        if start_tag not in content:
            errors.append(f"Missing required block: {block}")
        elif end_tag not in content[content.find(start_tag):]:
            errors.append(f"Missing END_BLOCK tag for: {block}")

    # Recommended blocks warning
    for block in recommended_blocks:
        if f"<!-- BLOCK:{block} -->" not in content:
            errors.append(f"[WARNING] Missing recommended block: {block}")

    return errors
```

### 1.3 Skill Naming Convention
| Pattern | Example | Agent |
|---------|---------|-------|
| dev_*.skill.md | dev_backend.skill.md | Developer |
| pm_*.skill.md | pm_planning.skill.md | PM |
| hr_*.skill.md | hr_onboarding.skill.md | HR |
| *_analytics.skill.md | audience_analytics.skill.md | Multiple |
| ebook_*.skill.md | ebook_writing.skill.md | Contents-Creator |

---

## Section 2: Universal Skill Content Validation

### 2.1 Core Logic Requirements
```python
def validate_core_logic(block_content):
    """Validate CORE_LOGIC block content"""
    errors = []
    required_elements = [
        'purpose',      # Clear skill purpose
        'logic',        # Core transformation logic
        'value'         # Value proposition
    ]

    for element in required_elements:
        if element not in block_content.lower():
            errors.append(f"Core logic should include: {element}")

    return errors
```

### 2.2 Input/Output Requirements
| Element | Required | Description |
|---------|----------|-------------|
| Input section | Yes | Clear input definitions |
| Output section | Yes | Clear output definitions |
| Data types | Yes | Specified for each field |
| Required flag | Yes | Mark required vs optional |

### 2.3 Execution Logic Requirements
| Element | Required | Description |
|---------|----------|-------------|
| L1 execution | Yes | Junior level steps |
| L2 execution | Yes | Senior level steps |
| Step sequence | Yes | Numbered or ordered steps |
| Quality criteria | Recommended | Success criteria |

---

## Section 3: Universal Level (L1/L2) Validation

### 3.1 Level Differentiation Standards
```markdown
### Junior Level (L1)
- Basic implementation tasks
- Standard procedures
- Supervised execution
- Limited decision scope

### Senior Level (L2)
- Strategic planning tasks
- Complex analysis
- Independent execution
- Leadership responsibilities
```

### 3.2 Level Validation Rules
```python
def validate_level_differentiation(skill_content):
    """Validate L1/L2 level differentiation"""
    errors = []

    l1_indicators = ['junior', 'l1', 'basic', 'standard']
    l2_indicators = ['senior', 'l2', 'advanced', 'strategic']

    has_l1 = any(ind in skill_content.lower() for ind in l1_indicators)
    has_l2 = any(ind in skill_content.lower() for ind in l2_indicators)

    if not has_l1:
        errors.append("Missing Junior/L1 level definition")
    if not has_l2:
        errors.append("Missing Senior/L2 level definition")

    return errors
```

### 3.3 Skill Count Requirements by Agent
| Agent | L1 Minimum | L2 Minimum |
|-------|------------|------------|
| Developer | 6 | 9 |
| PM | 5 | 11 |
| Finance | 5 | 6 |
| HR | 3 | 6 |
| Contents-Creator | 6 | 6 |

---

## Section 4: Universal Quality Metrics

### 4.1 Structure Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Block completeness | 100% | All required blocks present |
| Tag formatting | 100% | Correct tag syntax |
| Header hierarchy | 100% | Correct ## usage |

### 4.2 Content Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Core logic clarity | 95%+ | Purpose clearly stated |
| I/O completeness | 95%+ | All fields documented |
| L1/L2 differentiation | 100% | Clear level separation |

### 4.3 Integration Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Related skills | 90%+ | Cross-references present |
| Framework references | 80%+ | Shared framework usage |
| Agent alignment | 100% | Matches agent scope |

---

## Section 5: Agent-Specific Extension Points

### 5.1 Extension Pattern
Agent-specific validators should:
1. Reference this base validator
2. Define agent-specific skill matrix
3. Add domain-specific validation rules
4. Keep only unique validation logic

### 5.2 Extension Template
```markdown
# [Agent] Skill Validator

## Base Validation
This validator extends: `_base/agent_skill_base_validator.md`
Inherits: Block validation, Content validation, Level validation

## Agent-Specific Skill Matrix
[Only agent-specific skill list here]

## Agent-Specific Validation Rules
[Only agent-specific rules here]
```

### 5.3 Agent Validators Using This Base
| Validator | Agent | Unique Elements |
|-----------|-------|-----------------|
| pm_skill_validator.md | PM | PM skill matrix |
| developer_skill_validator.md | Developer | Tech skill matrix, dependencies |
| finance_skill_validator.md | Finance | Financial skill matrix |
| hr_skill_validator.md | HR | HR skill matrix |
| contents_creator_skill_validator.md | Contents-Creator | Creative skill matrix |

---

## Section 6: Validation Execution

### 6.1 Validation Order
1. File structure validation
2. Block existence validation
3. Block content validation
4. Level differentiation validation
5. Agent-specific validation (delegated)

### 6.2 Result Format
```yaml
skill_validation_result:
  skill_name: "dev_backend.skill.md"
  agent: "developer"
  status: PASS | FAIL
  structure_validation:
    status: PASS | FAIL
    errors: []
  content_validation:
    status: PASS | FAIL
    errors: []
  level_validation:
    status: PASS | FAIL
    errors: []
  agent_specific_validation:
    status: PASS | FAIL
    errors: []
```

### 6.3 Quality Standards
| Check | Threshold | Required |
|-------|-----------|----------|
| Structure compliance | 100% | Yes |
| Content completeness | 95%+ | Yes |
| Level differentiation | 100% | Yes |
| Integration quality | 90%+ | Yes |
