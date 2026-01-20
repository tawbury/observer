[Optimized: 2026-01-19]

# PM Analytics Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified product analytics with intelligent domain switching
- Product performance analysis, market research, user research, and data-driven decisions
- Single entry point for all product analytics needs with automatic domain detection
- **Scope**: Comprehensive product analytics engine that replaces 4 specialized analytics skills with intelligent routing
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Product usage data & performance metrics
- Business objectives & KPI requirements
- User feedback & behavioral data
- Market information & competitive data

### Output
**Unified Output Schema**:
- Product performance analysis reports & insights
- Market research results & competitive analysis
- User research findings & behavioral insights
- Data-driven recommendations & decision frameworks
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Analytics Detection Engine
```python
def detect_analytics_mode(input_data, keywords):
    """Intelligent domain switching based on product analytics needs"""
    
    # Product Analytics Mode
    if any(kw in keywords.lower() for kw in ['product', 'usage', 'performance', 'metrics', 'kpi']):
        return 'PRODUCT_ANALYTICS'
    
    # Market Research Mode  
    elif any(kw in keywords.lower() for kw in ['market', 'research', 'competitive', 'industry', 'trend']):
        return 'MARKET_RESEARCH'
        
    # User Research Mode
    elif any(kw in keywords.lower() for kw in ['user', 'customer', 'research', 'behavior', 'insight']):
        return 'USER_RESEARCH'
        
    # Data-Driven Decisions Mode
    elif any(kw in keywords.lower() for kw in ['decision', 'data-driven', 'analytics', 'insight', 'recommendation']):
        return 'DATA_DRIVEN_DECISIONS'
        
    # Unified Analytics Mode (default)
    else:
        return 'UNIFIED_ANALYTICS'
```

### Unified Product Analytics Pipeline

#### Phase 1: Data Collection & Preparation
1. Business objective analysis & measurement indicator definition
2. Product data collection & cleansing
3. User feedback aggregation & behavioral data processing
4. Market information gathering & competitive data compilation

#### Phase 2: Mode-Specific Analysis

**PRODUCT_ANALYTICS Mode**:
- Product data analysis & performance measurement
- User behavior data → business insights transformation
- Data-based decision making & product improvement
- A/B testing & performance optimization

**MARKET_RESEARCH Mode**:
- Market research & competitive analysis
- Industry trend identification & market opportunity analysis
- Competitive landscape assessment & positioning
- Market sizing & segmentation analysis

**USER_RESEARCH Mode**:
- User research & behavioral analysis
- Customer insight generation & persona development
- User experience evaluation & satisfaction measurement
- User journey mapping & pain point identification

**DATA_DRIVEN_DECISIONS Mode**:
- Data-driven decision making frameworks
- Advanced analytics & predictive modeling
- Business intelligence & reporting automation
- Strategic insights & recommendation generation

**UNIFIED_ANALYTICS Mode**:
- Comprehensive product analytics implementation
- Integrated product + market + user + decision analytics
- End-to-end data-driven product management
- Full-stack analytics optimization

#### Phase 3: Insight Generation & Analysis
1. Pattern recognition & trend analysis
2. Correlation analysis & causation testing
3. Predictive modeling & forecasting
4. Strategic insight derivation & recommendation

#### Phase 4: Reporting & Action
1. Analytics reports & dashboard creation
2. Insight communication & stakeholder alignment
3. Action plan development & implementation tracking
4. Performance monitoring & continuous improvement

### Level-Specific Execution

#### Junior Product Analyst (L1)
- Basic product analytics & performance reporting
- Simple market research & competitive analysis
- Standard user research & feedback collection
- Basic data-driven decision support

#### Senior Product Analyst (L2)
- Advanced product analytics & predictive modeling
- Complex market research & strategic analysis
- Sophisticated user research & behavioral insights
- Strategic data-driven decision leadership
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Analytics platforms (Google Analytics, Mixpanel, Amplitude)
- Business intelligence tools (Tableau, Power BI, Looker)
- Survey & user research tools (SurveyMonkey, Typeform, Hotjar)
- Market research platforms & competitive intelligence tools
- Data analysis & statistical software
- Visualization & reporting frameworks
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Product Analytics Protection
```python
def enforce_product_analytics_isolation(task_content):
    """Physical isolation of product development in analytics"""
    
    # 1. Product Development Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Development Pattern Detection
    forbidden_patterns = [
        r'\b(development|coding|programming|implementation)\b',
        r'\b(frontend|backend|database|api|technical)\b',
        r'\b(deployment|testing|debugging|engineering)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Product development detected in analytics")
    
    # 3. Product Analytics Scope Validation
    if not validate_product_analytics_scope(task_body):
        raise ConstraintViolation("Invalid product analytics scope")
    
    return task_body
```

### OUT Scope (Universal)
- Product development & technical implementation ❌
- Engineering decisions & architecture design ❌
- Database management & infrastructure ❌
- Code development & deployment ❌
- Technical operations & maintenance ❌

### Product Analytics Constraints
- Analytics & research only
- Data analysis & insight generation
- Market intelligence & competitive analysis
- User research & behavioral understanding
- Modern analytics best practices

### Mode-Specific Constraints
**PRODUCT_ANALYTICS**: Product data only, no market analysis
**MARKET_RESEARCH**: Market analysis only, no product data
**USER_RESEARCH**: User insights only, no product development
**DATA_DRIVEN_DECISIONS**: Decision frameworks only, no implementation
**UNIFIED_ANALYTICS**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- Analytics standards & data quality
- Research methodology & statistical validity
- User privacy & data protection
- Business intelligence best practices
- Ethical research & data-driven culture
<!-- END_BLOCK -->
