[Optimized: 2026-01-16]

# HR Onboarding Init Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Task document structure verification
- Required item missing confirmation
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
- Task document path or contents

### Output
- Validation Result (PASS/FAIL)
- Missing Fields List (if any)
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic
### Validation Rules
#### Required Meta Fields
- Project Name, File Name, Document ID, Status
- Created Date, Last Updated, Author, Parent Document

#### Required contents Sections
- Department, Role Name, Expected Level
- Provided Criteria, Notes

#### Structural Requirements
- Meta section presence & correct format
- contents separator (`---`) presence
- All required sections with appropriate headers

### Validation Logic
1. Meta section completeness check
2. All required contents sections presence confirmation
3. Section header format verification (##)
4. Required fields not empty confirmation
5. Return PASS if all checks pass
6. Return FAIL + missing fields list if any check fails
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Document structure parsing capability
- Field validity checking
- Format verification algorithms
- Result formatting
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints
- Judgment execution prohibited
- contents-based evaluation prohibited
- Structure verification ONLY
- No side effects
<!-- END_BLOCK -->
