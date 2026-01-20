# Unified Research Framework

**Purpose**: Cross-agent research framework providing standardized research patterns for all domains.

---

<!-- BLOCK:CORE_LOGIC -->
## Core Logic

Unified research system supporting multiple domains:
- **USER**: User research and experience insights (PM Agent)
- **MARKET**: Market research and competitive analysis (PM/Finance Agent)
- **AUDIENCE**: Audience research and behavior analysis (Contents-Creator Agent)
- **TREND**: Trend analysis and forecasting (Finance Agent)

### Mode Detection
```python
def detect_research_mode(input_data, context):
    """Auto-detect appropriate research mode"""
    mode_keywords = {
        'USER': ['user', 'customer', 'persona', 'journey', 'experience', 'usability'],
        'MARKET': ['market', 'competitor', 'industry', 'positioning', 'share'],
        'AUDIENCE': ['audience', 'reader', 'viewer', 'demographic', 'segment'],
        'TREND': ['trend', 'forecast', 'prediction', 'future', 'emerging']
    }

    for mode, keywords in mode_keywords.items():
        if any(kw in input_data.lower() for kw in keywords):
            return mode
    return 'MARKET'  # default
```
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output Specification

### Input
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| research_objective | string | Yes | What to research |
| scope | object | Yes | Research boundaries |
| data_sources | array | No | Primary/secondary sources |
| methodology | enum | No | QUALITATIVE/QUANTITATIVE/MIXED |
| mode | enum | No | Auto-detected if not specified |

### Output
| Field | Type | Description |
|-------|------|-------------|
| findings | array | Key research findings |
| insights | array | Actionable insights |
| recommendations | array | Strategic recommendations |
| data_summary | object | Summarized research data |
| confidence_level | string | HIGH/MEDIUM/LOW |
| mode_used | string | Research mode applied |
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Standard Research Process
1. **Planning** - Define objectives, scope, methodology
2. **Data Collection** - Gather primary and secondary data
3. **Data Analysis** - Process and analyze collected data
4. **Synthesis** - Combine findings into insights
5. **Reporting** - Document and present findings

### Mode-Specific Methods
```python
def execute_research(objective, mode, methodology):
    """Execute research based on mode"""

    METHODS_BY_MODE = {
        'USER': {
            'qualitative': ['interviews', 'focus_groups', 'observation', 'diary_studies'],
            'quantitative': ['surveys', 'A/B_testing', 'analytics', 'heatmaps']
        },
        'MARKET': {
            'qualitative': ['expert_interviews', 'case_studies', 'SWOT_analysis'],
            'quantitative': ['market_sizing', 'share_analysis', 'benchmarking']
        },
        'AUDIENCE': {
            'qualitative': ['persona_development', 'journey_mapping', 'community_analysis'],
            'quantitative': ['demographic_analysis', 'behavior_tracking', 'segmentation']
        },
        'TREND': {
            'qualitative': ['expert_panels', 'scenario_planning', 'Delphi_method'],
            'quantitative': ['time_series', 'regression', 'leading_indicators']
        }
    }

    methods = METHODS_BY_MODE.get(mode, {})
    return apply_research_methods(objective, methods, methodology)
```

### Data Source Categories
| Category | Examples | Reliability |
|----------|----------|-------------|
| Primary | Interviews, Surveys, Experiments | High |
| Secondary | Reports, Publications, Databases | Medium-High |
| Tertiary | Aggregators, Summaries | Medium |

### Analysis Framework
| Type | Methods | Output |
|------|---------|--------|
| Qualitative | Thematic analysis, Coding, Pattern matching | Themes, Patterns |
| Quantitative | Statistical analysis, Regression, Clustering | Metrics, Correlations |
| Mixed | Triangulation, Cross-validation | Comprehensive insights |
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICAL_REQUIREMENTS -->
## Technical Requirements

### Sample Size Guidelines
| Research Type | Minimum Sample | Recommended |
|---------------|----------------|-------------|
| Qualitative interviews | 8-12 | 15-20 |
| Quantitative surveys | 100 | 300+ |
| A/B tests | 1,000 per variant | 5,000+ |
| Trend analysis | 24 time points | 36+ |

### Data Quality Standards
- Source credibility verification
- Data recency (within 12 months for market data)
- Sample representativeness validation
- Bias assessment and mitigation

### Documentation Requirements
- Research methodology documentation
- Data collection instruments
- Analysis procedures
- Limitations and assumptions
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Out of Scope
- Direct customer contact (research design only)
- Personal data collection without consent
- Competitor intelligence gathering (unethical methods)
- Real-time data collection systems

### Ethical Guidelines
- Informed consent required for primary research
- Data privacy compliance (GDPR, etc.)
- Transparent methodology reporting
- Conflict of interest disclosure

### Agent-Specific Constraints
| Mode | Agent | Limitations |
|------|-------|-------------|
| USER | PM | No customer relationship management |
| MARKET | PM/Finance | No competitive intelligence operations |
| AUDIENCE | Contents-Creator | No direct audience engagement |
| TREND | Finance | No investment recommendations |
<!-- END_BLOCK -->

<!-- BLOCK:RELATED_SKILLS -->
## Related Skills

### PM Agent
- user_research.skill.md (uses USER mode)
- market_research.skill.md (uses MARKET mode)

### Contents-Creator Agent
- audience_analytics.skill.md (uses AUDIENCE mode)
- ebook_market_analysis.skill.md (uses MARKET mode)

### Finance Agent
- market_trend_analysis.skill.md (uses TREND mode)
- business_intelligence.skill.md (uses MARKET mode)
<!-- END_BLOCK -->
