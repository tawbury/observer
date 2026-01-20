[Optimized: 2026-01-19]

# Media Integration Framework Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Cross-media integration & synergy optimization strategies
- Multi-platform content adaptation & consistency maintenance
- Brand coherence across diverse media types & channels
- **Scope**: Advanced integration framework that enables seamless cross-media collaboration while preserving individual media specialization and quality standards
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Multi-media content assets & specifications
- Platform requirements & technical constraints
- Brand guidelines & consistency standards
- Integration objectives & synergy goals

### Output
**Unified Output Schema**:
- Cross-media integration strategies & implementation plans
- Multi-platform adaptation guidelines & standards
- Brand consistency frameworks & quality assurance
- Synergy optimization reports & performance metrics
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Integration Detection Engine
```python
def detect_integration_mode(input_data, keywords):
    """Intelligent integration switching based on media synergy needs"""
    
    # Visual-Text Integration Mode
    if any(kw in keywords.lower() for kw in ['visual-text', 'image-text', 'design-content', 'brand-content']):
        return 'VISUAL_TEXT_INTEGRATION'
    
    # Interactive-Visual Integration Mode  
    elif any(kw in keywords.lower() for kw in ['interactive-visual', 'ux-design', 'prototype-visual', 'interface-design']):
        return 'INTERACTIVE_VISUAL_INTEGRATION'
        
    # Video-Business Integration Mode
    elif any(kw in keywords.lower() for kw in ['video-business', 'content-marketing', 'video-strategy', 'media-business']):
        return 'VIDEO_BUSINESS_INTEGRATION'
        
    # Cross-Platform Integration Mode
    elif any(kw in keywords.lower() for kw in ['cross-platform', 'multi-platform', 'platform-adaptation', 'media-distribution']):
        return 'CROSS_PLATFORM_INTEGRATION'
        
    # Holistic Integration Mode (default)
    else:
        return 'HOLISTIC_INTEGRATION'
```

### Universal Media Integration Pipeline

#### Phase 1: Integration Analysis & Planning
1. Multi-media content asset analysis & compatibility assessment
2. Platform requirement evaluation & technical constraint identification
3. Brand guideline review & consistency standard establishment
4. Integration objective definition & synergy goal setting

#### Phase 2: Mode-Specific Integration Strategies

**VISUAL_TEXT_INTEGRATION Mode**:
- Visual-text content harmony & coherence optimization
- Brand identity consistency across visual and textual elements
- Typography and visual hierarchy alignment strategies
- Cross-format content adaptation and seamless integration

**INTERACTIVE_VISUAL_INTEGRATION Mode**:
- UX/UI design and visual asset synchronization
- Interactive prototype and visual design integration
- User experience consistency across interactive and visual elements
- Cross-platform interactive-visual adaptation strategies

**VIDEO_BUSINESS_INTEGRATION Mode**:
- Video content and business strategy alignment
- Marketing message and visual narrative integration
- Brand storytelling through video-business synergy
- Multi-channel video distribution and business impact optimization

**CROSS_PLATFORM_INTEGRATION Mode**:
- Multi-platform content adaptation and optimization
- Platform-specific technical requirements and constraints management
- Brand consistency maintenance across diverse platforms
- Cross-platform user experience and engagement optimization

**HOLISTIC_INTEGRATION Mode**:
- Comprehensive cross-media integration strategy
- End-to-end multi-platform content ecosystem
- Holistic brand experience and synergy optimization
- Integrated performance measurement and optimization

#### Phase 3: Implementation & Coordination
1. Cross-media asset integration and technical coordination
2. Platform-specific adaptation and quality assurance
3. Brand consistency enforcement and guideline compliance
4. Integration testing and performance validation

#### Phase 4: Optimization & Performance
1. Cross-media synergy measurement and optimization
2. Platform performance monitoring and enhancement
3. Brand consistency evaluation and improvement
4. Integration effectiveness assessment and refinement

### Level-Specific Execution

#### Junior Integration Specialist (L1)
- Basic cross-media integration and coordination
- Standard platform adaptation and quality assurance
- Template-based integration strategies
- Basic performance monitoring and optimization

#### Senior Integration Specialist (L2)
- Advanced cross-media synergy optimization
- Complex multi-platform integration strategies
- Custom integration framework development
- Strategic integration leadership and innovation
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Cross-media content management systems
- Multi-platform publishing and distribution platforms
- Brand management and consistency monitoring tools
- Integration testing and quality assurance frameworks
- Performance analytics and optimization platforms
- Collaboration tools and workflow management systems
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Media Integration Protection
```python
def enforce_media_integration_isolation(task_content):
    """Physical isolation of content creation in media integration"""
    
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
            raise ConstraintViolation("Content creation detected in media integration")
    
    # 3. Media Integration Scope Validation
    if not validate_media_integration_scope(task_body):
        raise ConstraintViolation("Invalid media integration scope")
    
    return task_body
```

### OUT Scope (Universal)
- Primary content creation and production ❌
- Technical platform development and implementation ❌
- Software engineering and system architecture ❌
- Original media asset creation and design ❌
- Platform infrastructure and technical operations ❌

### Media Integration Constraints
- Integration and coordination only
- Cross-media synergy optimization
- Brand consistency maintenance
- Platform adaptation and distribution
- Modern integration best practices

### Mode-Specific Constraints
**VISUAL_TEXT_INTEGRATION**: Visual-text coordination only, no content creation
**INTERACTIVE_VISUAL_INTEGRATION**: Interactive-visual alignment only, no design
**VIDEO_BUSINESS_INTEGRATION**: Video-business strategy only, no production
**CROSS_PLATFORM_INTEGRATION**: Platform adaptation only, no development
**HOLISTIC_INTEGRATION**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- Integration quality standards and best practices
- Cross-media consistency and brand alignment
- Platform compliance and technical standards
- User experience and engagement optimization
- Ethical integration and cultural sensitivity
<!-- END_BLOCK -->
