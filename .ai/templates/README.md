# Templates Directory

All document templates for Workflow System v2.0 (Stable).

**Status**: Updated for operational loop (Roadmap → Task → Run Record) as core pattern.

## Operational Loop Templates (Core)

These two templates are foundational for all workflows:

| Template | Purpose | Usage |
|----------|---------|-------|
| [[roadmap_template.md]] | Phase/session structure; Task and Run Record tracking; Roadmap status | Every workflow root level |
| [[run_record_template.md]] | Execution evidence; session closure; Roadmap update proposals | After any meaningful work within a session |

**Why core**: The operational loop requires these templates for session-resilient continuity. Interrupted sessions resume by reading current Roadmap state + latest Run Records.

## Domain Stage Templates

Used in the standard 4-stage workflow pattern:

| Template | Stage | Usage |
|----------|-------|-------|
| [[prd_template.md]] | 1. Planning | Product/domain requirements and strategy |
| [[architecture_template.md]] | 2. Design | System/domain architecture design |
| [[spec_template.md]] | 3. Specification | Technical specifications and interfaces |
| [[decision_template.md]] | 4. Decision | Decision records and rationale |

**Note**: These templates are for stage outputs; all stages must link to Roadmap and include Run Records.
## All Templates

| Template | File | Purpose | Domain |
|----------|------|---------|--------|
| Roadmap | [[roadmap_template.md]] | Phase/session and Task tracking | **Operational Loop** |
| Run Record | [[run_record_template.md]] | Execution evidence and Roadmap proposals | **Operational Loop** |
| Task | [[task_template.md]] | Executable unit (HR evaluation, sessions) | Operational |
| PRD | [[prd_template.md]] | Product/domain requirements | Stage 1: Planning |
| Architecture | [[architecture_template.md]] | System/domain design | Stage 2: Design |
| Specification | [[spec_template.md]] | Technical specifications, API | Stage 3: Specification |
| Decision | [[decision_template.md]] | Decision records and rationale | Stage 4: Decision |
| Anchor | [[anchor_template.md]] | Strategic foundation (business goals) | Strategic |
| Report | [[report_template.md]] | Evaluation and review results | Reporting |
| Workflow | [[workflow_template.md]] | Workflow definition structure | Workflow (English) |
| Risk Management | [[risk_management_template.md]] | Risk analysis and mitigation (Finance) | Finance |
| Trading Strategy | [[trading_strategy_template.md]] | Trading strategy specification | Finance/Dev |
| Backtesting Report | [[backtesting_report_template.md]] | Trading backtesting results | Finance/Dev |
| Data Pipeline Spec | [[data_pipeline_spec_template.md]] | Data pipeline specification | Development |

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
- **Workflows**: [[../workflows/workflow_index.md]] (all workflows and operational loop guide)
- **Operational skills**: [[../skills/_shared/operational_roadmap_management.skill.md]], [[../skills/_shared/operational_run_record_creation.skill.md]]
- **Validators**: [[../validators/README.md]] (template structure validation)
- **System rules**: [[../.cursorrules]]
- **Agent definitions**: [[../agents/]]

## Template Optimization
- **Context Efficiency**: Optimized for minimal context usage
- **Loading Performance**: Selective template loading based on agent requirements
- **Maintenance**: Regular template updates for consistency and improvement
