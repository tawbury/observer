[Updated: 2026-01-21]

# AI System Directory

**Status**: Workflow System v2.0 (Stable)  
**Core Loop**: Roadmap → Task → Run Record → Roadmap update  
**Foundation**: Metadata-first linking | Session-resilient continuity

## Purpose
Multi-agent AI system with specialized skills for task management, contents creation, and continuous operational loop execution.

## Quick Start
- **Workflow index**: [[workflows/workflow_index.md]] (all workflows, operational loop guide)
- **Operational skills**: [[skills/_shared/operational_roadmap_management.skill.md]], [[skills/_shared/operational_run_record_creation.skill.md]]
- **Templates**: [[templates/README.md]]
- **Rules**: [.cursorrules](.cursorrules)

## Structure
### agents/
- `hr.agent.md` - HR Agent for organizational role assessment
  - Role: Role-based task classification and evaluation
  - Input: Task documents
  - Output: Report documents
  - Classification levels: Junior (L1), Senior (L2), PENDING

- `pm.agent.md` - Product Management Agent
  - Role: Product strategy, roadmap planning, stakeholder coordination
  - Transform market requirements into actionable plans

- `contents-creator.agent.md` - Contents Creation Agent
  - Role: Integrated contents creation (visual + text)
  - Transform concepts/requirements into brand-consistent contents

- `developer.agent.md` - Development Agent
  - Role: Software design/implementation/maintenance
  - Transform technical specifications into functional code

- `finance.agent.md` - Finance Agent
  - Role: Internal project financial management
  - Document-based financial analysis and budget efficiency

### skills/
#### contents-creator/ (24 skills)
**Visual Contents:**
- `visual_design_fundamentals.skill.md` - Core visual design principles
- `image_generation.skill.md` - Visual images/graphics creation
- `brand_identity_design.skill.md` - Brand identity development
- `3d_visualization.skill.md` - 3D visualization techniques
- `motion_graphics.skill.md` - Motion graphics creation

**Video Contents:**
- `video_editing.skill.md` - Video post-production editing
- `video_postproduction.skill.md` - Advanced video post-production
- `video_storyboarding.skill.md` - Video storyboarding
- `advanced_postproduction.skill.md` - Advanced post-production techniques

**Ebook & Publishing:**
- `ebook_writing.skill.md` - Digital publishing contents writing
- `ebook_editing.skill.md` - Ebook editing & proofreading
- `ebook_structuring.skill.md` - Ebook contents structuring
- `ebook_monetization.skill.md` - Ebook revenue model design
- `ebook_platform_strategy.skill.md` - Platform distribution strategy
- `ebook_marketing.skill.md` - Ebook marketing & promotion
- `ebook_market_analysis.skill.md` - Market research & analysis
- `ebook_audience_development.skill.md` - Reader community building

**Design & Interactive:**
- `ux_ui_design.skill.md` - User experience & interface design
- `interactive_design.skill.md` - Interactive design development
- `contents_integration.skill.md` - Cross-media contents integration
- `contents_optimization.skill.md` - Contents performance optimization
- `visual_contents_strategy.skill.md` - Visual contents strategy
- `contents_writing_fundamentals.skill.md` - Contents writing fundamentals
- `image_prompting.skill.md` - AI image prompting techniques

#### hr/ (25 skills)
- `hr_template_management.skill.md` - Document template standardization & management
- Additional HR-specific skills for role assessment and task management

#### developer/ (27 skills)
**Core Development:**
- `dev_backend.skill.md` - Server-side component development
- `dev_frontend.skill.md` - User interface implementation
- `dev_api_design.skill.md` - API design & structuring
- `dev_database_design.skill.md` - Database schema design
- `dev_testing.skill.md` - Software testing & quality assurance
- `dev_deployment.skill.md` - Application deployment & CI/CD

**Advanced Development:**
- `dev_system_architecture.skill.md` - System architecture design
- `dev_security.skill.md` - Security implementation & vulnerability assessment
- `dev_performance_optimization.skill.md` - Performance optimization
- `dev_microservices.skill.md` - Microservices architecture
- `dev_cloud_infrastructure.skill.md` - Cloud infrastructure management
- `dev_containerization.skill.md` - Container orchestration

**Specialized Skills:**
- `dev_code_review.skill.md` - Code review & quality assurance
- `dev_documentation.skill.md` - Technical documentation
- `dev_monitoring.skill.md` - System monitoring & observability
- Additional specialized development skills

#### finance/ (12 skills)
- `financial_analysis.skill.md` - Financial data analysis
- `budget_management.skill.md` - Budget planning & management
- `cost_optimization.skill.md` - Cost reduction strategies
- `financial_reporting.skill.md` - Financial report generation
- `financial_risk_assessment.skill.md` - Risk evaluation & management
- `strategic_financial_planning.skill.md` - Strategic financial planning
- `funding_management.skill.md` - Funding & investment management
- `investment_portfolio_management.skill.md` - Portfolio management
- `forecasting_modeling.skill.md` - Financial forecasting
- `financial_system_optimization.skill.md` - Financial system optimization
- `cash_flow_management.skill.md` - Cash flow management
- `compliance_management.skill.md` - Regulatory compliance

#### pm/ (0 items)
*PM skills are integrated within the pm.agent.md file*

### templates/
Document templates for various agent workflows and task types

### validators/
- `task_validator.md` - Task document validation
- `spec_validator.md` - Specification validation
- `report_validator.md` - Report validation
- `anchor_validator.md` - Anchor document validation
- `architecture_validator.md` - Architecture validation
- `prd_validator.md` - PRD validation
- `decision_validator.md` - Decision validation
- `l2_review_validator.md` - L2 review validation
- `mentorship_validator.md` - Mentorship validation
- `cross_agent_validator.md` - Cross-agent validation
- `senior_decision_validator.md` - Senior decision validation

### workflows/
- `hr_evaluation.workflow.md` - HR evaluation workflow
- `software_development.workflow.md` - Software development workflow
- `contents_creation.workflow.md` - Contents creation workflow
- `financial_management.workflow.md` - Financial management workflow
- `project_management.workflow.md` - Project management workflow
- `integrated_development.workflow.md` - Integrated development workflow
- `l2_review_workflow.md` - L2 review workflow

### Performance Optimization
- `skill_loading_optimizer.md` - Skill loading optimization system
- `context_monitor.md` - Context usage monitoring
- `performance_test.md` - Performance testing framework

## Key Features
- **Operational Loop**: Roadmap → Task → Run Record → Roadmap update for session-resilient continuity
- **Metadata-First Linking**: All relationships in meta section; [[Obsidian links]] only
- **Multi-Agent Architecture**: Developer, HR, PM, Finance, Contents-Creator agents
- **Shared Operational Skills**: [[operational_roadmap_management.skill.md]], [[operational_run_record_creation.skill.md]]
- **Skill-Based System**: Modular skills per agent; frameworks in _shared/
- **L1/L2 Differentiation**: Junior and senior skill levels
- **Core Templates**: Roadmap and Run Record as loop foundation
- **Quality Validation**: Built-in validators and base validator framework
- **L2 Review System**: Senior-level verification and review capabilities
- **Performance Optimization**: Context usage optimization and monitoring

## Operational Loop (v2.0 Core)
1. **Roadmap**: Phase/session structure with Task references; updated after each Run Record
2. **Task**: Executable unit linked to Roadmap; input for skill execution
3. **Skill Execution**: Agent processes Task using assigned skills
4. **Run Record**: Evidence document created after work; proposes Roadmap updates
5. **Roadmap Update**: Review Run Record, update Roadmap status, plan next session
6. Loop back to step 2 with new Task or continue phase

**Session Resilience**: If interrupted, next session reads Roadmap + Run Records to understand state and resume

## L1/L2 Skill System
- **L1 (Junior)**: Basic implementation, task execution, standard procedures
- **L2 (Senior)**: Strategic planning, architecture design, leadership, review capabilities
- **L2 Review Validators**: Specialized validation for senior-level work
- **Mentorship System**: Knowledge transfer from L2 to L1 agents

## Constraints (Enforced in .cursorrules)
- Metadata-first linking required; no wildcard Obsidian links (e.g., no [[task_*.md]])
- All internal references use [[filename.md]] syntax
- Base document creation/modification prohibited ❌
- Task-external reasoning prohibited ❌
- Maintain 100% technical functionality while using optimized English context
- Context usage monitoring for performance optimization
- See [.cursorrules](.cursorrules) for complete enforcement rules
