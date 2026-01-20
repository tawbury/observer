# Report Validator

## Purpose
Structural integrity and quality standard verification for report documents

## Validation Rules

### 1. Meta Field Verification
#### Required Field List
- Project Name
- File Name
- Document ID
- Status
- Created Date
- Last Updated
- Author
- Reviewer
- Parent Document
- Related Reference
- Version

#### Verification Conditions
- All required fields must exist
- Field values must not be empty
- Meta section format must be correct
- Version field must be standard format (1.0, 1.1, 2.0, etc.)
- Reviewer field must be populated for L2 validation reports
- Reviewer field must contain valid Senior agent designation

### 2. Contents Section Verification
#### Required Section List
- Role
- Department
- Evaluation Result
- Decision Basis
- Flags
- Feedback for Improvement

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty
- Evaluation result status clearly defined

### 3. Evaluation Result Verification
#### Evaluation Result Criteria
- Status value: One of L1, L2, PENDING
- Status value format correct
- Evaluation result clearly displayed

#### Status Value Verification
- L1: Junior level
- L2: Senior level
- PENDING: Additional information required

### 4. Decision Basis Verification
#### Decision Basis Criteria
- Matched Criteria section included
- Missing/Unclear Criteria section included
- Specific criteria matching presented

#### Criteria Matching Standards
- Matched criteria clearly presented
- Missing/unclear criteria identified
- Evaluation results by criteria included

### 5. Flags Verification
#### Flags Criteria
- Needs Review field included
- Value is one of true/false
- Review requirement clearly stated

#### Review Conditions
- If PENDING status, Needs Review is true
- If clear L1/L2 decision, Needs Review is false

### 6. Feedback Verification
#### Feedback for Improvement Criteria
- Action Items section included (when PENDING)
- Recommended Keywords section included
- Improvement feedback is specific

#### Feedback Content Standards
- Detailed improvement measures when PENDING status
- Recommended competency keywords for job group included
- Actionable action items presented

### 7. Structure Verification
#### Structural Requirements
- Meta section exists (`# Meta` header)
- Contents separator exists (`---`)
- Appropriate section header format
- Logical content flow

#### Verification Order
1. Meta section completeness check
2. All required contents sections existence verification
3. Section header format verification (##)
4. Required field not empty verification
5. Evaluation result status verification
6. Decision basis completeness verification
7. Flags logicality verification
8. Feedback appropriateness verification

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- Evaluation result status accurate
- Decision basis completeness met
- Flags logicality match
- Feedback content appropriateness

### FAIL Conditions
- Required field/section missing
- Field value empty
- Structure format error
- Evaluation result status error
- Decision basis incomplete
- Flags logicality mismatch
- Feedback content inappropriate

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
Evaluation Issues: [issue1, issue2, ...] (if FAIL)
Decision Issues: [issue1, issue2, ...] (if FAIL)
Flag Issues: [issue1, issue2, ...] (if FAIL)
Feedback Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **Evaluation Logic**: Evaluation logicality verification important
- **Status Consistency**: Status consistency verification
- **Feedback Quality**: Feedback quality verification
- **Agent Consumption**: Format for other agent consumption

## Related Documents
- `.ai/templates/report_template.md` - Report template definition
- `.ai/workflows/hr_evaluation.workflow.md` - HR evaluation workflow
- `.ai/.cursorrules` - System rules
