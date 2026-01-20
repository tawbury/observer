# Structure Validator

## Purpose
Standardized document structure validation for all document types

## Validation Rules

### 1. Document Structure Verification
#### Required Elements
- Meta section with `# Meta` header
- Contents separator `---` after Meta section
- Proper header hierarchy (## for sections)
- Consistent section organization

#### Structure Requirements
- Meta section must be first section
- Contents separator must be exactly `---`
- Section headers must use `##` format
- No empty sections allowed

### 2. Header Format Validation
#### Header Hierarchy Rules
- Document title: `# Document Title`
- Section headers: `## Section Name`
- Subsection headers: `### Subsection Name`
- Consistent nesting levels

#### Header Content Validation
- Headers must not be empty
- Header naming consistency
- No duplicate section names
- Logical section ordering

### 3. Contents Separator Validation
#### Separator Requirements
- Must be exactly `---` (three hyphens)
- Must be placed after Meta section
- Must be on its own line
- No extra characters before/after

#### Separator Placement
- After Meta section completion
- Before first content section
- Proper spacing around separator
- Single separator per document

### 4. Section Organization Validation
#### Standard Section Order
1. Meta section
2. Contents separator
3. Main content sections
4. Appendices (if any)

#### Section Content Validation
- All sections must have content
- No empty sections allowed
- Content relevance to section title
- Consistent section depth

### 5. Format Consistency Validation
#### Language Compliance
- docs/ folder: Korean content
- .ai/ folder: English content
- No mixed languages within document
- Consistent language usage

#### Template Compliance
- Template structure adherence
- Required section completeness
- Optional section handling
- Custom section validation

### 6. Quality Assurance Validation
#### Readability Standards
- Proper section spacing
- Consistent formatting
- Clear section boundaries
- Logical content flow

#### Completeness Standards
- All required sections present
- No orphaned content
- Proper section closure
- Complete document structure

## Document Type Specific Validation

### Task Documents
- Department section required
- Role Name section required
- Expected Level section required
- Provided Criteria section required

### Report Documents
- Role section required
- Department section required
- Evaluation Result section required
- Decision Basis section required

### Technical Documents
- Overview section required
- Technical specifications section
- Implementation details section
- Quality criteria section

## Integration
- Connect to meta_validator.md for Meta section validation
- Support document-specific validators
- Enable automated structure checking
- Provide validation error reporting

## Usage
- Applied during document creation
- Used for template compliance
- Supports quality assurance
- Enables automated validation
