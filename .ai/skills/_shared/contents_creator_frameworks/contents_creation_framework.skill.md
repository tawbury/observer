[Optimized: 2026-01-19]

# Contents Creation Framework Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Universal contents creation principles & methodologies
- Cross-media consistency & quality standards enforcement
- Contents lifecycle management & optimization strategies
- **Scope**: Foundational framework that provides universal creation principles applicable across all media types while maintaining media-specific specialization
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- Contents requirements & objectives
- Target audience specifications & platform constraints
- Media type specifications & technical requirements
- Quality standards & brand guidelines

### Output
**Unified Output Schema**:
- Contents creation methodologies & best practices
- Cross-media consistency guidelines & standards
- Quality assurance frameworks & evaluation criteria
- Lifecycle management strategies & optimization plans
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Media Detection Engine
```python
def detect_contents_mode(input_data, keywords):
    """Intelligent media switching based on contents creation needs"""
    
    # Visual Creation Mode
    if any(kw in keywords.lower() for kw in ['visual', 'image', 'design', 'graphic', 'brand', '3d', 'motion']):
        return 'VISUAL_CREATION'
    
    # Text Creation Mode  
    elif any(kw in keywords.lower() for kw in ['text', 'writing', 'ebook', 'content', 'article', 'story']):
        return 'TEXT_CREATION'
        
    # Interactive Design Mode
    elif any(kw in keywords.lower() for kw in ['interactive', 'ux', 'ui', 'prototype', 'wireframe', 'user']):
        return 'INTERACTIVE_DESIGN'
        
    # Video Production Mode
    elif any(kw in keywords.lower() for kw in ['video', 'film', 'animation', 'editing', 'storyboard']):
        return 'VIDEO_PRODUCTION'
        
    # Business Strategy Mode
    elif any(kw in keywords.lower() for kw in ['marketing', 'business', 'strategy', 'monetization', 'audience']):
        return 'BUSINESS_STRATEGY'
        
    # Unified Creation Mode (default)
    else:
        return 'UNIFIED_CREATION'
```

### Universal Contents Creation Pipeline

#### Phase 1: Requirements Analysis & Planning
1. Contents requirements analysis & objective definition
2. Target audience specification & platform constraint evaluation
3. Media type assessment & technical requirement identification
4. Quality standards establishment & brand guideline alignment

#### Phase 2: Mode-Specific Creation Methodology

**VISUAL_CREATION Mode**:
- Visual design principles & composition fundamentals
- Color theory, typography, and visual hierarchy application
- Brand consistency & visual identity maintenance
- Cross-platform visual adaptation & optimization

**TEXT_CREATION Mode**:
- Writing fundamentals & content structure principles
- Audience-appropriate tone & style guidelines
- Content optimization & readability standards
- Cross-format text adaptation & localization

**INTERACTIVE_DESIGN Mode**:
- User experience principles & interaction design fundamentals
- Usability standards & accessibility compliance
- Prototyping methodologies & user testing frameworks
- Cross-platform interactive design consistency

**VIDEO_PRODUCTION Mode**:
- Visual storytelling principles & narrative structure
- Video production workflows & quality standards
- Cross-format video adaptation & platform optimization
- Audio-visual synchronization & technical standards

**BUSINESS_STRATEGY Mode**:
- Contents strategy development & market positioning
- Audience development & engagement optimization
- Monetization strategies & revenue optimization
- Cross-platform business model alignment

**UNIFIED_CREATION Mode**:
- Comprehensive contents creation methodology
- Integrated cross-media creation strategies
- Holistic quality assurance & optimization
- End-to-end contents lifecycle management

#### Phase 3: Quality Assurance & Standards
1. Universal quality standards application & evaluation
2. Cross-media consistency verification & validation
3. Brand guideline compliance & identity maintenance
4. Performance measurement & optimization implementation

#### Phase 4: Lifecycle Management & Optimization
1. Contents performance monitoring & analytics
2. Audience engagement tracking & optimization
3. Cross-media synergy evaluation & enhancement
4. Continuous improvement & strategy refinement

### Level-Specific Execution

#### Junior Contents Creator (L1)
- Basic creation principles & standard methodologies
- Template-based content creation & quality assurance
- Cross-media consistency maintenance
- Basic performance monitoring & optimization

#### Senior Contents Creator (L2)
- Advanced creation strategies & innovative methodologies
- Custom framework development & quality standard establishment
- Cross-media synergy optimization & strategic alignment
- Leadership in contents creation excellence & innovation
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Universal content management systems & platforms
- Cross-media design tools & creation software
- Quality assurance frameworks & testing tools
- Analytics platforms & performance monitoring systems
- Brand management systems & guideline repositories
- Collaboration tools & workflow management platforms
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Contents Creation Protection
```python
def enforce_contents_creation_isolation(task_content):
    """Physical isolation of technical implementation in contents creation"""
    
    # 1. Technical Implementation Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Technical Pattern Detection
    forbidden_patterns = [
        r'\b(development|coding|programming|technical\s+implementation)\b',
        r'\b(backend|frontend|database|api|infrastructure)\b',
        r'\b(deployment|testing|debugging|engineering)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Technical implementation detected in contents creation")
    
    # 3. Contents Creation Scope Validation
    if not validate_contents_creation_scope(task_body):
        raise ConstraintViolation("Invalid contents creation scope")
    
    return task_body
```

### OUT Scope (Universal)
- Technical development & software implementation ❌
- Engineering decisions & system architecture ❌
- Database management & infrastructure operations ❌
- Code development & deployment processes ❌
- DevOps & technical maintenance ❌

### Contents Creation Constraints
- Contents creation & media production only
- Cross-media consistency & quality standards
- Brand identity maintenance & strategic alignment
- Audience engagement & value delivery
- Modern contents creation best practices

### Mode-Specific Constraints
**VISUAL_CREATION**: Visual media only, no technical implementation
**TEXT_CREATION**: Text content only, no platform development
**INTERACTIVE_DESIGN**: User experience only, no system design
**VIDEO_PRODUCTION**: Video media only, no streaming infrastructure
**BUSINESS_STRATEGY**: Business strategy only, no financial implementation
**UNIFIED_CREATION**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- Contents quality standards & best practices
- Cross-media consistency & brand alignment
- Audience-centric approach & value proposition
- Ethical content creation & cultural sensitivity
- Innovation & creative excellence standards
<!-- END_BLOCK -->
