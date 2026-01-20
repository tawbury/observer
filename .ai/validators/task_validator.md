# Task Validator

## Purpose
Structural integrity and required element verification for Task documents

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
- Version

#### Verification Conditions
- All required fields must exist
- Field values must not be empty
- Meta section format must be correct
- Reviewer field is automatically filled during L2 verification

### 2. Contents Section Verification
#### Required Section List
- Department
- Role Name
- Expected Level
- Provided Criteria
- Notes

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty

### 3. Structure Verification
#### Structural Requirements
- Meta section exists (`# Meta` header)
- Contents separator exists (`---`)
- Appropriate section header format

#### Verification Order
1. Meta section completeness check
2. All required contents sections existence verification
3. Section header format verification (##)
4. Required field not empty verification

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- All structural requirements satisfied

### FAIL Conditions
- Required field/section missing
- Field value empty
- Structure format error

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
Structure Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **Last Updated field**: Required in validation but not in Task Template
- **Meta Isolation**: Evaluation results must not be affected by Meta section data
- **Structure Verification ONLY**: Content-based evaluation prohibited

## Related Documents
- `.ai/skills/hr/hr_onboarding.skill.md` - Validation logic implementation
- `.ai/templates/task_template.md` - Template definition
- `.ai/.cursorrules` - System rules
