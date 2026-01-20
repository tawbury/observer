[Optimized: 2026-01-19]

# HR Development Programs Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified development programs with intelligent modality switching
- Training program design and mentorship program management
- Single entry point for all development program needs with automatic modality detection
- **Scope**: Comprehensive development programs engine that replaces 2 specialized program skills with intelligent routing between structured training and relational mentoring
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Capability gap analysis results & development requirements
- Learning objectives & goals (individual/organizational)
- Resource constraints (budget, time, expertise)
- Program parameters (scale, duration, format preferences)

### Output
**Unified Output Schema**:
- Development program design proposals (training/mentorship)
- Learning curriculums & mentorship matching strategies
- Execution plans & performance measurement systems
- Program quality management & evaluation frameworks
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Modality Detection Engine
```python
def detect_development_modality(input_data, keywords):
    """Intelligent modality switching based on development program needs"""
    
    # Training Program Mode
    if any(kw in keywords.lower() for kw in ['training', 'course', 'curriculum', 'formal', 'structured', 'education']):
        return 'TRAINING_PROGRAM'
    
    # Mentorship Program Mode  
    elif any(kw in keywords.lower() for kw in ['mentorship', 'mentoring', 'relationship', 'experiential', 'guidance', 'coaching']):
        return 'MENTORSHIP_PROGRAM'
        
    # Unified Mode (default)
    else:
        return 'UNIFIED'
```

### Unified Development Programs Pipeline

#### Phase 1: Development Requirements Analysis
1. Capability gap analysis review & validation
2. Learning objectives specification & prioritization
3. Resource constraints assessment & optimization
4. Program success criteria definition

#### Phase 2: Modality-Specific Processing

**TRAINING_PROGRAM Mode**:
- Structured learning curriculum design
- Formal education program development
- Training materials & tools preparation
- Performance measurement indicator setting

**MENTORSHIP_PROGRAM Mode**:
- Relational learning program design
- Mentor-mentee matching algorithm development
- Experience transfer framework establishment
- Relationship quality management systems

**UNIFIED Mode**:
- Integrated development program design
- Blended learning approach (formal + experiential)
- Comprehensive learning ecosystem design
- Multi-modal development strategy

#### Phase 3: Program Design & Development

**Training Program Components**:
- Learning objective setting & specification
- Training program design & development
- Learning curriculum composition & sequencing
- Training materials & tools preparation

**Mentorship Program Components**:
- Mentorship requirements analysis
- Mentor/mentee capability evaluation
- Matching algorithm design & optimization
- Program structure design & management

#### Phase 4: Implementation Planning
1. Execution plan & schedule establishment
2. Resource allocation & budget optimization
3. Performance measurement system design
4. Quality assurance & evaluation frameworks

#### Phase 5: Program Management & Evaluation
1. Program quality review & improvement
2. Performance evaluation & feedback
3. Success measurement & ROI analysis
4. Program optimization & scaling

### Level-Specific Execution

#### Junior Program Designer (L1)
- Basic program template application
- Simple curriculum design
- Standard matching algorithm use
- Basic quality assurance

#### Senior Program Designer (L2)
- Advanced program architecture design
- Complex learning experience development
- Customized matching algorithm creation
- Strategic program optimization
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Training design tools & curriculum development systems
- Learning management platforms (LMS) integration
- Mentorship management platforms & matching algorithms
- Performance measurement & evaluation tools
- Communication systems & relationship management tools
- Program management & quality assurance frameworks
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Program Development Protection
```python
def enforce_development_program_isolation(task_content):
    """Physical isolation of execution operations in program development"""
    
    # 1. Execution Operation Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Execution Pattern Detection
    forbidden_patterns = [
        r'\b(execute|implement|deliver|teach|instruct)\b',
        r'\b(manage|supervise|coordinate|conduct|facilitate)\b',
        r'\b(certify|award|accredit|license|credential)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Execution operation detected in program development")
    
    # 3. Design-Only Scope Validation
    if not validate_design_scope(task_body):
        raise ConstraintViolation("Invalid design scope in development programs")
    
    return task_body
```

### OUT Scope (Universal)
- Actual training execution or teaching ❌
- Instructor management or supervision ❌
- Actual learning execution or assessment ❌
- Certificate issuance or credentialing ❌
- Substantial education provision ❌
- Actual mentorship execution or relationship management ❌
- Legal personnel management or counseling ❌

### Development Programs Constraints
- Design-based proposals only
- Realistic program plans & timelines
- Resource constraint consideration & optimization
- Effective learning design & relationship building
- Voluntary participation prerequisite (mentorship)
- Mutual respect & professional relationships

### Mode-Specific Constraints
**TRAINING_PROGRAM**: No actual teaching, design & curriculum only
**MENTORSHIP_PROGRAM**: No actual mentoring, program design & matching only
**UNIFIED**: Combined design-only constraints with enhanced protection

### Quality & Ethics Constraints
- Evidence-based program design
- Accessibility & inclusion considerations
- Cultural sensitivity & respect
- Sustainable development practices
- Continuous improvement & quality assurance
<!-- END_BLOCK -->
