# Developer Agent Skill Validator

## Purpose
Developer Agent skill validation and quality assurance for technical development capabilities

## Validation Rules

### 1. Developer Skill Structure Validation
#### Required Developer Skills
- Core development skills: backend, frontend, testing, documentation
- Architecture skills: API design, system architecture, security
- Performance skills: optimization, deployment, database design
- Quality skills: code review, mentoring
- Enhanced skills: technical debt analysis, code quality

#### Skill Level Requirements
- Junior Developer (L1): 6 core skills minimum
- Senior Developer (L2): 9 core skills minimum
- Clear L1/L2 differentiation
- Technical complexity progression

### 2. Developer Skill Content Validation
#### Core Logic Validation
- Technical implementation logic clarity
- Code quality and maintainability focus
- System design principles
- Performance optimization emphasis

#### Execution Logic Validation
- Junior level: basic development tasks
- Senior level: architectural leadership
- Clear technical progression
- Code review leadership

### 3. Developer Skill Quality Standards
#### Developer-Specific Requirements
- Code quality standards compliance
- Technical accuracy validation
- Security best practices
- Performance optimization focus

#### Quality Metrics
- Technical implementation quality
- Code review effectiveness
- Architecture design quality
- Performance optimization impact

## Developer Skill Validation Matrix

### Core Skills Validation
#### dev_backend.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Backend development completeness
- **L1/L2**: Basic vs advanced backend
- **Integration**: System architecture integration

#### dev_frontend.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Frontend development completeness
- **L1/L2**: Basic vs advanced frontend
- **Integration**: User experience integration

#### dev_frontend_react.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: React-specific development completeness
- **L2**: Senior Developer advanced React patterns
- **Integration**: Frontend skill dependency (prerequisite: dev_frontend.skill.md)
- **Prerequisite Validation**: Must reference dev_frontend.skill.md for baseline concepts

#### dev_testing.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Testing methodology completeness
- **L1/L2**: Basic vs advanced testing
- **Integration**: Quality assurance integration

#### dev_documentation.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Documentation standards completeness
- **L1/L2**: Basic vs advanced documentation
- **Integration**: Code review integration

### Architecture Skills Validation
#### dev_api_design.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: API design methodology completeness
- **L1/L2**: Basic vs architectural API design
- **Integration**: System architecture integration

#### dev_system_architecture.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Architecture methodology completeness
- **L1/L2**: Basic vs system architecture
- **Integration**: All development skills integration

#### dev_security.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Security methodology completeness
- **L1/L2**: Basic vs security leadership
- **Integration**: Code review integration

### Performance Skills Validation
#### dev_performance_optimization.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Optimization methodology completeness
- **L1/L2**: Basic vs advanced optimization
- **Integration**: Code quality integration

#### dev_deployment.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Deployment methodology completeness
- **L1/L2**: Basic vs deployment architecture
- **Integration**: System architecture integration

#### dev_database_design.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Database design methodology
- **L1/L2**: Basic vs schema architecture
- **Integration**: System architecture integration
- **Relationship**: Related to dev_query_optimization.skill.md and dev_nosql.skill.md

#### dev_query_optimization.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Query performance tuning and optimization completeness
- **L2**: Senior Developer query specialist
- **Integration**: Specialist layer dependency (prerequisite: dev_database_design.skill.md)
- **Prerequisite Validation**: Must reference dev_database_design.skill.md for schema concepts

#### dev_nosql.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: NoSQL database design and implementation completeness
- **L2**: Senior Developer NoSQL specialization
- **Integration**: Technology specialization dependency (prerequisite: dev_database_design.skill.md)
- **Prerequisite Validation**: Must reference dev_database_design.skill.md for data modeling concepts
- **Query Integration**: Should reference dev_query_optimization.skill.md for NoSQL query tuning

### Backend Stack Skills Validation

#### dev_nodejs.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Node.js runtime and server architecture completeness
- **L2**: Senior Developer backend foundation
- **Integration**: Base layer for api_frameworks and middleware
- **Relationship**: Related to dev_api_frameworks.skill.md and dev_middleware.skill.md

#### dev_api_frameworks.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: API framework design and implementation completeness
- **L2**: Senior Developer API design patterns
- **Integration**: Framework layer dependency (prerequisite: dev_nodejs.skill.md)
- **Prerequisite Validation**: Must reference dev_nodejs.skill.md for runtime concepts
- **Middleware Integration**: Should reference dev_middleware.skill.md for cross-cutting concerns

#### dev_middleware.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Middleware development and cross-cutting concerns completeness
- **L2**: Senior Developer middleware patterns
- **Integration**: Cross-cutting layer dependency (prerequisite: dev_nodejs.skill.md)
- **Prerequisite Validation**: Must reference dev_nodejs.skill.md for server concepts
- **Usage Validation**: Should be referenced by dev_api_frameworks.skill.md

### Enhanced Skills Validation
#### code_quality_and_technical_debt_analysis.skill.md
- **Structure**: Standard skill structure compliance
- **Content**: Quality and debt analysis methodology completeness
- **L1/L2**: Basic vs advanced quality and technical debt analysis
- **Integration**: Code quality and technical debt analysis integration
- **Consolidation Note**: Merged from technical_debt_analysis.skill.md and code_quality_analysis.skill.md (2026-01-17)

## Performance Metrics

### Developer Skill Quality Metrics
- Structure compliance: 100%
- Content completeness: 95%+
- Integration quality: 90%+
- Technical accuracy: 95%+

### Developer Agent Capability Metrics
- Code quality standards compliance
- Technical implementation quality
- Architecture design effectiveness
- Performance optimization impact
- Security best practices adherence

## Integration
- Connect to skill_validator.md for general skill validation
- Integrate with meta_validator.md for developer skill meta validation
- Support workflow validation for developer-workflow integration
- Enable cross-agent validation for developer-other agent coordination

## Usage
- Applied during developer skill creation and modification
- Used for developer agent capability assessment
- Supports developer skill optimization
- Enables developer agent performance evaluation

## Quality Standards
- Code quality standards compliance: 100%
- Technical accuracy: 95%+
- Security best practices: 90%+
- Performance optimization: 85%+
