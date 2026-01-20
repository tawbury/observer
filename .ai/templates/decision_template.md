# Decision Document Template

## Purpose
Template for documenting technical/business decision-making process and results

## Template Structure

```markdown
# Meta
- Project Name:
- File Name:
- Document ID:
- Status: Draft
- Created Date: {{CURRENT_DATE}}
- Last Updated: {{CURRENT_DATE}}
- Author: {{USER}}
- Reviewer: {{REVIEWER}}
- Parent Document:
- Related Reference:
- Version:

---

# [Decision Topic] Decision Record

**Decision Record**

---

## Decision Overview
### Decision Content
- Core decision item (summarize in one sentence)
- Scope and impact of decision
- Decision date and responsible party

### Decision Background
- Problem situation and necessity
- Timing when decision is needed
- Related stakeholders

## Alternative Analysis
### Considered Alternatives
- Alternative 1: Description and pros/cons
- Alternative 2: Description and pros/cons
- Alternative 3: Description and pros/cons

### Evaluation Criteria
- Technical feasibility
- Cost efficiency
- Market fit
- Implementation difficulty
- Long-term impact

## Decision Rationale
### Selected Alternative
- Final selected alternative
- Key reasons for selection
- Scores by evaluation criteria

### Rejected Alternatives
- Rejected alternatives and reasons
- Potential risk considerations

## Impact Analysis
### Positive Impact
- Expected effects and benefits
- Short-term impact
- Long-term impact

### Negative Impact
- Potential risks
- Mitigation measures
- Monitoring plan

## Execution Plan
### Implementation Phases
- Phase 1: Preparation and planning
- Phase 2: Execution and implementation
- Phase 3: Validation and stabilization

### Responsible Parties and Schedule
- Responsible parties and roles
- Major milestones
- Completion deadline

## Monitoring and Review
### Success Indicators
- Decision success measurement indicators
- Regular review cycle
- Performance evaluation methods

### Modification Plan
- Response plan when problems occur
- Decision modification procedures
- Rollback criteria
```

## Field Descriptions

### Meta Fields
- **Project Name**: Project name
- **File Name**: File name (auto-generated)
- **Document ID**: Document unique ID
- **Status**: Document status (Draft/Review/Approved)
- **Created Date**: Creation date
- **Last Updated**: Last update date
- **Author**: Author
- **Parent Document**: Parent document reference
- **Related Reference**: Related reference documents
- **Version**: Document version (1.0, 1.1, 2.0, etc.)

## Usage Rules
1. File name format: `decision_<topic>_<date>.md`
2. Storage location: `docs/dev/decision/`
3. Meta section and body separated by `---`
4. All required fields must not be empty

## Related Documents
- `.ai/templates/architecture_template.md` - Architecture template
- `.ai/templates/spec_template.md` - Specification template
- `.ai/.cursorrules` - System rules
