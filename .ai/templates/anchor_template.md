# Anchor Document Template

## Purpose
Standard template for anchor documents that serve as the foundation for all planning

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

# [Project/Product Name] Anchor Document

---

## Overview
### Project Vision
- Long-term vision and core values of the project
- Reason for existence and fundamental problem to solve
- Changes and impact to achieve upon success

### Problem Definition
- Core problem definition to solve
- Current market/industry inconveniences and opportunities
- Problem importance and urgency

### Solution Overview
- Core concept of solution provided
- Solution originality and differentiation
- Comparative advantage over existing alternatives

## Goal Setting
### Business Goals
- Revenue model and target revenue
- Market share goals
- Success measurement indicators (KPI)
- Business success criteria

### User Goals
- Target user group definition
- Core value users will gain
- User experience goals
- User success criteria

### Technical Goals
- Technical innovation goals
- Performance and scalability goals
- Technical advantage securing goals
- Technical debt minimization goals

## Market Analysis
### Market Status
- Market size and growth rate
- Market trends and change factors
- Market entry barriers and opportunities
- Market maturity and characteristics

### Competitive Analysis
- Major competitor analysis
- Competitor strengths and weaknesses
- Market positioning analysis
- Competitive advantage securing strategy

### Target Market
- Primary target market definition
- Market segmentation strategy
- Market entry priorities
- Market expansion plan

## Solution Strategy
### Core Strategy
- Market entry strategy
- Competitive advantage strategy
- Growth strategy
- Revenue generation strategy

### Product Strategy
- Product positioning
- Product differentiation strategy
- Product roadmap
- Product lifecycle management

### Technical Strategy
- Technical architecture strategy
- Technology stack selection strategy
- Technical innovation strategy
- Technical partnering strategy

## Execution Plan
### Phase-by-Phase Plan
#### Phase 1: Initial Market Entry
- Period: [Period]
- Goals: [Major goals]
- Key Activities: [Core activities]
- Success Indicators: [Measurement indicators]

#### Phase 2: Growth and Expansion
- Period: [Period]
- Goals: [Major goals]
- Key Activities: [Core activities]
- Success Indicators: [Measurement indicators]

#### Phase 3: Market Leadership
- Period: [Period]
- Goals: [Major goals]
- Key Activities: [Core activities]
- Success Indicators: [Measurement indicators]

### Key Milestones
- [Milestone 1]: [Description and schedule]
- [Milestone 2]: [Description and schedule]
- [Milestone 3]: [Description and schedule]

## Resource Plan
### Human Resources
- Core roles and responsibilities
- Team composition and scale
- External expert utilization plan
- Organizational structure and reporting system

### Financial Resources
- Initial investment requirement
- Operating fund plan
- Fund raising strategy
- Financial risk management

### Technical Resources
- Core technical infrastructure
- Technical partnerships
- Technology licenses
- Technical personnel training plan

## Risk Management
### Major Risks
#### Market Risks
- [Risk 1]: [Impact and probability, mitigation measures]
- [Risk 2]: [Impact and probability, mitigation measures]

#### Technical Risks
- [Risk 1]: [Impact and probability, mitigation measures]
- [Risk 2]: [Impact and probability, mitigation measures]

#### Operational Risks
- [Risk 1]: [Impact and probability, mitigation measures]
- [Risk 2]: [Impact and probability, mitigation measures]

### Risk Management Strategy
- Risk monitoring plan
- Crisis response protocol
- Risk mitigation measures
- Continuous risk evaluation

## Success Criteria
### Success Measurement Indicators
#### Business Indicators
- Revenue goal achievement rate
- Market share
- Customer satisfaction
- Financial health indicators

#### Product Indicators
- Product completion level
- User adoption rate
- Product quality indicators
- Technical performance indicators

#### Operational Indicators
- Team productivity
- Operational efficiency
- Risk management level
- Organizational health

### Success Conditions
- [Success Condition 1]: [Specific criteria]
- [Success Condition 2]: [Specific criteria]
- [Success Condition 3]: [Specific criteria]

## Governance
### Decision Making Structure
- Major decision making authority
- Decision making process
- Stakeholder participation method
- Decision making records and traceability

### Performance Management
- Performance measurement method
- Performance reporting cycle
- Performance improvement plan
- Incentive design

### Regulatory Compliance
- Related laws and regulations
- Compliance procedures and processes
- Regulatory risk management
- Legal review plan

## Change Management
### Document Version Management
- Version information managed in Meta section Version field
- Change approval procedures
- Change history records
- Stakeholder notification

### Modification Procedures
- Change request procedures
- Change impact evaluation
- Change approval criteria
- Change execution and confirmation

## Appendix
### Term Definitions
- [Term 1]: [Definition]
- [Term 2]: [Definition]

### Reference Materials
- [Material 1]: [Description]
- [Material 2]: [Description]

### Contact Information
- Project responsible person: [Information]
- Major contact: [Information]
- Inquiries: [Information]
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
1. File name format: `anchor_<project>_<version>.md`
2. Storage location: `docs/dev/anchor/`
3. Meta section and main text separated by `---`
4. All required fields must not be empty
5. Record change history when updating version

## Features
- **Reference Document**: Core document that serves as foundation for all planning documents
- **Strategic Level**: Includes business strategy and execution plans
- **Comprehensiveness**: Covers market, solution, execution, risk, success criteria
- **Sustainability**: Includes change management and version management system

## Related Documents
- `.ai/templates/prd_template.md` - Product requirements template
- `.ai/templates/architecture_template.md` - Architecture template
- `.ai/workflows/project_management.workflow.md` - Project management workflow
- `.ai/.cursorrules` - System rules
