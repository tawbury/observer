# Skill Index - Complete Skill Reference

Central index mapping all skills across agents with framework references.

---

## Quick Navigation

- [Developer Skills](#developer-skills)
- [PM Skills](#pm-skills)
- [HR Skills](#hr-skills)
- [Contents-Creator Skills](#contents-creator-skills)
- [Finance Skills](#finance-skills)
- [Shared Frameworks](#shared-frameworks)

---

## Developer Skills

**Location**: `.ai/skills/developer/`

### L1 (Junior) Core Skills
| Skill | File | Purpose |
|-------|------|---------|
| Backend Development | dev_backend.skill.md | Server-side implementation |
| Frontend Development | dev_frontend.skill.md | Client-side implementation |
| Testing | dev_testing.skill.md | Unit/integration testing |
| Documentation | dev_documentation.skill.md | Technical documentation |
| Code Review | dev_code_review.skill.md | Peer review participation |

### L2 (Senior) Core Skills
| Skill | File | Framework Reference |
|-------|------|---------------------|
| API Design | dev_api_design.skill.md | - |
| System Architecture | dev_system_architecture.skill.md | - |
| Security | dev_security.skill.md | - |
| Performance Optimization | dev_performance_optimization.skill.md | optimization_framework (PERFORMANCE) |
| Database Design | dev_database_design.skill.md | - |
| Deployment | dev_deployment.skill.md | - |

### Advanced Skills
- dev_frontend_react, dev_state_management, dev_build_tools, dev_pwa
- dev_nodejs, dev_api_frameworks, dev_middleware
- dev_nosql, dev_query_optimization
- dev_microservices, dev_cloud_infrastructure, dev_containerization
- dev_monitoring, dev_serverless, dev_autoscaling, dev_chaos_engineering

---

## PM Skills

**Location**: `.ai/skills/pm/`

### L1 (Junior) Core Skills
| Skill | File | Purpose |
|-------|------|---------|
| Planning | pm_planning.skill.md | Task and sprint planning |
| Requirement Definition | pm_requirement_definition.skill.md | Requirements gathering |
| Product Analytics | product_analytics.skill.md | Basic metrics analysis |
| Stakeholder Management | stakeholder_management.skill.md | Stakeholder coordination |
| Market Research | market_research.skill.md | Market analysis |

### L2 (Senior) Core Skills
| Skill | File | Framework Reference |
|-------|------|---------------------|
| Roadmap Management | pm_roadmap_management.skill.md | - |
| Product Growth | product_growth.skill.md | - |
| Product Launch | product_launch.skill.md | - |
| Global Strategy | global_product_strategy.skill.md | - |
| Product Monetization | product_monetization.skill.md | - |
| Data-Driven Decision | data_driven_decision_making.skill.md | analytics_framework (PRODUCT) |
| User Research | user_research.skill.md | research_framework (USER) |

---

## HR Skills

**Location**: `.ai/skills/hr/`

### Core Skills
| Skill | File | Purpose |
|-------|------|---------|
| Level Check | hr_level_check.skill.md | Role level assessment |
| Onboarding | hr_onboarding.skill.md | Task document validation |
| Report Emit | hr_report_emit.skill.md | Report generation |

### Unified Skills (Consolidated)
| Skill | File | Framework Reference |
|-------|------|---------------------|
| Analytics Unified | hr_analytics_unified.skill.md | analytics_framework (TALENT) |
| Performance Lifecycle | hr_performance_lifecycle_unified.skill.md | - |
| Career Management | hr_career_management_unified.skill.md | - |
| Goal Feedback | hr_goal_feedback_unified.skill.md | - |
| Development Programs | hr_development_programs_unified.skill.md | - |
| Context Intelligence | hr_context_intelligence_unified.skill.md | - |

### Additional Skills
- hr_capacity_development, hr_organization_design, hr_role_management
- hr_task_distribution, hr_template_management, turnover_prediction

---

## Contents-Creator Skills

**Location**: `.ai/skills/contents-creator/`

### L1 (Junior) Core Skills
| Skill | File | Purpose |
|-------|------|---------|
| Contents Writing | contents_writing_fundamentals.skill.md | Basic writing |
| Image Generation | image_generation.skill.md | Asset creation |
| Video Editing | video_editing.skill.md | Basic editing |
| Ebook Editing | ebook_editing.skill.md | Proofreading |

### L2 (Senior) Core Skills
| Skill | File | Framework Reference |
|-------|------|---------------------|
| Brand Identity Design | brand_identity_design.skill.md | - |
| Contents Integration | contents_integration.skill.md | - |
| Ebook Monetization | ebook_monetization.skill.md | - |
| Ebook Platform Strategy | ebook_platform_strategy.skill.md | - |
| Audience Analytics | audience_analytics.skill.md | analytics_framework (AUDIENCE) |
| Contents Optimization | contents_optimization.skill.md | optimization_framework (CONTENT) |

### Specialized Skills
**Visual**: 3d_visualization, motion_graphics, advanced_postproduction, image_prompting
**UX/UI**: ux_ui_design, interactive_design
**Video**: video_storyboarding, video_postproduction
**Ebook**: ebook_writing, ebook_structuring, ebook_marketing, ebook_market_analysis, ebook_audience_development

---

## Finance Skills

**Location**: `.ai/skills/finance/`

### L1 (Junior) Core Skills
| Skill | File | Purpose |
|-------|------|---------|
| Financial Analysis | financial_analysis.skill.md | Basic calculations |
| Budget Management | budget_management.skill.md | Budget tracking |
| Cost Optimization | cost_optimization.skill.md | Cost analysis |
| Financial Reporting | financial_reporting.skill.md | Basic reports |
| Business Intelligence | business_intelligence.skill.md | Basic BI |

### L2 (Senior) Core Skills
| Skill | File | Framework Reference |
|-------|------|---------------------|
| Strategic Financial Planning | strategic_financial_planning.skill.md | - |
| Funding Management | funding_management.skill.md | - |
| Financial Risk Assessment | financial_risk_assessment.skill.md | - |
| Investment Portfolio | investment_portfolio_management.skill.md | - |
| System Optimization | financial_system_optimization.skill.md | optimization_framework (COST) |
| Market Trend Analysis | market_trend_analysis.skill.md | research_framework (TREND) |

### Additional Skills
- cash_flow_management, compliance_management, forecasting_modeling

---

## Shared Frameworks

**Location**: `.ai/skills/_shared/`

| Framework | Modes | Agents |
|-----------|-------|--------|
| analytics_framework.skill.md | PRODUCT, AUDIENCE, TALENT, FINANCIAL, CONTENT | All |
| optimization_framework.skill.md | PERFORMANCE, COST, CONTENT, PROCESS | Developer, Finance, Contents-Creator |
| research_framework.skill.md | USER, MARKET, AUDIENCE, TREND | PM, Contents-Creator, Finance |

---

## Skill Loading Priority

### By Context Size Impact
| Priority | Load When | Skills |
|----------|-----------|--------|
| 1 - Core | Always | Agent core L1 skills |
| 2 - Supporting | Task-specific | L2 skills matching keywords |
| 3 - Framework | Multi-domain | Shared frameworks |
| 4 - Specialized | Advanced tasks | Specialized skills |

### Context Budget Guidelines
| Scenario | Max Skills | Max Context |
|----------|------------|-------------|
| Simple task | 3 | 10KB |
| Standard task | 5-7 | 30KB |
| Complex task | 10 | 50KB |
| Cross-agent | 15 | 100KB |

---

## Version

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial index creation |
