# Decision Validator

## Purpose
Structural integrity and decision process logicality verification for decision documents

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

### 2. Contents Section Verification
#### Required Section List
- Decision Overview
- Alternative Analysis
- Decision Basis
- Impact Analysis
- Execution Plan
- Monitoring & Review

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty
- Decision contents clearly defined

### 3. Decision Overview Verification
#### Decision Contents Criteria
- Core decision items summarized in one sentence
- Decision scope and impact specification
- Decision date and responsible person specification

#### Decision Background Criteria
- Problem situation and necessity clearly explained
- Timing when decision is needed presented
- Related stakeholders identified

### 4. Alternative Analysis Verification
#### Alternative Consideration Criteria
- At least 2 alternatives presented
- Description included for each alternative
- Pros and cons analysis included
- Evaluation criteria applied

#### Evaluation Criteria Standards
- Technical feasibility assessment
- Cost efficiency analysis
- Market fit consideration
- Implementation difficulty assessment
- Long-term impact consideration

### 5. Decision Basis Verification
#### Selected Alternative Criteria
- Final selected alternative specified
- Key reasons for selection presented
- Scores by evaluation criteria included

#### Rejected Alternative Criteria
- Rejected alternatives and reasons specified
- Potential risk considerations included

### 6. Impact Analysis Verification
#### Positive Impact Criteria
- Expected effects and benefits specific
- Short-term impact specified
- Long-term impact presented

#### Negative Impact Criteria
- Potential risks identified
- Mitigation measures presented
- Monitoring plan included

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
5. Decision overview completeness verification
6. Alternative analysis logicality verification
7. Decision basis validity verification

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- Decision overview completeness met
- Alternative analysis logicality secured
- Decision basis validity secured
- Impact analysis completeness met

### FAIL Conditions
- Required field/section missing
- Field value empty
- Structure format error
- Decision content unclear
- Alternative analysis insufficient
- Decision basis weak
- Impact analysis absent

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
Decision Issues: [issue1, issue2, ...] (if FAIL)
Analysis Issues: [issue1, issue2, ...] (if FAIL)
Impact Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **Decision Logic**: Decision logicality verification important
- **Alternative Analysis**: Alternative analysis completeness
- **Risk Assessment**: Risk assessment thoroughness
- **Implementation Feasibility**: Implementation feasibility verification

## Related Documents
- `.ai/templates/decision_template.md` - Decision template definition
- `.ai/workflows/project_management.workflow.md` - Project management workflow
- `.ai/.cursorrules` - System rules
