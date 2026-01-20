# Skill Performance Management

**Consolidation Note**: This file merges three previously separate system skills:
- `context_monitor.md` (monitoring)
- `skill_loading_optimizer.md` (optimization strategies)
- `performance_test.md` (testing/validation)

All functionality is preserved. For legacy reference paths, see DEPRECATED stubs at original locations.

---

## Core Logic

Integrated system for monitoring, optimizing, and validating skill loading performance to maintain context efficiency and system responsiveness.

---

## Part 1: Context Monitoring

### Purpose
- Monitor and track context usage across skill loading
- Provide alerts for potential performance issues
- Generate optimization recommendations

### Monitoring Metrics

#### Context Usage Metrics
```python
class ContextMetrics:
    def __init__(self):
        self.total_context_size = 0
        self.skill_count = 0
        self.loading_time = 0
        self.memory_usage = 0
```

#### Performance Thresholds (Canonical)
| Level | Threshold | Action |
|-------|-----------|--------|
| Green (Optimal) | <50KB | Normal operation |
| Yellow (Monitor) | 50-100KB | Monitor closely |
| Orange (Warning) | 100-150KB | Optimization needed |
| Red (Critical) | >150KB | Immediate action required |

**Legacy Note**: `performance_test.md` referenced 166KB for full system load (all skills). This 150KB threshold is the standard operational limit for any single agent's active skill set.

#### Performance Indicators
- Loading time per skill
- Memory usage trends
- Cache hit rates
- Response time impact

### Monitoring Implementation

#### Real-time Monitoring
```python
def monitor_context_usage(agent_name, skills_loaded):
    metrics = ContextMetrics()
    metrics.total_context_size = calculate_total_size(skills_loaded)
    metrics.skill_count = len(skills_loaded)
    
    # Check thresholds
    if metrics.total_context_size > 100000:  # 100KB
        log_warning("High context usage detected", agent_name)
    
    return metrics
```

#### Usage Analytics
```python
def generate_usage_report():
    return {
        "average_context_size": calculate_average(),
        "most_used_skills": identify_frequent_skills(),
        "optimization_opportunities": find_optimizations(),
        "performance_trends": track_trends()
    }
```

### Alert System

#### Warning Levels
- **GREEN**: <50KB, optimal performance
- **YELLOW**: 50-100KB, monitor closely
- **ORANGE**: 100-150KB, optimization required
- **RED**: >150KB, immediate optimization needed

#### Alert Actions
- Log performance issues
- Suggest optimizations
- Trigger automatic cleanup
- Notify system administrators

#### Optimization Recommendations
1. **Skill Consolidation**: Merge similar skills
2. **Block Compression**: Reduce redundant descriptions
3. **Caching Strategy**: Cache frequently accessed skills
4. **Lazy Loading**: Load skills on-demand

---

## Part 2: Skill Loading Optimization

### Purpose
- Optimize context usage for skill document loading
- Implement selective skill loading based on agent requirements
- Minimize memory footprint while maintaining functionality

### Loading Strategies

#### 1. Block-Level Loading
```python
def load_skill_block(skill_name, block_type):
    """Load specific block instead of entire file"""
    skill_file = f".ai/skills/{agent}/{skill_name}.skill.md"
    return extract_block(skill_file, block_type)
```

#### 2. Priority-Based Loading
```python
SKILL_PRIORITY = {
    "core": ["CORE_LOGIC", "EXECUTION_LOGIC"],
    "supporting": ["INPUT_OUTPUT", "TECHNICAL_REQUIREMENTS"],
    "optional": ["CONSTRAINTS"]
}
```

#### 3. Agent-Specific Loading
```python
AGENT_SKILL_SETS = {
    "developer": ["dev_backend", "dev_frontend", "dev_api_design"],
    "contents-creator": ["visual_design_fundamentals", "ebook_writing"],
    "pm": ["pm_planning", "pm_requirement_definition"],
    "finance": ["financial_analysis", "budget_management"]
}
```

### Context Optimization Rules

#### Loading Priority
1. Load only requested agent's core skills
2. Load supporting blocks only when needed
3. Cache frequently used skills
4. Lazy load optional blocks

#### Memory Management
- Maximum 10 skills loaded simultaneously
- Automatic cleanup of unused skills
- Context usage monitoring (see Part 1)
- Performance metrics tracking

### Implementation Example
```python
def optimized_skill_loading(agent_name, task_requirements):
    # 1. Identify required skills
    required_skills = map_task_to_skills(task_requirements)
    
    # 2. Load agent-specific skill set
    agent_skills = AGENT_SKILL_SETS.get(agent_name, [])
    
    # 3. Load only necessary blocks
    context = {}
    for skill in required_skills:
        if skill in agent_skills:
            context[skill] = load_skill_block(skill, "CORE_LOGIC")
    
    return context
```

### Integration Points
- **Part 1 (Monitoring)**: Track performance of optimized loading
- **Part 3 (Testing)**: Validate optimization effectiveness

---

## Part 3: Performance Test Scenarios

### Purpose
- Define benchmark test scenarios
- Establish performance thresholds
- Validate optimization effectiveness

### Test Scenarios

#### Scenario 1: Single Agent Request
**Test Case**: Developer agent requests API design skill
- Expected context: ~2KB (single skill)
- Loading time: <100ms
- Memory usage: Minimal
- Status: ✓ Optimal

#### Scenario 2: Multi-Skill Request
**Test Case**: PM agent requests planning + requirements + analytics
- Expected context: ~6KB (3 skills)
- Loading time: <200ms
- Memory usage: Low
- Status: ✓ Optimal

#### Scenario 3: Complex Task Request
**Test Case**: Contents-creator requests full ebook creation workflow
- Expected context: ~15KB (8-10 skills)
- Loading time: <500ms
- Memory usage: Moderate
- Status: ✓ Acceptable

#### Scenario 4: Cross-Agent Collaboration
**Test Case**: Developer + PM + Finance collaboration
- Expected context: ~20KB (multiple agents)
- Loading time: <800ms
- Memory usage: Moderate-High
- Status: ✓ Acceptable

#### Scenario 5: Full System Load (Stress Test)
**Test Case**: All agents with maximum skill sets
- Expected context: ~166KB (all skills)
- Loading time: <2000ms
- Memory usage: High
- Status: ⚠ Warning (exceeds operational threshold)

### Performance Benchmarks

#### Acceptable Thresholds (by scenario)
- **Single Skill**: <100ms loading time
- **Multi-Skill**: <500ms loading time
- **Complex Task**: <1000ms loading time
- **Cross-Agent**: <1500ms loading time
- **Full System**: <3000ms loading time

#### Context Limits (by operational mode)
- **Optimal**: <50KB total context
- **Acceptable**: 50-100KB context
- **Warning**: 100-150KB context (Part 1)
- **Critical**: >150KB context (Part 1)

### Test Implementation

#### Test Script
```python
def run_performance_test():
    scenarios = [
        test_single_agent,
        test_multi_skill,
        test_complex_task,
        test_cross_agent,
        test_full_system
    ]
    
    results = {}
    for scenario in scenarios:
        results[scenario.__name__] = scenario()
    
    return generate_performance_report(results)
```

#### Metrics Collection
- Loading time per scenario
- Context size measurement
- Memory usage tracking
- Response time impact
- Error rate monitoring

### Optimization Validation

#### Before Optimization
- Full system load: 166KB context
- Loading time: ~3000ms
- Memory usage: High

#### After Optimization (with Part 2 strategies)
- Selective loading: ~20KB context
- Loading time: ~500ms
- Memory usage: Moderate

#### Improvement Metrics
- Context reduction: 88%
- Loading time improvement: 83%
- Memory usage reduction: 75%

### Recommendations

1. **Implement selective loading** (Part 2) for all agent requests
2. **Add context monitoring** (Part 1) for real-time performance tracking
3. **Create skill caching** for frequently used skills (Part 2)
4. **Establish context limits** per operational mode (Part 1)
5. **Regular performance testing** (this section) to maintain optimization

---

## Integration & Constraints

### Dependencies
- Requires: Skill loading infrastructure in agent initialization
- Used by: All agents during skill context management
- Affects: System responsiveness and memory footprint

### Testing Requirements
- Run performance tests (Part 3) before production deployment
- Monitor alerts (Part 1) continuously
- Validate optimization (Part 2) monthly

### Performance SLA
- 95% of requests should load within optimal thresholds (Part 3)
- No single agent should exceed 150KB context (Part 1)
- Average context usage should remain <50KB (Part 1)

