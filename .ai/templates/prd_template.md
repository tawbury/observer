# PRD (Product Requirements Document) Template

## Purpose
Standard template for product requirements definition

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
- Related Reference:
- Version:

---

# [Product/Service Name] PRD

**Product Requirements Document**

---

## Product Overview
### Product Vision
- Long-term vision and goals of the product
- Position and differentiation in the market

### Problem Definition
- Core problem to solve
- Current market inconveniences

### Target Users
- Primary target user groups
- User personas and needs

## Product Goals
### Business Goals
- Revenue model and targets
- Market share goals
- Success measurement indicators

### User Goals
- User value proposition
- Core user experience goals
- Satisfaction goals

## Functional Requirements
### Core Features
- MVP (Minimum Viable Product) features
- Feature classification by priority
- Feature dependencies

### Extended Features
- Phase 2 development features
- Long-term roadmap
- Optional features

## Non-Functional Requirements
### Performance Requirements
- Response time and throughput
- Concurrent user support
- Scalability requirements

### Security Requirements
- Data protection policy
- Authentication and authorization management
- Regulatory compliance requirements

### User Experience
- Usability requirements
- Accessibility considerations
- Multi-language support

## Market and Competition
### Market Analysis
- Market size and growth rate
- Target market segmentation
- Market entry strategy

### Competitive Analysis
- Major competitor analysis
- Competitive advantage elements
- Differentiation strategy

## Development Plan
### Development Phases
- Phase 1: MVP development
- Phase 2: Feature expansion
- Phase 3: Optimization and scaling

### Schedule and Milestones
- Major milestone plan
- Development schedule
- Release plan

## Success Measurement
### Key Indicators
- User indicators (MAU, DAU, etc.)
- Business indicators (revenue, conversion rate, etc.)
- Product indicators (satisfaction, churn rate, etc.)

### Analysis Plan
- Data collection plan
- Analysis tools and methods
- Report cycle and format
```

## Field Descriptions

### Meta Fields
- **Project Name**: Project name
- **File Name**: File name (auto-generated)
- **Document ID**: Document unique ID
- **Status**: Document status (Draft/Review/Approved)
- **Created Date**: Creation date
- **Last Updated**: Last update date
- **Author**: Author
- **Parent Document**: Parent document reference
- **Related Reference**: Related reference documents
- **Version**: Document version (1.0, 1.1, 2.0, etc.)

## Usage Rules
1. File name format: `prd_<product>_<version>.md`
2. Storage location: `docs/dev/PRD/`
3. Meta section and body separated by `---`
4. All required fields must not be empty

## Related Documents
- `.ai/templates/spec_template.md` - Specification template
- `.ai/templates/architecture_template.md` - Architecture template
- `.ai/.cursorrules` - System rules
