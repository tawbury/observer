# Workflows Directory

Workflow definitions and operational loop patterns for Workflow System v2.0 (Stable).

**Primary Resource**: See [[workflow_index.md]] for complete workflow reference, operational loop guide, and session resilience patterns.

## Purpose
All workflows implement the **operational loop**: Roadmap → Task → Run Record → Roadmap update
- **Session-resilient continuity**: Interruptions resolved via Roadmap + Run Record state
- **Metadata-first linking**: All relationships via [[Obsidian links]] in meta sections
- **Shared operational skills**: [[../skills/_shared/operational_roadmap_management.skill.md]], [[../skills/_shared/operational_run_record_creation.skill.md]]

Domain workflows:
- HR evaluation workflow
- Stock trading system development (integrated pattern)
- Contents creation workflow
- Financial management workflow
- Project management workflow
- Integrated development workflow
- L2 review and validation workflows

## Workflow Types

**See [[workflow_index.md]] for complete workflow definitions.**

Quick overview below:
- **File**: `hr_evaluation.workflow.md`
- **Purpose**: HR evaluation process automation
- **Primary Agent**: HR Agent
- **Key Stages**: Task creation → Structure validation → Level determination → Report generation

### Stock Trading System Development Workflow
- **File**: `stock_trading_system.workflow.md`
- **Purpose**: Stock trading system development and operation lifecycle management
- **Primary Agents**: PM Agent, Developer Agent, Finance Agent
- **Key Stages**: Trading strategy discovery → Financial planning & risk assessment → Data architecture design → Trading system architecture → Integrated specification → Decision making → Parallel implementation → Backtesting & validation → Deployment & monitoring → Live trading & analysis
- **Focus**: Trading strategy, data pipeline, automated trading, risk management, backtesting, performance analysis

### Contents Creation Workflow
- **File**: `contents_creation.workflow.md`
- **Purpose**: Contents creation process management
- **Primary Agents**: PM Agent, Contents Creator Agent
- **Key Stages**: Planning → Design → Creation → Validation → Final deliverables

### Financial Management Workflow
- **File**: `financial_management.workflow.md`
- **Purpose**: Financial management process definition
- **Primary Agents**: Finance Agent, PM Agent
- **Key Stages**: Planning → Budget establishment → Execution → Monitoring → Performance analysis

### Project Management Workflow
- **File**: `project_management.workflow.md`
- **Purpose**: Project management process definition
- **Primary Agents**: PM Agent, Related agents
- **Key Stages**: Planning → Design → Execution → Monitoring → Performance management

### Integrated Development Workflow
- **File**: `integrated_development.workflow.md`
- **Purpose**: Multi-agent collaboration process integration
- **Primary Agents**: All agents collaboration
- **Key Stages**: Business planning → Product definition → Parallel execution → Integration testing → Deployment

### L2 Review Workflow
- **File**: `l2_review_workflow.md`
- **Purpose**: Senior-level work validation and review process
- **Primary Agents**: All L2 agents, Validators
- **Key Stages**: L2 work submission → Technical review → Business impact review → Leadership review → Cross-agent integration → Final validation

## Structure
```
workflows/
├── README.md                              # Workflow guide
├── hr_evaluation.workflow.md              # HR evaluation workflow
├── stock_trading_system.workflow.md       # Stock trading system workflow
├── contents_creation.workflow.md          # Contents creation workflow
├── financial_management.workflow.md       # Financial management workflow
├── project_management.workflow.md         # Project management workflow
├── integrated_development.workflow.md     # Integrated development workflow
├── l2_review_workflow.md                  # Senior review workflow
└── backup/                                # Archived workflows
    └── software_development.workflow.md.backup_20260120
```

## Senior Review System

### Senior-Level Validation Process
1. **Senior Work Submission**: Senior agents submit work for review
2. **Technical Review**: Architecture, innovation, optimization assessment
3. **Business Impact Review**: Strategic value, risk management evaluation
4. **Leadership Review**: Decision-making authority, mentoring quality
5. **Cross-Agent Integration**: Collaboration quality, synergy assessment
6. **Final Validation**: Comprehensive quality assessment and certification

### Review Criteria by Agent Type
- **Developer Senior**: Architecture design, code review leadership, system optimization
- **PM Senior**: Strategic planning, market analysis, product vision
- **Finance Senior**: Strategic financial planning, risk management, investment analysis
- **Contents-Creator Senior**: Contents strategy innovation, brand guidelines, cross-media integration

### Quality Gates
- Technical excellence threshold
- Business impact minimum requirements
- Leadership competency standards
- Integration quality criteria

## Workflow Integration

### Agent Collaboration Matrix
| Workflow | HR | PM | Developer | Contents-Creator | Finance |
|---|---|---|---|---|---|
| HR Evaluation | Lead | - | - | - | - |
| Stock Trading System | - | Lead | Lead | - | Lead |
| Contents Creation | - | Lead | - | Lead | - |
| Financial Management | - | Lead | - | - | Lead |
| Project Management | - | Lead | Collaborate | Collaborate | Collaborate |
| Integrated Development | - | Lead | Lead | Lead | Lead |
| Senior Review | Collaborate | Collaborate | Lead | Lead | Collaborate |

### Validation Integration
- All workflows connect to appropriate validators
- Senior workflows use specialized Senior validators
- Quality assurance checkpoints at each stage
- Cross-agent validation for integrated workflows

## Related Documents
- **Single source of truth**: [[workflow_index.md]] for all workflows, operational loop, and agent role definitions
- **Base pattern**: [[_base/workflow_base.md]] for L1/L2 role definitions and standard 4-stage structure
- **Agent definitions**: [[../agents/]] directory
- **Operational skills**: [[../skills/_shared/operational_roadmap_management.skill.md]], [[../skills/_shared/operational_run_record_creation.skill.md]]
- **Templates**: [[../templates/]] directory (especially [[../templates/roadmap_template.md]], [[../templates/run_record_template.md]])
- **System rules**: [[../.cursorrules]]

## Junior/Senior Agent Roles

### Junior Agent (Author)
- **Primary Responsibility**: Document creation and initial development
- **Meta Field Assignment**: Author field
- **Quality Assurance**: Basic self-review and validation
- **Submission**: Prepared for Senior review process

### Senior Agent (Reviewer)
- **Primary Responsibility**: Senior-level review and validation
- **Meta Field Assignment**: Reviewer field
- **Quality Assurance**: Technical excellence assessment
- **Authority**: Final approval and certification

### Agent-Specific Junior/Senior Roles

#### HR Agent
- **Junior Role**: Task document creation and role definition
- **Senior Role**: Senior role evaluation and level determination

#### PM Agent
- **Junior Role**: Project and strategy document authoring
- **Senior Role**: Project quality and compliance review

#### Developer Agent
- **Junior Role**: Technical document and code authoring
- **Senior Role**: Architecture and code quality review

#### Finance Agent
- **Junior Role**: Financial document creation and analysis
- **Senior Role**: Financial accuracy and compliance review

#### Contents Creator Agent
- **Junior Role**: Content creation and design authoring
- **Senior Role**: Content standards and brand guideline review

## Workflow Creation Guidelines

### Template Usage
- Use `.ai/templates/workflow_template.md` for new workflow creation
- Follow standardized 7-stage structure
- Include meta section with proper Document ID format: WF-[CATEGORY]-[NUMBER]
- Maintain consistent agent role definitions

### Structure Requirements
- **Meta Section**: Standardized fields (Workflow Name, File Name, Document ID, Status, Created Date, Last Updated, Author, Reviewer, Parent Document, Related Reference, Version)
- **Purpose**: Clear workflow objective definition
- **Workflow Overview**: Comprehensive lifecycle description
- **Workflow Stages**: 7 standardized stages with Responsible, Input, Output, Template, Deliverable
- **Agent Roles**: Clear role definitions and responsibilities
- **Related Documents**: Proper template, agent, and skill references
- **Constraint Conditions**: Quality standards and requirements
- **Success Indicators**: Measurable performance metrics

## Performance Optimization
- Workflow execution monitoring
- Agent coordination optimization
- Cross-agent synergy tracking
- L2 review efficiency metrics
