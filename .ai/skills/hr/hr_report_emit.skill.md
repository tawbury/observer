[Optimized: 2026-01-16]

# HR Report Emit Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Judgment results → structured Report output
- Document creation for other Agent consumption
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
- Task document information (role, department, meta)
- Level judgment results (L1/L2/PENDING)
- Decision basis information

### Output
- Structured Report document
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic
### Report Structure
#### Meta Section
- Project Name: [from task]
- File Name: report_<role>_<dept>_<date>.md
- Document ID: <Project>-REPORT-<number>
- Status: Active
- Created Date: YYYY-MM-DD HH:MM
- Author: HR Agent
- Reviewer: {{REVIEWER}}
- Parent Document: [[task_<role>_<dept>.md]]
- Related Reference: [blank]

#### contents Sections
- Role: [role name]
- Department: [department name]
- Evaluation Result: Status: L1|L2|PENDING
- Decision Basis:
  - Matched Criteria: [list]
  - Missing/Unclear Criteria: [list]
- Flags: Needs Review: true|false
- Feedback for Improvement:
  - Action Items: [user additional content when PENDING]
  - Recommended Keywords: [recommended competency keywords for job group]

### Generation Rules
1. File name: report_<role>_<dept>_<YYYYMMDD>.md
2. Meta section template strict compliance
3. Evaluation Result: status value only included
4. Decision Basis: matched/missing list separation
5. Needs Review = true IF PENDING OR unclear criteria
6. Needs Review = false IF clear L1/L2 decision
7. Reviewer field: Auto-populated with Senior HR Agent for L2 validation
8. {{REVIEWER}} variable: Replaced with "Senior HR Agent" for L2 reviews

### Output Format
```markdown
# HR Evaluation Report

## Meta
[meta section template]

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
```
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICAL_REQUIREMENTS -->
## Technical Requirements
- Template engine
- File creation capability
- Metadata processing
- Format verification
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints
- Structured data output only
- Natural language description prohibited
- Agent consumption format compliance
- Decisional structure maintenance
<!-- END_BLOCK -->
