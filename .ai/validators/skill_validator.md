# Skill Validator

## Purpose
Skill structure validation and quality assurance for all agent skills

## Validation Rules

### 1. Skill Structure Verification
#### Required Skill Structure
- Optimized header with date format: `[Optimized: YYYY-MM-DD]`
- Skill title with proper naming convention
- Core Logic block with `<!-- BLOCK:CORE_LOGIC -->` tags
- Input/Output block with `<!-- BLOCK:INPUT_OUTPUT -->` tags
- Execution Logic block with `<!-- BLOCK:EXECUTION_LOGIC -->` tags
- Proper block closing tags: `<!-- END_BLOCK -->`

#### Verification Conditions
- All required blocks must exist
- Block tags must be properly formatted
- Skill title must follow naming convention
- Header date must be current or recent

### 2. Skill Content Validation
#### Core Logic Requirements
- Clear skill purpose definition
- Core logic description
- Input/output transformation logic
- Value proposition statement

#### Input/Output Requirements
- Input section with clear input definitions
- Output section with clear output definitions
- Input/output relevance to core logic
- Input/output completeness

#### Execution Logic Requirements
- Execution flow definition
- Level-specific execution (L1/L2)
- Skill component breakdown
- Performance metrics definition

### 3. Skill Quality Standards
#### Content Quality
- Clear and concise descriptions
- Logical flow and structure
- Consistent terminology
- Actionable insights

#### Technical Quality
- Proper markdown formatting
- Consistent header hierarchy
- Correct block tag usage
- No syntax errors

### 4. Skill Integration Validation
#### Integration Requirements
- Integration section with other skills
- Connection to relevant workflows
- Tool and platform references
- Quality standards compliance

#### Cross-Skill Consistency
- Consistent terminology across skills
- Standardized execution logic
- Uniform performance metrics
- Common integration patterns

## Skill Type Validation

### PM Skills Validation
#### Required Components
- Junior/Senior level differentiation
- PM-specific terminology
- Product management focus
- Stakeholder integration

#### PM-Specific Validation
- Product lifecycle coverage
- Market research integration
- Stakeholder management
- Data-driven decision making

### Developer Skills Validation
#### Required Components
- Technical accuracy validation
- Code quality standards
- Architecture principles
- Performance optimization

#### Developer-Specific Validation
- Technical debt analysis
- Code review processes
- Security best practices
- System architecture design

### Finance Skills Validation
#### Required Components
- Financial accuracy standards
- Regulatory compliance
- Risk assessment frameworks
- Business intelligence

#### Finance-Specific Validation
- Financial analysis accuracy
- Budget management standards
- Investment analysis quality
- Market trend analysis

### HR Skills Validation
#### Required Components
- Data privacy compliance
- Performance evaluation standards
- Talent assessment accuracy
- Organizational analysis

#### HR-Specific Validation
- Talent analytics accuracy
- Performance analysis quality
- Confidentiality standards
- Ethical data usage

### Contents Creator Skills Validation
#### Required Components
- Content quality standards
- Brand guideline compliance
- Audience analysis accuracy
- Creative quality metrics

#### Contents-Specific Validation
- Visual design quality
- Content strategy alignment
- Audience engagement metrics
- Brand consistency

## Performance Metrics

### Skill Quality Metrics
- Structure compliance score
- Content completeness score
- Integration quality score
- Technical accuracy score

### Execution Quality Metrics
- Logic clarity score
- Flow efficiency score
- Level differentiation score
- Insight relevance score

## Integration
- Connect to meta_validator.md for skill meta validation
- Integrate with structure_validator.md for skill structure validation
- Support agent-specific validators for skill-agent alignment
- Enable workflow validation for skill-workflow integration

## Usage
- Applied during skill creation and modification
- Used for skill quality assurance
- Supports skill optimization
- Enables skill standardization

## Quality Standards
- Structure compliance: 100%
- Content completeness: 95%+
- Integration quality: 90%+
- Technical accuracy: 95%+
