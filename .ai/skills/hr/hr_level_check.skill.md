[Optimized: 2026-01-16]

# HR Level Check Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Task text-based Level determination
- Result: L1 | L2 | PENDING
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
- Task document contents (Meta section excluded)

### Output
- Level Result (L1/L2/PENDING)
- Decision Basis Summary
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic
### Decision Rules
#### Common Criteria
- **L1 (Junior):** Guidance/supervision required, learning phase, limited responsibility
- **L2 (Senior):** Independent execution, mentoring, complex problem solving, decision-making authority

#### Department Keywords
- **Dev:** 
  - L2=architecture design, technical debt management, code review leadership, system design, API design, security architecture, performance strategy
  - L1=function implementation, bug fixes, basic testing, code documentation, basic integration

- **contents-creator**: 
  - L2=strategy establishment, brand guideline formulation, pipeline optimization, contents architecture, revenue strategy, cross-media integration
  - L1=simple editing, asset creation, template usage, basic writing, basic formatting

- **pm**: 
  - L2=strategic planning, market analysis, product vision, growth strategy, roadmap leadership, stakeholder coordination
  - L1=task execution, backlog management, basic planning, milestone tracking, basic documentation

- **finance**: 
  - L2=strategic financial planning, risk management, investment analysis, financial system design, business advisory
  - L1=basic analysis, budget tracking, data entry, basic reporting, compliance checking

#### PENDING Criteria
- Criteria unclear/insufficient
- L1/L2 distinction ambiguous
- Judgment information insufficient
- Vague/general skills only present

### Judgment Logic
1. Analyze Task text `Provided Criteria` section only (Meta excluded)
2. Apply specialized keyword weighting based on `Department` field
3. Judge as L1 if closer to L1 criteria
4. Judge as L2 if closer to L2 criteria
5. Judge as PENDING if unclear
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICAL_REQUIREMENTS -->
## Technical Requirements
- Task document parsing capability
- Keyword matching algorithms
- Department-specific criteria database
- Judgment result formatting
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints
- Meta information interpretation prohibited
- Task text-based judgment ONLY
- PENDING processing when clear criteria absent
- Objective keyword-based judgment
<!-- END_BLOCK -->
