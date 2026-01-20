[Optimized: 2026-01-19]

# Dev Frontend Stack Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified frontend development stack with intelligent technology switching
- Frontend implementation, React specialization, state management, and build optimization
- Single entry point for all frontend development needs with automatic technology detection
- **Scope**: Comprehensive frontend stack engine that replaces 4 specialized frontend skills with intelligent routing
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- UI/UX design specifications & screen designs
- User requirements & API specifications
- Brand guidelines & performance requirements
- Technology preferences & constraints

### Output
**Unified Output Schema**:
- Frontend implementation plans & component architecture
- React component architecture & state management design
- Build configurations & optimized frontend code
- Routing design & user interface implementation
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Technology Detection Engine
```python
def detect_frontend_mode(input_data, keywords):
    """Intelligent technology switching based on frontend development needs"""
    
    # Basic Frontend Mode
    if any(kw in keywords.lower() for kw in ['basic', 'html', 'css', 'vanilla', 'simple']):
        return 'BASIC_FRONTEND'
    
    # React Specialization Mode  
    elif any(kw in keywords.lower() for kw in ['react', 'component', 'jsx', 'hooks']):
        return 'REACT_SPECIALIZATION'
        
    # State Management Mode
    elif any(kw in keywords.lower() for kw in ['state', 'redux', 'zustand', 'context', 'store']):
        return 'STATE_MANAGEMENT'
        
    # Build Tools Mode
    elif any(kw in keywords.lower() for kw in ['build', 'webpack', 'vite', 'bundle', 'optimize']):
        return 'BUILD_TOOLS'
        
    # Unified Frontend Mode (default)
    else:
        return 'UNIFIED_FRONTEND'
```

### Unified Frontend Stack Pipeline

#### Phase 1: Requirements Analysis & Planning
1. UI/UX design specifications analysis
2. User requirements & API specifications review
3. Technology stack assessment & selection
4. Performance & accessibility requirements definition

#### Phase 2: Mode-Specific Implementation

**BASIC_FRONTEND Mode**:
- Responsive/accessibility/intuitive UI development
- Client-side development & UI implementation
- Basic UX optimization & browser compatibility
- Standard HTML/CSS/JavaScript implementation

**REACT_SPECIALIZATION Mode**:
- React-based frontend development
- Component-based architecture design
- Modern frontend optimization & performance enhancement
- JSX, hooks, and React patterns implementation

**STATE_MANAGEMENT Mode**:
- Frontend state management design & implementation
- Complex state logic management
- Predictable state update architecture
- Redux, Zustand, or Context API integration

**BUILD_TOOLS Mode**:
- Frontend build system design & construction
- Code bundling & optimization
- Development & deployment environment automation
- Webpack/Vite configuration & build optimization

**UNIFIED_FRONTEND Mode**:
- Comprehensive frontend stack implementation
- Integrated React + state management + build pipeline
- End-to-end frontend architecture development
- Full-stack frontend optimization

#### Phase 3: Architecture & Implementation
1. Component architecture design & implementation
2. State management strategy development
3. Routing design & navigation structure
4. Build configuration & optimization setup

#### Phase 4: Optimization & Deployment
1. Performance optimization & enhancement
2. Accessibility compliance & testing
3. Build optimization & asset management
4. Deployment-ready artifact generation

### Level-Specific Execution

#### Junior Frontend Developer (L1)
- Basic frontend implementation & UI development
- Simple component creation & styling
- Standard build tool usage
- Basic responsive design implementation

#### Senior Frontend Developer (L2)
- Advanced React architecture & state management
- Complex build system optimization
- Performance enhancement & accessibility
- Frontend architecture leadership & mentoring
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Frontend development frameworks (React, Vue, Angular)
- State management libraries (Redux, Zustand, Context API)
- Build tools & bundlers (Webpack, Vite, Rollup)
- CSS preprocessors & styling frameworks
- Testing frameworks & accessibility tools
- Performance monitoring & optimization tools
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Frontend Development Protection
```python
def enforce_frontend_stack_isolation(task_content):
    """Physical isolation of technology conflicts in frontend development"""
    
    # 1. Technology Conflict Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Technology Pattern Detection
    forbidden_patterns = [
        r'\b(backend|server|database|api\s+server)\b',
        r'\b(deployment|infrastructure|devops)\b',
        r'\b(security\s+backend|authentication\s+server)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Backend technology detected in frontend stack")
    
    # 3. Frontend Scope Validation
    if not validate_frontend_scope(task_body):
        raise ConstraintViolation("Invalid frontend development scope")
    
    return task_body
```

### OUT Scope (Universal)
- Backend development & server-side logic ❌
- Database design & management ❌
- Infrastructure & deployment management ❌
- Backend security & authentication ❌
- DevOps & operations ❌

### Frontend Stack Constraints
- Frontend-only development & implementation
- UI/UX focus & user experience optimization
- Client-side performance & accessibility
- Responsive design & cross-browser compatibility
- Modern frontend best practices & standards

### Mode-Specific Constraints
**BASIC_FRONTEND**: No complex frameworks, vanilla web technologies only
**REACT_SPECIALIZATION**: React ecosystem only, no other frameworks
**STATE_MANAGEMENT**: State logic only, no UI implementation
**BUILD_TOOLS**: Build optimization only, no application logic
**UNIFIED_FRONTEND**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- Web standards compliance & accessibility
- Performance optimization & best practices
- Code quality & maintainability
- Cross-browser compatibility & responsive design
- Modern frontend architecture patterns
<!-- END_BLOCK -->
