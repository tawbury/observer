# Specification Validator

## Purpose
Structural integrity and technical completeness verification for specification documents

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
- Overview
- Requirements
- Design
- API Interfaces
- Implementation
- Verification

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty
- API interfaces section included (for integration specifications)

### 3. API Interface Verification (Required)
#### API Structure Requirements
- API overview and purpose specification
- Endpoint definition (methods, paths)
- Request/response data models
- Error handling definition
- Authentication method specification

#### Verification Conditions
- At least one endpoint defined
- Each endpoint includes description, parameters, response
- Data models presented in JSON format
- Error codes and handling methods specified

### 4. Structure Verification
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
5. API interface structure verification

### 5. Technical Completeness Verification
#### Technical Specification Criteria
- Clear interface definition
- Data format standardization
- Error handling completeness
- Security considerations included
- Performance requirements specified

#### Implementation Feasibility
- Technical feasibility verification
- Implementation complexity assessment
- Dependency analysis
- Testability verification

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- API interface structure complete
- Technical completeness criteria met

### FAIL Conditions
- Required field/section missing
- Field value empty
- Structure format error
- API interface incomplete
- Technical completeness insufficient

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
API Issues: [issue1, issue2, ...] (if FAIL)
Technical Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **API Integration**: API completeness important for integration specifications
- **Data Models**: Data model standardization verification
- **Error Handling**: Error handling completeness verification
- **Security**: Security requirement fulfillment verification

## Related Documents
- `.ai/templates/spec_template.md` - Specification template definition
- `.ai/workflows/software_development.workflow.md` - Software development workflow
- `.ai/.cursorrules` - System rules
