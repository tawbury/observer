[Optimized: 2026-01-19]

# Contents Strategy Framework Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Strategic contents planning and roadmap management across all media types
- Audience development and engagement optimization strategies
- Cross-media strategy alignment and business objective integration
- **Scope**: Strategic framework that provides comprehensive content strategy development, audience optimization, and cross-media alignment while enabling media-specific strategic execution
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Business objectives and strategic goals
- Target audience specifications and market analysis
- Content performance metrics and engagement data
- Platform requirements and distribution strategies

### Output
**Unified Output Schema**:
- Content strategies and roadmap development plans
- Audience development and engagement optimization strategies
- Cross-media alignment frameworks and execution plans
- Performance measurement and strategic optimization recommendations
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Strategy Detection Engine
```python
def detect_strategy_mode(input_data, keywords):
    """Intelligent strategy switching based on strategic needs"""
    
    # Audience Strategy Mode
    if any(kw in keywords.lower() for kw in ['audience', 'user', 'reader', 'viewer', 'engagement']):
        return 'AUDIENCE_STRATEGY'
    
    # Platform Strategy Mode  
    elif any(kw in keywords.lower() for kw in ['platform', 'channel', 'distribution', 'publishing', 'media']):
        return 'PLATFORM_STRATEGY'
        
    # Monetization Strategy Mode
    elif any(kw in keywords.lower() for kw in ['monetization', 'revenue', 'business', 'profit', 'commercial']):
        return 'MONETIZATION_STRATEGY'
        
    # Growth Strategy Mode
    elif any(kw in keywords.lower() for kw in ['growth', 'scale', 'expansion', 'reach', 'market']):
        return 'GROWTH_STRATEGY'
        
    # Integrated Strategy Mode (default)
    else:
        return 'INTEGRATED_STRATEGY'
```

### Universal Contents Strategy Pipeline

#### Phase 1: Strategic Analysis & Planning
1. Business objective analysis and strategic goal identification
2. Target audience specification and market landscape evaluation
3. Content performance assessment and competitive analysis
4. Platform requirement evaluation and distribution strategy planning

#### Phase 2: Mode-Specific Strategy Development

**AUDIENCE_STRATEGY Mode**:
- Audience development and engagement optimization strategies
- User persona development and audience segmentation
- Content personalization and experience optimization
- Cross-media audience journey and engagement mapping

**PLATFORM_STRATEGY Mode**:
- Multi-platform content distribution and optimization strategies
- Platform-specific content adaptation and technical requirements
- Cross-platform consistency and brand alignment strategies
- Platform performance monitoring and optimization frameworks

**MONETIZATION_STRATEGY Mode**:
- Content monetization strategies and revenue optimization
- Business model development and commercial viability assessment
- Cross-media revenue streams and profit optimization
- Market positioning and competitive advantage strategies

**GROWTH_STRATEGY Mode**:
- Content growth strategies and market expansion plans
- Audience scaling and reach optimization strategies
- Cross-media growth synergies and expansion opportunities
- Performance-based growth optimization and scaling frameworks

**INTEGRATED_STRATEGY Mode**:
- Comprehensive cross-media content strategy development
- Integrated audience-platform-monetization-growth alignment
- Holistic business objective and content strategy integration
- End-to-end strategic planning and execution optimization

#### Phase 3: Strategy Implementation & Execution
1. Cross-media strategy implementation and coordination
2. Platform-specific execution and performance monitoring
3. Audience engagement tracking and optimization
4. Business objective alignment and strategic adjustment

#### Phase 4: Performance Measurement & Optimization
1. Strategy performance measurement and KPI tracking
2. Cross-media synergy evaluation and optimization
3. Audience engagement analysis and improvement
4. Strategic refinement and continuous improvement

### Level-Specific Execution

#### Junior Content Strategist (L1)
- Basic strategy development and standard planning
- Template-based strategic frameworks and execution
- Cross-media coordination and basic optimization
- Strategy reporting and documentation

#### Senior Content Strategist (L2)
- Advanced strategic planning and custom framework development
- Complex cross-media strategy optimization and innovation
- Strategic leadership and business alignment
- Strategy excellence and continuous improvement programs
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Strategy planning and management platforms
- Audience analytics and engagement monitoring tools
- Content performance measurement and optimization systems
- Cross-platform distribution and management platforms
- Business intelligence and strategic analytics tools
- Collaboration and workflow management systems
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Contents Strategy Protection
```python
def enforce_contents_strategy_isolation(task_content):
    """Physical isolation of content creation in strategy development"""
    
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
            raise ConstraintViolation("Content creation detected in strategy development")
    
    # 3. Contents Strategy Scope Validation
    if not validate_contents_strategy_scope(task_body):
        raise ConstraintViolation("Invalid contents strategy scope")
    
    return task_body
```

### OUT Scope (Universal)
- Primary content creation and production ❌
- Technical platform development and implementation ❌
- Original media asset creation and design ❌
- Software engineering and system architecture ❌
- Financial management and budget execution ❌

### Contents Strategy Constraints
- Strategy development and planning only
- Audience analysis and engagement optimization
- Platform strategy and distribution planning
- Business alignment and objective integration
- Modern strategic planning best practices

### Mode-Specific Constraints
**AUDIENCE_STRATEGY**: Audience strategy only, no content creation
**PLATFORM_STRATEGY**: Platform strategy only, no technical development
**MONETIZATION_STRATEGY**: Monetization strategy only, no financial execution
**GROWTH_STRATEGY**: Growth strategy only, no operational implementation
**INTEGRATED_STRATEGY**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- Strategic planning standards and best practices
- Audience-centric approach and value alignment
- Business objective integration and strategic coherence
- Ethical strategy development and cultural sensitivity
- Innovation and strategic excellence standards
<!-- END_BLOCK -->
