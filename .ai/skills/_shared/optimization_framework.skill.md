# Unified Optimization Framework

**Purpose**: Cross-agent optimization framework providing standardized optimization patterns for all domains.

---

<!-- BLOCK:CORE_LOGIC -->
## Core Logic

Unified optimization system supporting multiple domains:
- **PERFORMANCE**: System/code performance optimization (Developer Agent)
- **COST**: Cost reduction and efficiency (Finance Agent)
- **CONTENT**: SEO/UX content optimization (Contents-Creator Agent)
- **PROCESS**: Workflow/process optimization (All Agents)

### Mode Detection
```python
def detect_optimization_mode(input_data, context):
    """Auto-detect appropriate optimization mode"""
    mode_keywords = {
        'PERFORMANCE': ['performance', 'speed', 'latency', 'throughput', 'memory'],
        'COST': ['cost', 'budget', 'expense', 'efficiency', 'reduction'],
        'CONTENT': ['SEO', 'UX', 'engagement', 'conversion', 'readability'],
        'PROCESS': ['workflow', 'process', 'automation', 'efficiency', 'productivity']
    }

    for mode, keywords in mode_keywords.items():
        if any(kw in input_data.lower() for kw in keywords):
            return mode
    return 'PROCESS'  # default
```
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output Specification

### Input
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target_area | string | Yes | Area to optimize |
| current_metrics | object | Yes | Current performance baseline |
| constraints | object | No | Optimization constraints |
| priority | enum | No | SPEED/QUALITY/COST |
| mode | enum | No | Auto-detected if not specified |

### Output
| Field | Type | Description |
|-------|------|-------------|
| recommendations | array | Prioritized optimization actions |
| expected_improvement | object | Predicted improvement metrics |
| implementation_plan | array | Step-by-step implementation |
| risk_assessment | object | Potential risks and mitigations |
| mode_used | string | Optimization mode applied |
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Standard 8-Step Pattern
All optimization modes follow this pattern:

1. **Analyze** - Evaluate current state and metrics
2. **Identify** - Find optimization opportunities
3. **Prioritize** - Rank by impact and feasibility
4. **Design** - Create optimization strategies
5. **Validate** - Test strategies against constraints
6. **Implement** - Execute optimization changes
7. **Monitor** - Track improvement metrics
8. **Report** - Document results and learnings

### Mode-Specific Execution
```python
def execute_optimization(target, mode, constraints):
    """Execute optimization based on mode"""

    TECHNIQUES_BY_MODE = {
        'PERFORMANCE': {
            'analysis': ['profiling', 'benchmarking', 'bottleneck_detection'],
            'strategies': ['caching', 'lazy_loading', 'code_optimization', 'resource_pooling']
        },
        'COST': {
            'analysis': ['cost_breakdown', 'variance_analysis', 'benchmark_comparison'],
            'strategies': ['consolidation', 'automation', 'renegotiation', 'elimination']
        },
        'CONTENT': {
            'analysis': ['SEO_audit', 'UX_analysis', 'A/B_testing'],
            'strategies': ['keyword_optimization', 'structure_improvement', 'load_optimization']
        },
        'PROCESS': {
            'analysis': ['workflow_mapping', 'bottleneck_analysis', 'time_study'],
            'strategies': ['automation', 'parallel_processing', 'elimination', 'simplification']
        }
    }

    techniques = TECHNIQUES_BY_MODE.get(mode, {})
    return apply_optimization_techniques(target, techniques, constraints)
```

### Prioritization Matrix
| Impact | Effort: Low | Effort: Medium | Effort: High |
|--------|-------------|----------------|--------------|
| High | **Priority 1** | Priority 2 | Priority 3 |
| Medium | Priority 2 | Priority 3 | Priority 4 |
| Low | Priority 3 | Priority 4 | Do Not Do |
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICAL_REQUIREMENTS -->
## Technical Requirements

### Baseline Requirements
- Documented current state metrics
- Defined success criteria
- Established measurement methodology

### Performance Standards by Mode
| Mode | Key Metric | Target Improvement |
|------|------------|-------------------|
| PERFORMANCE | Response time | >= 20% faster |
| COST | Total cost | >= 15% reduction |
| CONTENT | Engagement | >= 10% increase |
| PROCESS | Cycle time | >= 25% reduction |

### Monitoring Requirements
- Before/after comparison metrics
- Continuous monitoring post-implementation
- Rollback capability for all changes
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Out of Scope
- Actual implementation execution (analysis only)
- Budget approval decisions
- Personnel changes
- Third-party vendor negotiations

### Quality Gates
- All recommendations must have measurable KPIs
- Risk assessment required for high-impact changes
- Stakeholder approval required before implementation

### Agent-Specific Constraints
| Mode | Agent | Limitations |
|------|-------|-------------|
| PERFORMANCE | Developer | No infrastructure purchases |
| COST | Finance | No contract terminations |
| CONTENT | Contents-Creator | No brand guideline changes |
| PROCESS | All | No organizational restructuring |
<!-- END_BLOCK -->

<!-- BLOCK:RELATED_SKILLS -->
## Related Skills

### Developer Agent
- dev_performance_optimization.skill.md (uses PERFORMANCE mode)

### Finance Agent
- cost_optimization.skill.md (uses COST mode)

### Contents-Creator Agent
- contents_optimization.skill.md (uses CONTENT mode)

### Cross-Agent
- skill_performance_management.md (uses PROCESS mode)
<!-- END_BLOCK -->
