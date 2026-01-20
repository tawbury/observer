[Optimized: 2026-01-19]

# Quality Assurance Framework Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Universal quality standards & evaluation criteria across all media types
- Cross-media quality consistency and performance optimization
- Contents quality assurance methodologies and continuous improvement
- **Scope**: Comprehensive QA framework that ensures consistent quality standards across all media while enabling media-specific quality optimization and performance measurement
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Content assets across all media types and formats
- Quality standards and brand guidelines
- Performance metrics and evaluation criteria
- Platform-specific requirements and technical constraints

### Output
**Unified Output Schema**:
- Quality assessment reports and evaluation results
- Cross-media quality consistency analysis
- Performance optimization recommendations
- Quality improvement strategies and action plans
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Quality Detection Engine
```python
def detect_quality_mode(input_data, keywords):
    """Intelligent quality switching based on QA needs"""
    
    # Visual QA Mode
    if any(kw in keywords.lower() for kw in ['visual', 'image', 'design', 'graphic', 'brand', '3d', 'motion']):
        return 'VISUAL_QA'
    
    # Text QA Mode  
    elif any(kw in keywords.lower() for kw in ['text', 'writing', 'content', 'article', 'story', 'readability']):
        return 'TEXT_QA'
        
    # Interactive QA Mode
    elif any(kw in keywords.lower() for kw in ['interactive', 'ux', 'ui', 'prototype', 'usability', 'accessibility']):
        return 'INTERACTIVE_QA'
        
    # Video QA Mode
    elif any(kw in keywords.lower() for kw in ['video', 'film', 'animation', 'audio', 'quality', 'streaming']):
        return 'VIDEO_QA'
        
    # Unified QA Mode (default)
    else:
        return 'UNIFIED_QA'
```

### Universal Quality Assurance Pipeline

#### Phase 1: Quality Standards Analysis
1. Content asset analysis and quality requirement identification
2. Brand guideline review and consistency standard establishment
3. Platform-specific quality criteria and technical constraint evaluation
4. Performance metrics definition and quality benchmark setting

#### Phase 2: Mode-Specific Quality Assessment

**VISUAL_QA Mode**:
- Visual design quality assessment and consistency verification
- Brand identity compliance and visual hierarchy evaluation
- Color accuracy, typography quality, and composition standards
- Cross-platform visual quality and technical specification compliance

**TEXT_QA Mode**:
- Text quality assessment and readability evaluation
- Content accuracy, grammar, and style consistency verification
- Audience-appropriate language and tone assessment
- Cross-format text quality and localization quality standards

**INTERACTIVE_QA Mode**:
- User experience quality assessment and usability evaluation
- Accessibility compliance and interaction design quality verification
- Cross-platform interactive quality and performance standards
- User testing results and experience optimization recommendations

**VIDEO_QA Mode**:
- Video quality assessment and technical specification compliance
- Audio-visual synchronization and production quality evaluation
- Cross-platform video quality and streaming performance standards
- Content appropriateness and brand alignment verification

**UNIFIED_QA Mode**:
- Comprehensive cross-media quality assessment
- Integrated quality consistency analysis and optimization
- Holistic brand experience quality evaluation
- End-to-end quality assurance and performance optimization

#### Phase 3: Quality Testing & Validation
1. Cross-media quality testing and consistency verification
2. Platform-specific quality validation and compliance checking
3. Brand guideline enforcement and identity consistency assessment
4. User experience testing and quality feedback collection

#### Phase 4: Quality Optimization & Improvement
1. Quality issue identification and root cause analysis
2. Cross-media quality optimization strategies and implementation
3. Performance improvement recommendations and action planning
4. Continuous quality monitoring and enhancement programs

### Level-Specific Execution

#### Junior QA Specialist (L1)
- Basic quality assessment and standard evaluation
- Template-based quality checking and compliance verification
- Cross-media consistency monitoring and basic optimization
- Quality reporting and documentation

#### Senior QA Specialist (L2)
- Advanced quality assessment methodologies and custom evaluation frameworks
- Complex cross-media quality optimization and strategic quality planning
- Quality standard development and innovation leadership
- Quality assurance excellence and continuous improvement programs
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Quality assurance platforms and testing frameworks
- Cross-media quality monitoring and analytics tools
- Brand management and consistency verification systems
- Performance testing and optimization platforms
- User testing and feedback collection systems
- Quality reporting and documentation tools
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Quality Assurance Protection
```python
def enforce_quality_assurance_isolation(task_content):
    """Physical isolation of content creation in quality assurance"""
    
    # 1. Content Creation Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Creation Pattern Detection
    forbidden_patterns = [
        r'\b(create|design|write|produce|generate)\b',
        r'\b(develop|implement|code|program|build)\b',
        r'\b(edit|modify|compose|craft|make)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Content creation detected in quality assurance")
    
    # 3. Quality Assurance Scope Validation
    if not validate_quality_assurance_scope(task_body):
        raise ConstraintViolation("Invalid quality assurance scope")
    
    return task_body
```

### OUT Scope (Universal)
- Primary content creation and production ❌
- Technical platform development and implementation ❌
- Original media asset creation and design ❌
- Software engineering and system architecture ❌
- Platform infrastructure and technical operations ❌

### Quality Assurance Constraints
- Quality assessment and evaluation only
- Cross-media consistency verification and optimization
- Performance monitoring and improvement recommendations
- Quality standard development and compliance enforcement
- Modern quality assurance best practices

### Mode-Specific Constraints
**VISUAL_QA**: Visual quality assessment only, no design creation
**TEXT_QA**: Text quality evaluation only, no content writing
**INTERACTIVE_QA**: Interactive quality testing only, no UX design
**VIDEO_QA**: Video quality assessment only, no production
**UNIFIED_QA**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- Quality standards compliance and best practices
- Cross-media consistency and brand alignment
- User experience and accessibility standards
- Ethical quality assessment and cultural sensitivity
- Continuous improvement and excellence standards
<!-- END_BLOCK -->
