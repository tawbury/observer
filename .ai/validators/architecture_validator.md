# Architecture Validator

## Purpose
Structural integrity and quality requirement verification for architecture documents

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

### 2. contents Section Verification
#### Required Section List
- Overview
- Architecture Principles
- System Structure
- Technology Stack
- Implementation Plan
- Decision Items

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty
- Architecture diagram or structure description included

### 3. Structure Verification
#### Structure Requirements
- Meta section contents must not be empty
- contents separator presence (`---`)
- Appropriate section header format
- Logical contents flow

#### Verification Sequence
1. Meta section completeness check
2. All required contents sections existence confirmation
3. Section header format verification (##)
4. Required fields not empty confirmation
5. Architecture structure description confirmation

### 4. Quality Verification
#### Architecture Quality Criteria
- Clear system boundary definition
- Scalability and maintainability consideration
- Technology selection basis presentation
- Component relationship specification
- Security and performance considerations included

#### Technical Completeness
- Major technology stack specification
- Data flow description
- Deployment architecture inclusion
- Monitoring strategy presentation

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- Structure requirements all satisfied
- Architecture quality criteria satisfied

### FAIL Conditions
- Required fields/sections missing
- Field values empty
- Structure format errors
- Architecture quality insufficient

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
Structure Issues: [issue1, issue2, ...] (if FAIL)
Quality Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **Version Field**: Architecture version information managed in Meta section Version field
- **Technical Completeness**: Technical completeness verification
- **Scalability**: Scalability considerations confirmation
- **Maintainability**: Maintainability evaluation

## Related Documents
- `.ai/templates/architecture_template.md` - Architecture template definition
- `.ai/workflows/software_development.workflow.md` - Software development workflow
- `.ai/.cursorrules` - System rules
