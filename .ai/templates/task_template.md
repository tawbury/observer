# Task Template

## Purpose
Standard Task document template for HR evaluation

## Template Structure

```markdown
# Meta
- Project Name:
- File Name:
- Document ID:
- Status: Draft
- Created Date: {{CURRENT_DATE}}
- Last Updated: {{CURRENT_DATE}}
- Author: {{USER}}
- Reviewer: {{REVIEWER}}
- Parent Document:
- Version:

---

## Department
-
## Role Name
-
## Expected Level
-
## Provided Criteria
- [ ] (Define specific responsibilities and required skills here)
- [ ]
- [ ]
- [ ]
- [ ]
## Notes
-
```

## Field Descriptions

### Meta Fields
- **Project Name**: Project name
- **File Name**: File name (auto-generated)
- **Document ID**: Document unique ID
- **Status**: Document status (Draft/Active/Completed)
- **Created Date**: Creation date
- **Last Updated**: Last update date
- **Author**: Author
- **Reviewer**: Reviewer
- **Parent Document**: Parent document reference
- **Version**: Document version (1.0, 1.1, 2.0, etc.)

### Contents Section
- **Department**: Department affiliation (Dev/Contents/Finance/PM, etc.)
- **Role Name**: Role name
- **Expected Level**: Expected level (L1/L2)
- **Provided Criteria**: Specific responsibilities and required competencies
- **Notes**: Additional notes

## Usage Rules
1. File name format: `task_<role>_<dept>.md`
2. Storage location: `docs/tasks/`
3. Meta section and contents section separated by `---`
4. All required fields must not be empty

## Validation Requirements
- Required Meta fields: Project Name, File Name, Document ID, Status, Created Date, Last Updated, Author, Reviewer, Parent Document, Version
- Required contents sections: Department, Role Name, Expected Level, Provided Criteria, Notes
- Structural requirements: Meta section presence, contents separator presence, appropriate header format

## Related Documents
- `.ai/validators/task_validator.md` - Structure validation
- `.ai/skills/hr/hr_onboarding.skill.md` - Validation logic
- `.ai/.cursorrules` - System rules
