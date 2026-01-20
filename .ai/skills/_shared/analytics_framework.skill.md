# Unified Analytics Framework

**Purpose**: Cross-agent analytics framework providing standardized analytics patterns for all domains.

---

<!-- BLOCK:CORE_LOGIC -->
## Core Logic

Unified analytics system supporting multiple analysis modes across agents:
- **PRODUCT**: Product/feature analytics (PM Agent)
- **AUDIENCE**: User/audience analytics (Contents-Creator Agent)
- **TALENT**: HR/talent analytics (HR Agent)
- **FINANCIAL**: Financial/business analytics (Finance Agent)
- **CONTENT**: Content performance analytics (Contents-Creator Agent)

### Mode Detection
```python
def detect_analytics_mode(input_data, context):
    """Auto-detect appropriate analytics mode based on input context"""
    mode_keywords = {
        'PRODUCT': ['product', 'feature', 'user engagement', 'conversion', 'funnel'],
        'AUDIENCE': ['audience', 'reader', 'viewer', 'subscriber', 'engagement'],
        'TALENT': ['employee', 'performance', 'retention', 'skill', 'workforce'],
        'FINANCIAL': ['revenue', 'cost', 'ROI', 'budget', 'profit', 'expense'],
        'CONTENT': ['content', 'views', 'shares', 'reach', 'impressions']
    }

    for mode, keywords in mode_keywords.items():
        if any(kw in input_data.lower() for kw in keywords):
            return mode
    return 'PRODUCT'  # default
```
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output Specification

### Input
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| data_source | string | Yes | Data source identifier |
| analysis_type | enum | Yes | DESCRIPTIVE/PREDICTIVE/PRESCRIPTIVE |
| mode | enum | No | Auto-detected if not specified |
| time_range | object | No | Analysis time period |
| metrics | array | No | Specific metrics to analyze |

### Output
| Field | Type | Description |
|-------|------|-------------|
| insights | array | Key findings and patterns |
| recommendations | array | Actionable suggestions |
| visualizations | array | Chart/graph specifications |
| confidence_score | float | Analysis confidence (0-1) |
| mode_used | string | Analytics mode applied |
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Phase 1: Data Collection & Preparation
1. Identify data sources based on mode
2. Validate data completeness
3. Clean and normalize data
4. Handle missing values

### Phase 2: Analysis Execution
```python
def execute_analysis(data, mode, analysis_type):
    """Execute analytics based on mode and type"""

    # Mode-specific metric definitions
    METRICS_BY_MODE = {
        'PRODUCT': ['DAU', 'MAU', 'retention', 'conversion', 'ARPU'],
        'AUDIENCE': ['engagement_rate', 'reach', 'growth_rate', 'demographics'],
        'TALENT': ['performance_score', 'turnover_risk', 'skill_gaps', 'satisfaction'],
        'FINANCIAL': ['revenue', 'margin', 'cash_flow', 'ROI', 'variance'],
        'CONTENT': ['views', 'shares', 'time_on_page', 'bounce_rate', 'CTR']
    }

    metrics = METRICS_BY_MODE.get(mode, [])

    if analysis_type == 'DESCRIPTIVE':
        return descriptive_analysis(data, metrics)
    elif analysis_type == 'PREDICTIVE':
        return predictive_analysis(data, metrics)
    elif analysis_type == 'PRESCRIPTIVE':
        return prescriptive_analysis(data, metrics)
```

### Phase 3: Insight Generation
1. Identify patterns and trends
2. Detect anomalies
3. Generate comparative analysis
4. Produce actionable recommendations

### Analysis Methods by Type
| Type | Methods | Output |
|------|---------|--------|
| Descriptive | Aggregation, Visualization, Pattern Analysis | Current state summary |
| Predictive | Forecasting, Classification, Clustering | Future predictions |
| Prescriptive | Optimization, Recommendations, Simulation | Action recommendations |
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICAL_REQUIREMENTS -->
## Technical Requirements

### Data Standards
- Minimum sample size: 100 records for statistical significance
- Time series: Minimum 30 data points for trend analysis
- Data freshness: Within 24 hours for real-time dashboards

### Performance Thresholds
| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Analysis time | <5s | 5-15s | >15s |
| Data load time | <2s | 2-5s | >5s |
| Memory usage | <100MB | 100-200MB | >200MB |

### Integration Points
- Database connections (SQL/NoSQL)
- API endpoints for real-time data
- Export formats: JSON, CSV, PDF
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Out of Scope
- Real-time streaming analytics (batch only)
- Raw data storage management
- Data source configuration
- External API management

### Agent-Specific Constraints
| Mode | Agent | Limitations |
|------|-------|-------------|
| PRODUCT | PM | No technical implementation |
| AUDIENCE | Contents-Creator | No marketing execution |
| TALENT | HR | No performance decisions |
| FINANCIAL | Finance | No actual transactions |
| CONTENT | Contents-Creator | No publishing decisions |

### Quality Standards
- Confidence score >= 0.7 for recommendations
- Minimum 3 data points for trend analysis
- All outputs must include data source citations
<!-- END_BLOCK -->

<!-- BLOCK:RELATED_SKILLS -->
## Related Skills

### PM Agent
- product_analytics.skill.md (uses PRODUCT mode)
- data_driven_decision_making.skill.md

### Contents-Creator Agent
- audience_analytics.skill.md (uses AUDIENCE mode)
- contents_analytics.skill.md (uses CONTENT mode)

### HR Agent
- hr_analytics_unified.skill.md (uses TALENT mode)

### Finance Agent
- business_intelligence.skill.md (uses FINANCIAL mode)
- financial_analysis.skill.md
<!-- END_BLOCK -->
