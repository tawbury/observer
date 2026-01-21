# Validators Directory

Validation framework for document structure, template compliance, and quality assurance.

**Status**: Aligned to Workflow System v2.0 (Stable)  
**Focus**: Metadata-first validation | Operational loop compliance | Template structure

## Purpose
- Document structure validation (meta, contents, formats)
- Operational loop artifact validation (Roadmap, Task, Run Record)
- Template compliance checking
- L2 senior-level work validation
- Cross-agent collaboration validation

## Structure
```
validators/
├── README.md                    # Validator guide
├── meta_validator.md            # Meta section validator
├── structure_validator.md       # Structure validator
├── skill_validator.md            # General skill validator
├── skill_loading_validator.md     # Skill loading validator
├── skill_execution_validator.md    # Skill execution validator
├── task_validator.md            # Task validator
├── anchor_validator.md          # Anchor document validator
├── architecture_validator.md    # Architecture validator
├── spec_validator.md            # Specification validator
├── prd_validator.md             # PRD validator
├── decision_validator.md        # Decision validator
├── report_validator.md          # Report validator
├── l2_review_validator.md       # L2 review validator
├── mentorship_validator.md      # Mentorship validator
├── cross_agent_validator.md     # Cross-agent validator
├── senior_decision_validator.md  # Senior decision validator
├── pm_skill_validator.md         # PM agent skill validator
├── developer_skill_validator.md   # Developer agent skill validator
├── finance_skill_validator.md    # Finance agent skill validator
├── hr_skill_validator.md         # HR agent skill validator
├── contents_creator_skill_validator.md # Contents Creator agent skill validator
└── senior_decision_validator.md  # Senior decision validator
```

## Validation Functions

### Task Validator
- **File**: `task_validator.md`
- **Purpose**: Task document structure validation
- **Key Validation**: Meta fields, contents section, structural integrity

### Anchor Validator
- **File**: `anchor_validator.md`
- **Purpose**: Anchor document strategic validity validation
- **Key Validation**: Strategic depth, execution plan, success criteria

### Architecture Validator
- **File**: `architecture_validator.md`
- **Purpose**: Architecture document quality validation
- **Key Validation**: Architecture structure, technical completeness, scalability

### Spec Validator
- **File**: `spec_validator.md`
- **Purpose**: Specification technical completeness validation
- **Key Validation**: API interfaces, data models, technical specifications

### PRD Validator
- **File**: `prd_validator.md`
- **Purpose**: PRD business validity validation
- **Key Validation**: Product overview, market analysis, requirements completeness

### Decision Validator
- **File**: `decision_validator.md`
- **Purpose**: Decision logic validation
- **Key Validation**: Alternative analysis, decision rationale, impact analysis

### Report Validator
- **File**: `report_validator.md`
- **Purpose**: Report evaluation results validation
- **Key Validation**: Evaluation results, decision rationale, feedback quality

### L2 Review Validator
- **File**: `l2_review_validator.md`
- **Purpose**: Senior-level work validation and competency assessment
- **Key Validation**: Technical excellence, leadership, business impact

### Mentorship Validator
- **File**: `mentorship_validator.md`
- **Purpose**: Mentorship quality and knowledge transfer effectiveness validation
- **Key Validation**: Knowledge transfer, learning progress, L2 readiness

### Cross-Agent Validator
- **File**: `cross_agent_validator.md`
- **Purpose**: Inter-agent collaboration and integration quality validation
- **Key Validation**: Collaboration quality, integration consistency, synergy effectiveness

### Senior Decision Validator
- **File**: `senior_decision_validator.md`
- **Purpose**: Senior-level decision quality and strategic validity validation
- **Key Validation**: Strategic alignment, decision quality, leadership competency

### Meta Validator
- **File**: `meta_validator.md`
- **Purpose**: Standardized meta section format validation
- **Key Validation**: Required fields, format consistency, L1/L2 role validation

### Structure Validator
- **File**: `structure_validator.md`
- **Purpose**: Standardized document structure validation
- **Key Validation**: Header format, contents separator, section organization

### Skill Validator
- **File**: `skill_validator.md`
- **Purpose**: General skill structure and quality validation
- **Key Validation**: Skill structure, content quality, integration standards

### Skill Loading Validator
- **File**: `skill_loading_validator.md`
- **Purpose**: Skill loading process validation and optimization
- **Key Validation**: Loading performance, dependency management, resource optimization

### Skill Execution Validator
- **File**: `skill_execution_validator.md`
- **Purpose**: Skill execution quality validation and performance measurement
- **Key Validation**: Execution accuracy, output quality, performance metrics

## Agent-Specific Skill Validation

### PM Agent Skill Validator
- **File**: `pm_skill_validator.md`
- **Purpose**: PM agent skill validation and quality assurance
- **Key Validation**: PM methodology, stakeholder management, strategic planning

### Developer Agent Skill Validator
- **File**: `developer_skill_validator.md`
- **Purpose**: Developer agent skill validation and quality assurance
- **Key Validation**: Technical accuracy, code quality, architecture design

### Finance Agent Skill Validator
- **File**: `finance_skill_validator.md`
- **Purpose**: Finance agent skill validation and quality assurance
- **Key Validation**: Financial accuracy, risk assessment, business intelligence

### HR Agent Skill Validator
- **File**: `hr_skill_validator.md`
- **Purpose**: HR agent skill validation and quality assurance
- **Key Validation**: Evaluation accuracy, data privacy, talent assessment

### Contents Creator Agent Skill Validator
- **File**: `contents_creator_skill_validator.md`
- **Purpose**: Contents Creator agent skill validation and quality assurance
- **Key Validation**: Creative quality, brand compliance, audience engagement

## L2 Validation System

### Senior-Level Validation
- **Technical Excellence**: Architecture design, innovation, optimization
- **Leadership Assessment**: Decision-making authority, mentoring, coordination
- **Business Impact**: Strategic value creation, risk management
- **Quality Assurance**: Senior-level work standards compliance

### Mentorship Validation
- **Knowledge Transfer**: Technical skill development tracking
- **Learning Progress**: Skill gap identification, development plan execution
- **L2 Readiness**: Independent work capability, complex problem handling

### Cross-Agent Validation
- **Collaboration Quality**: Inter-agent communication effectiveness
- **Integration Consistency**: Shared standards compliance, interface compatibility
- **Synergy Assessment**: Combined value creation, resource optimization

## Related Documents
- **Workflows**: [[../workflows/workflow_index.md]]
- **Operational skills**: [[../skills/_shared/operational_roadmap_management.skill.md]], [[../skills/_shared/operational_run_record_creation.skill.md]]
- **Templates**: [[../templates/README.md]]
- **Agents**: [[../agents/]]
- **Base validators**: [[_base/README.md]]

## Integration Points
- **HR Agent**: Level assessment and validation
- **All Agents**: L2 competency verification
- **Workflow System**: Validation checkpoints
- **Quality Assurance**: Consistent standards enforcement
