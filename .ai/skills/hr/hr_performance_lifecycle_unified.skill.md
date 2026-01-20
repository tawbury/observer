[Optimized: 2026-01-19]

# HR Performance Lifecycle Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified performance lifecycle management with intelligent phase switching
- Performance evaluation, analysis, and improvement in integrated workflow
- Single entry point for all performance lifecycle needs with automatic phase detection
- **Scope**: Comprehensive performance lifecycle engine that replaces 2 specialized performance skills with intelligent routing between evaluation (WHAT), analysis (WHY), and improvement (HOW)
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Performance data (evaluations, ratings, goals, achievements)
- Context information (role requirements, business objectives, feedback)
- Analysis parameters (timeframe, scope, depth, focus areas)
- Improvement requirements (resources, constraints, priorities)

### Output
**Unified Output Schema**:
- Performance evaluation results & ratings
- Performance analysis reports & insights
- Performance improvement plans & recommendations
- Performance calibration results & optimization strategies
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Phase Detection Engine
```python
def detect_performance_phase(input_data, keywords):
    """Intelligent phase switching based on performance lifecycle needs"""
    
    # Performance Evaluation Phase (WHAT)
    if any(kw in keywords.lower() for kw in ['evaluate', 'rate', 'assess', 'measure', 'review', 'what']):
        return 'PERFORMANCE_EVALUATION'
    
    # Performance Analysis Phase (WHY)
    elif any(kw in keywords.lower() for kw in ['analyze', 'diagnose', 'interpret', 'investigate', 'why']):
        return 'PERFORMANCE_ANALYSIS'
        
    # Performance Improvement Phase (HOW)
    elif any(kw in keywords.lower() for kw in ['improve', 'enhance', 'optimize', 'develop', 'how']):
        return 'PERFORMANCE_IMPROVEMENT'
        
    # Unified Lifecycle Mode (default)
    else:
        return 'UNIFIED_LIFECYCLE'
```

### Unified Performance Lifecycle Pipeline

#### Phase 1: Performance Data Collection & Validation
1. Performance evaluation data collection
2. Goal achievement records compilation
3. 360-degree feedback data integration
4. Performance improvement plan outcomes review

#### Phase 2: Phase-Specific Processing

**PERFORMANCE_EVALUATION Phase**:
- Performance rating & assessment execution
- Goal achievement measurement & validation
- Objective performance criteria application
- Fair evaluation process implementation

**PERFORMANCE_ANALYSIS Phase**:
- Performance trend analysis & interpretation
- Root cause analysis of performance variations
- Performance pattern identification & diagnosis
- Strategic performance insight generation

**PERFORMANCE_IMPROVEMENT Phase**:
- Performance gap identification & assessment
- Improvement opportunity analysis & prioritization
- Intervention strategy development & planning
- Performance optimization roadmap creation

**UNIFIED_LIFECYCLE Mode**:
- End-to-end performance management process
- Integrated evaluation → analysis → improvement workflow
- Comprehensive performance lifecycle management
- Holistic performance optimization strategy

#### Phase 3: Performance Intelligence & Analytics

**Descriptive Analytics**:
- Performance distribution analysis
- Performance trend identification
- Comparative performance analysis
- Performance variance assessment

**Predictive Analytics**:
- Performance prediction modeling
- At-risk employee identification
- Performance improvement forecasting
- Success probability modeling

**Prescriptive Analytics**:
- Performance optimization recommendations
- Intervention strategy optimization
- Resource allocation recommendations
- Performance improvement planning

#### Phase 4: Performance Management & Planning
1. Performance calibration & normalization
2. Improvement plan development & prioritization
3. Resource allocation & timeline planning
4. Success measurement & evaluation frameworks

### Level-Specific Execution

#### Junior Performance Manager (L1)
- Basic performance evaluation execution
- Simple performance analysis & reporting
- Standard improvement plan templates
- Basic performance tracking

#### Senior Performance Manager (L2)
- Advanced performance modeling & analysis
- Complex performance calibration
- Strategic performance optimization
- Predictive performance management
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Performance management system integration
- Goal tracking & measurement platforms
- Feedback collection & analysis systems
- Performance analytics & modeling tools
- Calibration & normalization frameworks
- Predictive modeling & machine learning platforms
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Performance Management Protection
```python
def enforce_performance_lifecycle_isolation(task_content):
    """Physical isolation of bias in performance lifecycle management"""
    
    # 1. Bias Detection & Prevention
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Bias Pattern Detection
    forbidden_patterns = [
        r'\b(subjective|personal|biased|preferential|discriminatory)\b',
        r'\b(individual\s+judgment|personal\s+opinion|unfair\s+treatment)\b',
        r'\b(manipulation|favoritism|nepotism|harassment)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Performance bias detected in lifecycle management")
    
    # 3. Fair Evaluation Scope Validation
    if not validate_fair_evaluation_scope(task_body):
        raise ConstraintViolation("Invalid fair evaluation scope in performance lifecycle")
    
    return task_body
```

### OUT Scope (Universal)
- Individual performance ratings without evidence ❌
- Subjective performance judgments ❌
- Unfair or discriminatory evaluation practices ❌
- Personal performance counseling without data ❌
- Legal performance management decisions ❌

### Performance Lifecycle Constraints
- Evidence-based evaluation & analysis only
- Objective criteria application & consistency
- Fairness & transparency in all processes
- Data-driven decision making & insights
- Equal opportunity & non-discrimination

### Mode-Specific Constraints
**PERFORMANCE_EVALUATION**: No subjective ratings, evidence-based only
**PERFORMANCE_ANALYSIS**: No speculation, data-driven interpretation only
**PERFORMANCE_IMPROVEMENT**: No unrealistic expectations, achievable plans only
**UNIFIED_LIFECYCLE**: Combined constraints with enhanced fairness protection

### Quality & Ethics Constraints
- Performance evaluation fairness & accuracy
- Analysis methodology rigor & validity
- Improvement plan feasibility & relevance
- Performance management confidentiality & privacy
- Continuous improvement & learning orientation
<!-- END_BLOCK -->
