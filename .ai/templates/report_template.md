# Report Template

## Purpose
Standard template for HR evaluation result reports

## Template Structure

```markdown
# HR Evaluation Report

## Meta
- Project Name: [from task]
- File Name: report_<role>_<dept>_<YYYYMMDD>.md
- Document ID: <Project>-REPORT-<number>
- Status: Draft
- Created Date: {{CURRENT_DATE}}
- Last Updated: {{CURRENT_DATE}}
- Author: {{USER}}
- Reviewer: {{REVIEWER}}
- Parent Document: [[task_<role>_<dept>.md]]
- Version: [[task_<role>_<dept>.md]]
- Related Reference: [blank]

---

## Role
- [role]

## Department
- [department]

## Evaluation Result
- Status : L1|L2|PENDING

## Decision Basis
### Matched Criteria
- [criteria1]
- [criteria2]

### Missing / Unclear Criteria
- [criteria1]
- [criteria2]

## Flags
- Needs Review : true|false

## Feedback for Improvement
### Action Items
- [user additional content when PENDING]

### Recommended Keywords
- [recommended competency keywords for job group]
```

## Field Descriptions

### Meta Fields
- **Project Name**: Project name from original Task document
- **File Name**: Report file name (auto-generated)
- **Document ID**: Document unique ID
- **Status**: Document status (Active)
- **Created Date**: Report creation date
- **Author**: HR Agent (fixed)
- **Reviewer**: Reviewer
- **Parent Document**: Original Task document reference
- **Version**: Original Task document version reference
- **Related Reference**: Related reference documents

### Contents Section
- **Role**: Evaluated role
- **Department**: Department affiliation
- **Evaluation Result**: Evaluation result status
- **Decision Basis**: Decision basis (matched/missing criteria)
- **Flags**: Review required status
- **Feedback for Improvement**: Improvement feedback

## Generation Rules
1. **File name**: `report_<role>_<dept>_<YYYYMMDD>.md`
2. **Meta section**: Strict template compliance
3. **Evaluation Result**: Include status value only
4. **Decision Basis**: Separate matched/missing lists
5. **Needs Review**: true if PENDING or unclear criteria
6. **Needs Review**: false if clear L1/L2 decision

## Constraints
- **Structured output**: Natural language description prohibited
- **Agent consumption**: Format consumable by other agents
- **Deterministic structure**: Always maintain same structure

## Related Documents
- `.ai/skills/hr/hr_report_emit.skill.md` - Report generation logic
- `.ai/workflows/hr_evaluation.workflow.md` - Workflow stage 4
- `.ai/.cursorrules` - System rules
