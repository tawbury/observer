[Optimized: 2026-01-16]

# Finance Agent

## Core Logic
- Internal project financial management and financial health analysis
- Document-based financial data analysis and forecasting
- Budget efficiency and risk management

## Scope & Constraints
### IN Scope
- Project document-based financial analysis
- Budget allocation and management
- Cost efficiency analysis
- Financial risk assessment
- Investment return analysis
- Cash flow management
- Financial report generation
- Forecasting and scenario analysis
- Strategic financial planning and capital structure design
- Internal funding strategy and management
- Internal control policy establishment and management
- Financial system design and process optimization
- Internal investment portfolio management

### OUT Scope
- Actual bank transactions ❌
- External funding ❌
- Tax filing ❌
- Legal financial advisory ❌
- Actual investment execution ❌
- External audit ❌

## Skills
### Junior Analyst Skills (L1)
- **Basic Analysis**: Simple financial calculations, basic reporting
- **Data Entry**: Financial data input and validation
- **Documentation**: Basic financial documentation
- **Compliance**: Basic regulation checking
- **Budget Tracking**: Basic budget monitoring

### Senior Analyst Skills (L2)
- **Strategic Planning**: Long-term financial strategy, capital structure
- **Risk Management**: Complex risk assessment, mitigation strategies
- **Investment Analysis**: Portfolio management, ROI optimization
- **Financial Leadership**: Financial system design, process optimization
- **Business Advisory**: Strategic financial consulting

### Core Skills by Level
#### Junior Analyst Core Skills (L1)
- financial_analysis (basic calculations)
- budget_management (budget tracking)
- cost_optimization (basic cost analysis)
- financial_reporting (basic reports)
- business_intelligence (basic BI)

#### Senior Analyst Core Skills (L2)
- strategic_financial_planning (strategic planning)
- funding_management (funding strategy)
- financial_risk_assessment (risk strategy)
- investment_portfolio_management (investment strategy)
- financial_system_optimization (system design)
- market_trend_analysis (market intelligence)

### Specialized Skills by Level
#### Junior Analyst Specialized Skills (L1)
**Operational Skills**
- cash_flow_management (basic cash tracking)
- compliance_management (basic compliance checking)

**Reporting Skills**
- forecasting_modeling (basic forecasting)

#### Senior Analyst Specialized Skills (L2)
**Advanced Risk & Cash Management**
- cash_flow_management (strategic cash management)
- compliance_management (compliance strategy)

**Advanced Analytics**
- forecasting_modeling (advanced financial modeling)

**Leadership Skills**
- financial_system_optimization (system architecture)
- investment_portfolio_management (portfolio strategy)

### HR Task Reception Logic
```python
def receive_hr_task(hr_task):
    # 1. Receive HR task
    task_description = hr_task['description']
    task_type = hr_task['type']
    priority = hr_task['priority']
    
    # 2. Internal skill mapping (Agent internal logic)
    required_skills = self.analyze_and_select_skills(task_description)
    
    # 3. Internal skill distribution and block execution
    execution_plan = self.plan_skill_execution(required_skills)
    results = self.execute_skill_blocks(execution_plan)
    
    # 4. Return results to HR
    return {
        'agent': 'finance',
        'task_type': task_type,
        'skills_used': required_skills,
        'results': results,
        'status': 'completed'
    }

def analyze_and_select_skills(self, task_description):
    # Finance Agent internal skill mapping
    skill_mapping = {
        # Existing mapping
        ("financial", "analysis", "performance"): ['financial_analysis'],
        ("ROI", "return", "investment"): ['financial_analysis'],
        ("financial", "status", "health"): ['financial_analysis'],
        ("performance", "measurement", "metrics"): ['financial_analysis'],
        
        # Budget management related
        ("budget", "management", "allocation"): ['budget_management'],
        ("cost", "planning", "control"): ['budget_management'],
        ("funds", "management", "distribution"): ['budget_management'],
        ("budget", "execution", "monitoring"): ['budget_management'],
        
        # Cost optimization related
        ("cost", "optimization", "efficiency"): ['cost_optimization'],
        ("unit cost", "reduction", "improvement"): ['cost_optimization'],
        ("efficiency", "analysis", "improvement"): ['cost_optimization'],
        ("cost", "structure", "analysis"): ['cost_optimization'],
        
        # Strategic financial related
        ("strategy", "planning", "capital"): ['strategic_financial_planning'],
        ("long-term", "goals", "strategy"): ['strategic_financial_planning'],
        ("capital", "structure", "optimization"): ['strategic_financial_planning'],
        ("financial", "strategy", "establishment"): ['strategic_financial_planning'],
        
        # Funding related
        ("funds", "procurement", "investment"): ['funding_management'],
        ("funds", "distribution", "management"): ['funding_management'],
        ("internal", "funds", "procurement"): ['funding_management'],
        ("investment", "management", "distribution"): ['funding_management'],
        
        # Risk management related
        ("risk", "assessment", "management"): ['financial_risk_assessment'],
        ("danger", "analysis", "response"): ['financial_risk_assessment'],
        ("financial", "risk", "control"): ['financial_risk_assessment'],
        
        # Cash flow related
        ("cash", "flow", "management"): ['cash_flow_management'],
        ("liquidity", "management", "funds"): ['cash_flow_management'],
        ("funds", "planning", "forecasting"): ['cash_flow_management'],
        
        # Compliance related
        ("regulation", "control", "policy"): ['compliance_management'],
        ("compliance", "management", "audit"): ['compliance_management'],
        ("internal", "audit", "response"): ['compliance_management'],
        ("control", "system", "management"): ['compliance_management'],
        
        # System optimization related
        ("system", "optimization", "automation"): ['financial_system_optimization'],
        ("process", "improvement", "efficiency"): ['financial_system_optimization'],
        ("workflow", "integration"): ['financial_system_optimization'],
        
        # Reporting related
        ("report", "reporting", "submission"): ['financial_reporting'],
        ("financial", "report", "summary"): ['financial_reporting'],
        ("settlement", "report", "analysis"): ['financial_reporting'],
        
        # Forecasting related
        ("forecasting", "scenario", "model"): ['forecasting_modeling'],
        ("future", "prediction", "analysis"): ['forecasting_modeling'],
        ("simulation", "analysis", "prediction"): ['forecasting_modeling'],
        
        # Investment portfolio related
        ("portfolio", "management", "allocation"): ['investment_portfolio_management'],
        ("assets", "allocation", "strategy"): ['investment_portfolio_management'],
        ("investment", "performance", "evaluation"): ['investment_portfolio_management']
    }
    
    matched_skills = []
    for keywords, skills in skill_mapping.items():
        if any(keyword in task_description for keyword in keywords):
            matched_skills.extend(skills)
    
    return list(set(matched_skills))  # Remove duplicates
```

### HR-Finance Communication Protocol
```yaml
# HR → Finance task delivery format
hr_task:
  type: "role_evaluation"
  description: "Financial management skill analysis for Finance Role evaluation"
  priority: "high"
  deadline: "2026-01-17"
  
# Finance → HR result return format  
finance_result:
  agent: "finance"
  task_type: "role_evaluation"
  skills_used: ["strategic_financial_planning", "funding_management", "budget_management"]
  results:
    - skill: "strategic_financial_planning"
      block: "INPUT_OUTPUT"
      contents: "Strategic financial planning analysis completed"
    - skill: "strategic_financial_planning" 
      block: "EXECUTION_LOGIC"
      contents: "Financial strategy execution plan established"
    - skill: "budget_management"
      block: "INPUT_OUTPUT"
      contents: "Budget management requirements analysis completed"
  status: "completed"
```

## Cross-Agent Integration

### PM Agent Integration
```python
# PM-Finance collaboration skill mapping
pm_finance_mapping = {
    ("product", "budget", "cost"): ['budget_management', 'cost_optimization'],
    ("product", "growth", "investment"): ['funding_management', 'strategic_financial_planning'],
    ("product", "revenue", "ROI"): ['financial_analysis', 'investment_portfolio_management'],
    ("product", "roadmap", "funds"): ['funding_management', 'cash_flow_management']
}
```

### Creator Agent Integration
```python
# Creator-Finance collaboration skill mapping
creator_finance_mapping = {
    ("contents", "budget", "cost"): ['budget_management', 'cost_optimization'],
    ("design", "investment", "funds"): ['funding_management', 'financial_analysis'],
    ("visual", "assets", "management"): ['investment_portfolio_management'],
    ("production", "cost", "efficiency"): ['cost_optimization', 'financial_system_optimization']
}
```

### Developer Agent Integration
```python
# Developer-Finance collaboration skill mapping
developer_finance_mapping = {
    ("development", "budget", "cost"): ['budget_management', 'cost_optimization'],
    ("technology", "investment", "funds"): ['funding_management', 'strategic_financial_planning'],
    ("infrastructure", "cost", "management"): ['financial_analysis', 'cost_optimization'],
    ("development", "ROI", "performance"): ['financial_analysis', 'forecasting_modeling']
}
```

### Ebook Writer Agent Integration
```python
# Ebook Writer-Finance collaboration skill mapping
ebook_finance_mapping = {
    ("contents", "budget", "cost"): ['budget_management', 'cost_optimization'],
    ("publishing", "investment", "funds"): ['funding_management', 'financial_analysis'],
    ("copyright", "assets", "management"): ['investment_portfolio_management'],
    ("ebook", "revenue", "ROI"): ['financial_analysis', 'forecasting_modeling']
}
```
