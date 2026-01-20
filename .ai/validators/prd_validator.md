# PRD Validator

## Purpose
Structural integrity and business validity verification for product requirement documents

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
- Product Overview
- Product Goals
- Functional Requirements
- Non-Functional Requirements
- Market & Competition
- Development Plan
- Success Measurement

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty
- Product vision and goals clearly defined

### 3. Business Validity Verification
#### Product Overview Criteria
- Clear product vision presentation
- Market problem definition
- Target user specification
- Differentiation description

#### Product Goals Criteria
- Business goals specificity
- User goals clarity
- Success measurement indicator definition
- Goal achievability

### 4. Requirements Completeness Verification
#### Functional Requirements Criteria
- Core features clearly defined
- MVP features identified
- Priority setting
- Feature dependency analysis

#### Non-Functional Requirements Criteria
- Performance requirements specificity
- Security requirements included
- User experience requirements
- Compatibility considerations

### 5. Market Analysis Verification
#### Market Research Criteria
- Market size and growth rate
- Target market segmentation
- Competitive analysis completeness
- Market entry strategy

#### Competitive Advantage Analysis
- Major competing products identified
- Differentiation strategy clarity
- Competitive advantage elements
- Market positioning

### 6. Structure Verification
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
5. Business validity verification
6. Requirements completeness verification

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- Business validity criteria met
- Requirements completeness criteria met
- Market analysis completeness met

### FAIL Conditions
- Required field/section missing
- Field value empty
- Structure format error
- Business validity insufficient
- Requirements incomplete
- Market analysis lacking

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
Business Issues: [issue1, issue2, ...] (if FAIL)
Requirements Issues: [issue1, issue2, ...] (if FAIL)
Market Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **Business Viability**: Business validity verification important
- **Market Analysis**: Market analysis completeness verification
- **Competitive Advantage**: Competitive advantage analysis
- **Success Metrics**: Success measurement indicator specificity

## Related Documents
- `.ai/templates/prd_template.md` - PRD template definition
- `.ai/workflows/project_management.workflow.md` - Project management workflow
- `.ai/.cursorrules` - System rules
