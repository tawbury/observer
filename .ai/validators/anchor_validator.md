# Anchor Validator

## Purpose
Structural integrity and strategic validity verification for anchor documents

## Validation Rules

### 1. Meta Field Verification
#### Required Field List
- Project Name
- File Name
- Document ID
- Status
- Created Date
- Last Updated
- Author
- Reviewer
- Parent Document
- Related Reference
- Version

#### Verification Conditions
- All required fields must exist
- Field values must not be empty
- Meta section format must be correct
- Version field must be standard format (1.0, 1.1, 2.0, etc.)

### 2. contents Section Verification
#### Required Section List
- Overview
- Goal Setting
- Market Analysis
- Solution Strategy
- Execution Plan
- Resource Plan
- Risk Management
- Success Criteria
- Governance
- Change Management
- Appendix

#### Verification Conditions
- All required sections must exist
- Section header format must be `##`
- Section contents must not be empty
- Strategic depth as anchor document guaranteed

### 3. Overview Verification
#### Project Vision Criteria
- Clear long-term vision presentation
- Existence reason and fundamental problem definition
- Success achievement changes and impact specification

#### Problem Definition Criteria
- Core problem to solve clearly defined
- Current market/industry inconveniences and opportunities identified
- Problem importance and urgency evaluated

### 4. Goal Setting Verification
#### Business Goal Criteria
- Specific revenue model and target revenue presentation
- Clear market share goals
- Success measurement indicators (KPI) definition
- Business success criteria specification

#### User Goal Criteria
- Clear target user group definition
- Core value users will gain presentation
- User experience goal definition
- User success criteria specification

### 5. Market Analysis Verification
#### Market Status Criteria
- Specific market size and growth rate data
- Market trends and change factor analysis
- Market entry barriers and opportunities identification
- Market maturity and characteristics evaluation

#### Competitive Analysis Criteria
- Major competitors identification and analysis
- Competitor strengths and weaknesses evaluation
- Market positioning analysis
- Competitive advantage securing strategy presentation

### 6. Solution Strategy Verification
#### Core Strategy Criteria
- Clear market entry strategy presentation
- Differentiated competitive advantage strategy
- Sustainable growth strategy
- Clear revenue generation strategy

#### Product Strategy Criteria
- Clear product positioning
- Differentiated product strategy
- Realistic product roadmap
- Systematic product lifecycle management

### 7. Execution Plan Verification
#### Phase-by-Phase Plan Criteria
- Minimum 3-phase specific plan
- Clear goals and timeline for each phase
- Specific major activities definition
- Measurable success indicators presentation

#### Milestone Criteria
- Major milestone identification and definition
- Clear timeline and goals
- Milestone achievement criteria presentation

### 8. Resource Plan Verification
#### Human Resource Criteria
- Core roles and responsibilities clearly defined
- Realistic team composition and scale
- External expert utilization plan
- Clear organizational structure and reporting system

#### Financial Resource Criteria
- Specific initial investment requirement
- Realistic operating fund plan
- Clear fund raising strategy
- Systematic financial risk management

### 9. Risk Management Verification
#### Risk Identification Criteria
- Market, technology, operation risk identification
- Each risk impact and probability evaluation
- Specific mitigation measures presentation
- Continuous risk monitoring plan

#### Risk Management Strategy Criteria
- Systematic risk monitoring
- Clear crisis response protocol
- Effective risk mitigation measures
- Continuous risk evaluation plan

### 10. Success Criteria Verification
#### Success Measurement Indicator Criteria
- Business, product, operation indicators included
- Specific and measurable indicators
- Clear success criteria presentation
- Success condition fulfillment check

### 11. Structure Verification
#### Structure Requirements
- Meta section contents must not be empty
- contents separator presence (`---`)
- Logical contents flow
- Section header format

#### Verification Sequence
1. Meta section completeness check
2. All required contents sections existence confirmation
3. Section header format verification (##)
4. Required fields not empty confirmation
5. Strategic depth verification
6. Execution feasibility verification

## Result Output

### PASS Conditions
- All required Meta fields exist and not empty
- All required contents sections exist
- Strategic depth and completeness satisfied
- Execution plan reality secured
- Success criteria specificity secured

### FAIL Conditions
- Required fields/sections missing
- Field values empty
- Structure format errors
- Strategic depth insufficient
- Execution plan unrealistic
- Success criteria ambiguity

### Output Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
Missing Sections: [section1, section2, ...] (if FAIL)
Strategic Issues: [issue1, issue2, ...] (if FAIL)
Execution Issues: [issue1, issue2, ...] (if FAIL)
Success Criteria Issues: [issue1, issue2, ...] (if FAIL)
```

## Special Considerations
- **Strategic Depth**: Strategic depth and completeness verification important
- **Market Analysis**: Market analysis specificity and validity confirmation
- **Execution Feasibility**: Execution plan reality verification
- **Success Metrics**: Success criteria specificity and measurability

## Related Documents
- `.ai/templates/anchor_template.md` - Anchor document template definition
- `.ai/workflows/project_management.workflow.md` - Project management workflow
- `.ai/.cursorrules` - System rules
