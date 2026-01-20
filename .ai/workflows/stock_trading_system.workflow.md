# Meta
- Workflow Name: Stock Trading System Development Workflow
- File Name: stock_trading_system.workflow.md
- Document ID: WF-TRADING-001
- Status: Active
- Created Date: 2026-01-20
- Last Updated: 2026-01-20
- Author: AI System
- Parent Document: .ai/workflows/README.md
- Related Reference: stock_trading_system_documentation_guide.md
- Version: 1.0.0

---

# Stock Trading System Development Workflow

## Purpose
Workflow for systematic development and operation of stock trading systems with integrated data collection and automated trading capabilities, emphasizing risk management, backtesting, and performance analysis.

## Workflow Overview
Complete stock trading system lifecycle management from strategy discovery through live trading operations, using a hybrid approach: integrated design, parallel modular development, and integrated testing/deployment/operations.

## System Structure

```
Stock Trading System
│
├─ Project 1: Data Collection & Archiving System
│  └─ Securities API → Data Extract → Archive → Database Storage
│
└─ Project 2: Automated Trading Program
   └─ DB Data Analysis → Trading Signals → Securities API Order Execution
```

## Workflow Stages

### 1. Trading Strategy Discovery & Planning
- **Lead**: PM Agent
- **Collaborate**: Finance Agent
- **Input**: Business concept, market research, trading ideas
- **Output**: Trading strategy document
- **Template**: `.ai/templates/trading_strategy_template.md`
- **Deliverable**: `docs/dev/trading/trading_strategy_<version>.md`
- **Purpose**: Define trading strategy fundamentals, entry/exit conditions, and initial risk parameters

**Key Activities:**
- Trading idea conceptualization
- Market research and analysis
- Strategy hypothesis formulation
- Initial parameter definition
- AI Collaboration: ChatGPT for strategy structuring, Claude for feasibility review

### 2. Financial Planning & Risk Assessment
- **Lead**: Finance Agent
- **Collaborate**: PM Agent, Developer Agent
- **Input**: Trading strategy document
- **Output**: Financial plan, risk management rules
- **Template**: `.ai/templates/risk_management_template.md`
- **Deliverable**: `docs/dev/trading/risk_management_<version>.md`
- **Purpose**: Establish comprehensive risk management framework and financial constraints

**Key Activities:**
- Capital allocation planning
- Risk limit definition (max loss, daily/weekly/monthly limits)
- Position sizing rules
- Stop loss and take profit parameters
- Emergency stop conditions
- Backtesting performance requirements
- AI Collaboration: Claude for risk rule design, ChatGPT for scenario analysis

### 3. Data Collection Architecture Design
- **Lead**: Developer Agent
- **Collaborate**: PM Agent
- **Input**: Trading strategy, data requirements
- **Output**: Data pipeline architecture document
- **Template**: `.ai/templates/data_pipeline_spec_template.md`, `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/data_pipeline_architecture_<project>.md`
- **Purpose**: Design ETL pipeline for securities data collection and archiving

**Key Activities:**
- Securities API specification
- Data collection schedule definition
- Archive storage format design
- Database schema design
- Data quality rules establishment
- Error handling strategy
- AI Collaboration: Windsurf for architecture design, Copilot for API wrapper code

### 4. Trading System Architecture Design
- **Lead**: Developer Agent
- **Collaborate**: Finance Agent, PM Agent
- **Input**: Trading strategy, risk management rules
- **Output**: Trading bot architecture document
- **Template**: `.ai/templates/architecture_template.md`
- **Deliverable**: `docs/dev/archi/trading_bot_architecture_<project>.md`
- **Purpose**: Design automated trading system architecture

**Key Activities:**
- Trading signal generation logic
- Order execution system design
- Real-time monitoring architecture
- Risk management system integration
- Database query optimization
- Performance requirements specification
- AI Collaboration: Claude for system design, Windsurf for implementation planning

### 5. Integrated Data & Trading Specification
- **Lead**: Developer Agent, PM Agent
- **Collaborate**: Finance Agent
- **Input**: Data pipeline architecture, trading bot architecture
- **Output**: Integrated system specification
- **Template**: `.ai/templates/spec_template.md`
- **Deliverable**: `docs/dev/spec/integrated_trading_spec_<project>.md`
- **Purpose**: Unify data and trading system specifications

**Key Activities:**
- Data flow integration (pipeline → database → trading bot)
- Shared database schema finalization
- API integration specification
- System interface standardization
- Integration testing requirements
- AI Collaboration: Claude Code for spec validation, Windsurf for technical review

### 6. Technical & Financial Decision Making
- **Lead**: PM Agent
- **Collaborate**: Developer Agent, Finance Agent
- **Input**: All specifications, constraint conditions
- **Output**: Integrated decision making record
- **Template**: `.ai/templates/decision_template.md`
- **Deliverable**: `docs/dev/decision/trading_decision_<topic>_<date>.md`
- **Purpose**: Make critical technical and financial decisions

**Key Activities:**
- Technology stack selection
- Risk parameter finalization
- Budget approval
- Timeline establishment
- Infrastructure decisions
- Security and compliance verification
- AI Collaboration: All agents for multi-perspective review

### 7. Parallel Implementation
**Purpose**: Independent modular development with coordinated integration points

#### 7.1 Data Pipeline Development
- **Lead**: Developer Agent
- **Input**: Data pipeline specification
- **Output**: Data collection system, archive storage, database loading
- **Verification**: Data quality validation, schedule compliance

**Key Activities:**
- Securities API integration
- Data extraction implementation
- Archive log system
- Database loading scripts
- Error handling and retry logic
- Data quality validation
- AI Collaboration: Windsurf for real-time coding, Copilot for code completion

#### 7.2 Trading Bot Development
- **Lead**: Developer Agent
- **Collaborate**: Finance Agent
- **Input**: Trading bot specification, risk rules
- **Output**: Trading signal generator, order execution system
- **Verification**: Unit testing, mock trading validation

**Key Activities:**
- Signal generation algorithm implementation
- Order execution logic
- Position management system
- Risk check integration
- Logging and monitoring
- AI Collaboration: Windsurf for development, Claude Code for code review

#### 7.3 Financial Monitoring
- **Lead**: Finance Agent
- **Collaborate**: Developer Agent
- **Input**: Financial plan, system specifications
- **Output**: Monitoring dashboard, performance tracking
- **Verification**: Real-time data accuracy

**Key Activities:**
- Performance metrics dashboard
- P&L tracking system
- Risk exposure monitoring
- Alert system configuration
- Report generation automation
- AI Collaboration: Claude for dashboard design, ChatGPT for report templates

#### 7.4 Risk Management System
- **Lead**: Developer Agent, Finance Agent
- **Input**: Risk management rules
- **Output**: Automated risk control system
- **Verification**: Risk scenario testing

**Key Activities:**
- Risk limit enforcement
- Circuit breaker implementation
- Position limit monitoring
- Emergency stop mechanism
- Risk alert system
- AI Collaboration: Claude for risk logic, Windsurf for implementation

### 8. Integrated Backtesting & Validation
- **Lead**: Developer Agent, Finance Agent
- **Collaborate**: PM Agent
- **Input**: Implemented systems, historical data
- **Output**: Backtesting results, validation report
- **Template**: `.ai/templates/backtesting_report_template.md`
- **Deliverable**: `docs/dev/backtesting/backtesting_results_<version>.md`
- **Purpose**: Validate trading strategy performance and system integrity

**Key Activities:**
- Historical data preparation
- Backtesting execution
- Performance metrics calculation (Sharpe ratio, max drawdown, win rate, etc.)
- Trade-by-trade analysis
- Risk metric validation
- Strategy parameter optimization
- System integration testing
- AI Collaboration: Claude for analysis, ChatGPT for report generation, Gemini for optimization suggestions

**Validation Criteria:**
- Minimum Sharpe ratio threshold
- Maximum drawdown limit compliance
- Win rate targets
- Risk-adjusted return requirements
- System reliability metrics

### 9. Deployment & Monitoring Setup
- **Lead**: Developer Agent
- **Collaborate**: Finance Agent, PM Agent
- **Input**: Validated systems, deployment plan
- **Output**: Deployed system, monitoring infrastructure, operational documentation
- **Template**: Deployment guide, operational manual
- **Deliverable**: `docs/dev/deployment/deployment_guide_<version>.md`, `docs/dev/deployment/operational_manual_<version>.md`
- **Purpose**: Deploy systems to production and establish operational procedures

**Key Activities:**
- Production environment setup
- API key and credentials configuration
- Database deployment and migration
- Monitoring system installation
- Alert configuration (Telegram, email, etc.)
- Backup and disaster recovery setup
- Operational runbook creation
- AI Collaboration: Windsurf for deployment scripts, Claude Code for documentation

**Operational Requirements:**
- Real-time system monitoring
- Performance tracking
- Error alerting
- Data backup verification
- Security compliance

### 10. Live Trading & Performance Analysis
- **Lead**: Finance Agent
- **Collaborate**: PM Agent, Developer Agent
- **Input**: Live trading data, market conditions
- **Output**: Performance reports, strategy adjustments, optimization recommendations
- **Template**: `.ai/templates/report_template.md`
- **Deliverable**: `docs/dev/reports/performance_report_<period>.md`
- **Purpose**: Operate live trading system and continuously improve performance

**Key Activities:**
- Daily trading operations
- Real-time monitoring
- Performance analysis
- Risk exposure review
- Strategy parameter adjustment
- System optimization
- Incident response
- Post-trade analysis
- AI Collaboration: Claude for log analysis, ChatGPT for performance reports, Gemini for strategy improvements

**Performance Tracking:**
- Daily/weekly/monthly P&L
- Risk-adjusted metrics
- Trade execution quality
- System uptime and reliability
- Alert response times

## Agent Roles

### PM Agent
- Trading strategy planning and coordination
- Cross-functional team leadership
- Stakeholder communication
- Progress tracking and risk management
- Strategic decision making
- **L1 Role**: Primary author for strategy and business documents
- **L2 Role**: Senior reviewer for overall project quality and integration

### Developer Agent
- System architecture design (data pipeline and trading bot)
- Technical implementation and coding
- Database design and optimization
- API integration
- Deployment and infrastructure
- Technical documentation
- **L1 Role**: Primary author for technical documents and code
- **L2 Role**: Senior reviewer for code quality, architecture, and system integration

### Finance Agent
- Financial planning and budget management
- Risk management framework design
- Backtesting analysis and validation
- Performance monitoring and reporting
- Trading performance evaluation
- Risk compliance verification
- **L1 Role**: Primary author for financial and risk documents
- **L2 Role**: Senior reviewer for financial accuracy and risk compliance

## L1/L2 Role Definitions

### L1 Agent (Author) Responsibilities
- Document creation and initial development
- Basic quality assurance and self-review
- Submission for L2 review process
- **Meta Field**: Author field assignment

### L2 Agent (Reviewer) Responsibilities
- Senior-level work review and validation
- Technical excellence assessment
- Risk compliance verification
- Final approval and certification
- **Meta Field**: Reviewer field assignment

## Agent Collaboration Matrix

| Stage | PM | Developer | Finance |
|-------|-----|-----------|---------|
| 1. Trading Strategy Discovery | Lead | - | Collaborate |
| 2. Financial Planning & Risk | Collaborate | Collaborate | Lead |
| 3. Data Architecture Design | Collaborate | Lead | - |
| 4. Trading System Architecture | Collaborate | Lead | Collaborate |
| 5. Integrated Specification | Collaborate | Lead | Collaborate |
| 6. Decision Making | Lead | Collaborate | Collaborate |
| 7.1 Data Pipeline Dev | - | Lead | - |
| 7.2 Trading Bot Dev | - | Lead | Collaborate |
| 7.3 Financial Monitoring | Collaborate | Collaborate | Lead |
| 7.4 Risk Management System | Collaborate | Lead | Lead |
| 8. Backtesting & Validation | Collaborate | Lead | Lead |
| 9. Deployment & Monitoring | Collaborate | Lead | Collaborate |
| 10. Live Trading & Analysis | Collaborate | Collaborate | Lead |

## Related Documents

### Templates
- `.ai/templates/trading_strategy_template.md` - Trading strategy specification
- `.ai/templates/risk_management_template.md` - Risk management rules
- `.ai/templates/data_pipeline_spec_template.md` - Data pipeline specification
- `.ai/templates/backtesting_report_template.md` - Backtesting results
- `.ai/templates/architecture_template.md` - System architecture
- `.ai/templates/spec_template.md` - Technical specifications
- `.ai/templates/decision_template.md` - Decision making records
- `.ai/templates/report_template.md` - Performance reports

### Agents
- `.ai/agents/pm.agent.md` - PM agent
- `.ai/agents/developer.agent.md` - Development agent
- `.ai/agents/finance.agent.md` - Finance agent

### Skills
- `.ai/skills/pm/` - PM related skills (strategy, coordination, risk management)
- `.ai/skills/developer/` - Development skills (architecture, API, database, deployment)
- `.ai/skills/finance/` - Finance skills (planning, risk assessment, analysis, forecasting)

### Reference Documents
- `stock_trading_system_documentation_guide.md` - Comprehensive documentation guide
- `.ai/workflows/integrated_development.workflow.md` - Multi-agent collaboration patterns
- `.ai/workflows/financial_management.workflow.md` - Financial workflow patterns

## Constraint Conditions

### Quality Standards
- All deliverables must comply with templates
- Code must pass unit tests and integration tests
- Architecture must guarantee scalability and maintainability
- Data quality must meet defined standards

### Security Requirements
- API key and credential security (encryption, vault storage)
- Secure data transmission
- Access control and authentication
- Audit logging for all trading operations
- Security review required at all development stages

### Risk Management Requirements
- All risk limits must be enforced programmatically
- Emergency stop mechanism must be tested and verified
- Real-time risk monitoring mandatory
- Circuit breakers must prevent over-trading
- Position limits must be strictly enforced

### Regulatory & Compliance
- Trading regulations compliance
- Data privacy and protection
- Audit trail maintenance
- Reporting requirements satisfaction

### Performance Requirements
- Data collection latency within acceptable range
- Trading signal generation speed targets
- Order execution latency requirements
- System uptime target: 99.9% or higher during trading hours
- Monitoring and alerting response time

## Success Indicators

### Trading Performance
- **Sharpe Ratio**: Target value or higher (e.g., > 1.5)
- **Maximum Drawdown**: Within acceptable limit (e.g., < 15%)
- **Win Rate**: Target percentage or higher (e.g., > 55%)
- **Profit Factor**: Target value or higher (e.g., > 1.5)
- **Risk-Adjusted Return**: Meets or exceeds benchmark

### System Reliability
- **Data Collection Success Rate**: 99.5% or higher
- **Order Execution Success Rate**: 99.9% or higher
- **System Uptime**: 99.9% or higher during trading hours
- **Alert Response Time**: Within target (e.g., < 1 minute)
- **Data Quality Compliance**: 99.9% or higher

### Operational Efficiency
- **Development Period Compliance**: Within planned timeline
- **Budget Compliance**: 95% or higher
- **Backtesting Validation Success**: All scenarios passed
- **Incident Resolution Time**: Within target (e.g., < 15 minutes for critical)
- **Monitoring Coverage**: 100% of critical metrics

### Risk Management
- **Risk Limit Violations**: Zero tolerance
- **Emergency Stop Effectiveness**: 100% success rate
- **Risk Exposure**: Always within defined limits
- **Compliance Rate**: 100% for all regulations
- **Audit Readiness**: Continuous compliance

## Non-Developer Collaboration Points

### Discovery Phase (Stage 1-2)
- **User Role**: Define trading ideas, strategy concepts, risk tolerance
- **AI Tools**: ChatGPT (strategy structuring), Claude (feasibility), Gemini (research)

### Planning Phase (Stage 3-6)
- **User Role**: Review and approve specifications, provide domain knowledge
- **AI Tools**: Claude (design review), Windsurf (architecture), Copilot (API samples)

### Development Phase (Stage 7)
- **User Role**: Monitor progress, provide intermediate testing, adjust parameters
- **AI Tools**: Windsurf (real-time coding), Copilot (completion), Claude Code (review)

### Testing Phase (Stage 8)
- **User Role**: Provide test scenarios, validate backtesting assumptions, review results
- **AI Tools**: Claude (analysis), ChatGPT (reports), Gemini (optimization)

### Deployment Phase (Stage 9)
- **User Role**: Final approval, credential configuration, operational readiness
- **AI Tools**: Claude Code (deployment scripts), Windsurf (environment setup)

### Operations Phase (Stage 10)
- **User Role**: Daily monitoring, parameter tuning, performance review, strategy improvements
- **AI Tools**: Claude (diagnostics), ChatGPT (reports), Windsurf (bug fixes), Gemini (improvements)

## Workflow Execution Notes

### Hybrid Approach Benefits
1. **Integrated Design (Stages 1-6)**: Ensures data pipeline and trading bot share common architecture, reducing integration risks
2. **Parallel Development (Stage 7)**: Accelerates delivery while maintaining module independence
3. **Integrated Testing/Ops (Stages 8-10)**: Validates end-to-end system and ensures unified operations

### Critical Success Factors
- Clear communication between PM, Developer, and Finance agents
- Comprehensive risk management from day one
- Thorough backtesting before live trading
- Continuous monitoring and optimization post-deployment
- Rapid incident response procedures

### Risk Mitigation Strategies
- Start with paper trading before live trading
- Implement graduated capital deployment
- Maintain strict risk limits
- Regular strategy review and adjustment
- Comprehensive backup and disaster recovery

---

*This workflow integrates best practices from software development, financial management, and risk control to create a robust stock trading system development and operation framework.*
