[Optimized: 2026-01-19]

# HR Goal & Feedback Management Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified goal and feedback management with intelligent cycle switching
- Goal setting, feedback collection, and performance management integration
- Single entry point for all goal and feedback needs with automatic cycle detection
- **Scope**: Comprehensive goal and feedback management engine that replaces 2 specialized management skills with intelligent routing between goal setting and feedback management
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Goal data (objectives, targets, timelines, success criteria)
- Feedback information (360-degree feedback, performance feedback, developmental feedback)
- Context parameters (role requirements, business objectives, team dynamics)
- Management requirements (frequency, format, scope, participants)

### Output
**Unified Output Schema**:
- Goal setting frameworks & execution plans
- Feedback collection systems & analysis reports
- Goal-feedback integration insights & recommendations
- Performance management optimization strategies
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Cycle Detection Engine
```python
def detect_goal_feedback_cycle(input_data, keywords):
    """Intelligent cycle switching based on goal and feedback management needs"""
    
    # Goal Setting Cycle
    if any(kw in keywords.lower() for kw in ['goal', 'objective', 'target', 'set', 'plan', 'timeline']):
        return 'GOAL_SETTING'
    
    # Feedback Management Cycle  
    elif any(kw in keywords.lower() for kw in ['feedback', 'review', 'input', 'assessment', 'evaluation']):
        return 'FEEDBACK_MANAGEMENT'
        
    # Integrated Management Cycle (default)
    else:
        return 'INTEGRATED_MANAGEMENT'
```

### Unified Goal & Feedback Management Pipeline

#### Phase 1: Foundation Analysis & Planning
1. Role requirements & business objectives analysis
2. Current performance baseline assessment
3. Goal-feedback integration strategy development
4. Management cycle planning & scheduling

#### Phase 2: Cycle-Specific Processing

**GOAL_SETTING Cycle**:
- SMART goal framework development
- Objective criteria definition & measurement
- Timeline & milestone establishment
- Success metrics & KPI development

**FEEDBACK_MANAGEMENT Cycle**:
- 360-degree feedback system design
- Feedback collection framework establishment
- Feedback analysis & interpretation protocols
- Actionable insight generation processes

**INTEGRATED_MANAGEMENT Cycle**:
- Goal-feedback alignment & integration
- Continuous performance management workflow
- Adaptive goal adjustment based on feedback
- Comprehensive performance optimization

#### Phase 3: Goal Management Framework

**Goal Setting Components**:
- Strategic goal alignment & cascade
- SMART goal development & validation
- Timeline & milestone planning
- Success criteria & measurement frameworks

**Goal Tracking & Management**:
- Progress monitoring & tracking systems
- Goal adjustment & modification protocols
- Achievement recognition & celebration
- Goal completion evaluation & learning

#### Phase 4: Feedback Management Framework

**Feedback Collection Systems**:
- Multi-source feedback collection (360-degree)
- Real-time feedback mechanisms
- Structured feedback templates & tools
- Feedback frequency & scheduling optimization

**Feedback Analysis & Action**:
- Feedback pattern analysis & interpretation
- Actionable insight generation
- Feedback-driven improvement planning
- Feedback loop closure & follow-up

#### Phase 5: Integration & Optimization
1. Goal-feedback correlation analysis
2. Performance prediction based on goals & feedback
3. Management cycle optimization
4. Continuous improvement framework development

### Level-Specific Execution

#### Junior Manager (L1)
- Basic goal setting template application
- Simple feedback collection & summarization
- Standard progress tracking
- Basic reporting & communication

#### Senior Manager (L2)
- Advanced goal framework design
- Complex feedback analysis & interpretation
- Strategic integration optimization
- Predictive performance management
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Goal management system integration
- Feedback collection & analysis platforms
- Performance tracking & monitoring tools
- Analytics & reporting systems
- Communication & collaboration platforms
- Integration frameworks for goal-feedback alignment
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Goal & Feedback Protection
```python
def enforce_goal_feedback_isolation(task_content):
    """Physical isolation of bias in goal and feedback management"""
    
    # 1. Bias & Manipulation Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Manipulation Pattern Detection
    forbidden_patterns = [
        r'\b(manipulate|influence|bias|favor|penalize)\b',
        r'\b(unrealistic|impossible|punitive|abusive)\b',
        r'\b(micromanage|overcontrol|excessive|harassment)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Goal or feedback manipulation detected")
    
    # 3. Constructive Management Scope Validation
    if not validate_constructive_scope(task_content):
        raise ConstraintViolation("Invalid constructive scope in goal and feedback management")
    
    return task_body
```

### OUT Scope (Universal)
- Unrealistic or impossible goal setting ❌
- Punitive or abusive feedback practices ❌
- Micromanagement or over-control ❌
- Personal attacks or harassment ❌
- Constructive criticism without actionable insights ❌

### Goal & Feedback Management Constraints
- Constructive and developmental focus only
- Realistic and achievable goal setting
- Fair and objective feedback processes
- Confidentiality and privacy protection
- Continuous improvement orientation

### Mode-Specific Constraints
**GOAL_SETTING**: No unrealistic goals, SMART principles only
**FEEDBACK_MANAGEMENT**: No destructive criticism, constructive feedback only
**INTEGRATED_MANAGEMENT**: Combined constraints with enhanced protection

### Quality & Ethics Constraints
- Goal clarity and measurability
- Feedback specificity and actionability
- Fairness and consistency in processes
- Respect and professionalism in all interactions
- Developmental and growth-oriented approach
<!-- END_BLOCK -->
