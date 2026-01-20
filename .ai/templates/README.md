# Templates Directory

This directory contains all template documents used by the AI system for standardized document creation.

## Purpose
- Task template standardization
- Report template management
- Document format consistency maintenance
- Template usage guidelines and optimization

## Structure
```
templates/
├── task_template.md              # Standard task template
├── report_template.md            # Standard report template
├── anchor_template.md            # Anchor document template (strategic foundation)
├── architecture_template.md      # Architecture document template
├── spec_template.md              # Specification template (API included)
├── prd_template.md              # Product requirements template
├── decision_template.md          # Decision record template
├── workflow_template.md          # Workflow definition template
└── README.md                     # Templates guide
```

**Current Status**: All 9 template files are present and updated with:
- Standardized meta section structure
- Korean language compliance for docs/ folder
- Checkbox format for task criteria
- Template variables support ({{CURRENT_DATE}}, {{USER}})
- Contents separator (`---`) implementation
- Reviewer field for document review and approval workflow

## Template Types

### Task Template
- **Usage**: `docs/tasks/` directory
- **Purpose**: HR evaluation role definition documents
- **Features**: Required Meta fields and Contents sections with checkbox format
- **Language**: Korean (docs/ folder requirement)

### Report Template  
- **Usage**: `docs/reports/` directory
- **Purpose**: Evaluation result report format
- **Features**: Structured data output with feedback sections
- **Language**: Korean (docs/ folder requirement)

### Anchor Template
- **Usage**: `docs/dev/anchor/` directory
- **Purpose**: Strategic foundation documents for all initiatives
- **Features**: Business strategy and execution plans
- **Language**: Korean (docs/ folder requirement)

### Architecture Template
- **Usage**: `docs/dev/archi/` directory
- **Purpose**: System architecture documentation
- **Features**: Technical decisions and structure definition
- **Language**: Korean (docs/ folder requirement)

### Specification Template
- **Usage**: `docs/dev/spec/` directory
- **Purpose**: Technical specifications and API documentation
- **Features**: Detailed technical requirements and interface definitions
- **Language**: Korean (docs/ folder requirement)

### Workflow Template
- **Usage**: `.ai/workflows/` directory
- **Purpose**: Standard workflow definition template
- **Features**: 7-stage workflow structure with agent roles and success indicators
- **Language**: English (.ai/ folder requirement)

### PRD Template
- **Usage**: `docs/dev/PRD/` directory
- **Purpose**: Product requirements definition
- **Features**: Business objectives and market analysis
- **Language**: Korean (docs/ folder requirement)

### Decision Template
- **Usage**: `docs/dev/decision/` directory
- **Purpose**: Decision process documentation
- **Features**: Alternative analysis and decision rationale
- **Language**: Korean (docs/ folder requirement)

## Template Variables
All templates support standardized variables:
- **{{CURRENT_DATE}}**: Current date in YYYY-MM-DD HH:MM format
- **{{USER}}**: Current user name
- **{{REVIEWER}}**: Senior agent designation for L2 validation
- **Meta Section**: Standardized meta fields (Project Name, File Name, Document ID, Status, Created Date, Last Updated, Author, Reviewer, Parent Document, Version)
- **Contents Separator**: `---` separator between meta and contents sections

## Junior/Senior Role Guidelines

### Author Field (Junior Agent)
- **Purpose**: Document creator and primary author
- **Responsibility**: Initial development, basic quality assurance, self-review
- **Assignment**: Junior level agents create and author documents
- **Meta Field**: Author field populated by Junior agent

### Reviewer Field (Senior Agent)
- **Purpose**: Senior-level review and validation
- **Responsibility**: Technical excellence assessment, final approval, certification
- **Assignment**: Senior level agents review and validate documents
- **Meta Field**: Reviewer field populated by Senior agent

### Role Assignment Matrix
| Document Type | Junior Author | Senior Reviewer |
|---|---|---|
| Task Documents | HR Agent (Junior) | Senior Agent (Senior) |
| Technical Documents | Developer Agent (Junior) | Senior Developer (Senior) |
| Financial Documents | Finance Agent (Junior) | Senior Finance (Senior) |
| Content Documents | Content Creator (Junior) | Senior Creator (Senior) |
| Project Documents | PM Agent (Junior) | Senior PM (Senior) |

## Template Usage Guidelines

### Language Compliance
- **docs/ folder**: All templates output in Korean
- **.ai/ folder**: Template definitions in English
- **Mixed Language**: Prohibited within same document

### Structure Requirements
- **Meta Section**: Must include all required fields
- **Contents Sections**: Must use proper header format (##)
- **Separator**: Must use `---` between meta and contents

### Quality Assurance
- **Template Validation**: Use `.ai/validators/task_validator.md` for structure validation
- **Meta Integrity**: Ensure all required meta fields are present
- **Format Consistency**: Maintain standardized format across all templates

## Integration Points

### Workflow Integration
- **HR Evaluation Workflow**: Task Template → HR Agent → Report Template
- **Development Workflow**: Architecture/Spec/PRD/Decision Templates → Developer Agent
- **Validation System**: All templates integrate with `.ai/validators/` system

### Agent Integration
- **HR Agent**: Uses Task and Report templates
- **Developer Agent**: Uses Architecture, Spec, PRD, Decision templates
- **PM Agent**: Uses all development templates for coordination
- **Finance Agent**: Uses templates for financial documentation review
- **Contents-Creator Agent**: Uses templates for content strategy documentation

## Related Documents
- `.ai/.cursorrules` - Template definitions and usage rules
- `.ai/validators/task_validator.md` - Template structure validation
- `.ai/workflows/` - Template usage in workflows
- `docs/tasks/` - Task template usage examples
- `docs/reports/` - Report template usage examples

## Template Optimization
- **Context Efficiency**: Optimized for minimal context usage
- **Loading Performance**: Selective template loading based on agent requirements
- **Maintenance**: Regular template updates for consistency and improvement
