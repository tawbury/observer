[Updated: 2026-01-16]

# AI System Directory

## Purpose
Multi-agent AI system with specialized skills for organizational task management and contents creation.

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
- **Multi-Agent Architecture**: Specialized agents for different domains
- **Cross-Agent Integration**: Seamless collaboration between agents
- **Skill-Based System**: Modular skill components for each agent
- **L1/L2 Skill Differentiation**: Junior and senior level skill classification
- **Template Standardization**: Consistent document structures
- **Quality Validation**: Built-in validation frameworks
- **L2 Review System**: Senior-level verification and review capabilities
- **Performance Optimization**: Context usage optimization and monitoring

## Execution Flow
1. Task document input
2. Agent selection based on task type
3. Skill execution for task processing
4. Validation and quality assurance
5. L2 review (for senior-level tasks)
6. Report generation and output

## L1/L2 Skill System
- **L1 (Junior)**: Basic implementation, task execution, standard procedures
- **L2 (Senior)**: Strategic planning, architecture design, leadership, review capabilities
- **L2 Review Validators**: Specialized validation for senior-level work
- **Mentorship System**: Knowledge transfer from L2 to L1 agents

## Constraints
- Base document creation/modification prohibited ❌
- Task-external reasoning prohibited ❌
- Meta information interpretation prohibited ❌
- Maintain 100% technical functionality while using optimized English context
- Context usage monitoring for performance optimization
