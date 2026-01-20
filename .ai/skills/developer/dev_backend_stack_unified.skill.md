[Optimized: 2026-01-19]

# Dev Backend Stack Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified backend development stack with intelligent technology switching
- Node.js runtime, API frameworks, and middleware integration
- Single entry point for all backend development needs with automatic technology detection
- **Scope**: Comprehensive backend stack engine that replaces 3 specialized backend skills with intelligent routing
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- API specifications & business logic requirements
- Database schemas & data models
- Performance & scalability requirements
- Security & authentication specifications

### Output
**Unified Output Schema**:
- Node.js server architecture & API implementations
- API framework implementations & documentation
- Middleware configurations & security setups
- Database integration code & optimized endpoints
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Technology Detection Engine
```python
def detect_backend_mode(input_data, keywords):
    """Intelligent technology switching based on backend development needs"""
    
    # NodeJS Runtime Mode
    if any(kw in keywords.lower() for kw in ['nodejs', 'runtime', 'event', 'async', 'server']):
        return 'NODEJS_RUNTIME'
    
    # API Frameworks Mode  
    elif any(kw in keywords.lower() for kw in ['api', 'framework', 'rest', 'graphql', 'endpoint']):
        return 'API_FRAMEWORKS'
        
    # Middleware Mode
    elif any(kw in keywords.lower() for kw in ['middleware', 'auth', 'logging', 'error', 'security']):
        return 'MIDDLEWARE'
        
    # Unified Backend Mode (default)
    else:
        return 'UNIFIED_BACKEND'
```

### Unified Backend Stack Pipeline

#### Phase 1: Requirements Analysis & Architecture
1. API specifications & business logic analysis
2. Database schema & data model review
3. Performance & scalability requirements assessment
4. Security & authentication requirements definition

#### Phase 2: Mode-Specific Implementation

**NODEJS_RUNTIME Mode**:
- Node.js-based backend development
- Event-driven architecture design
- Scalable server application implementation
- Async processing & event loop optimization

**API_FRAMEWORKS Mode**:
- API framework design & implementation
- RESTful/GraphQL API development
- API documentation & test automation
- Framework selection & configuration

**MIDDLEWARE Mode**:
- Authentication, logging, error handling middleware
- Request/response processing & validation
- Security middleware & CORS configuration
- Custom middleware development & integration

**UNIFIED_BACKEND Mode**:
- Comprehensive backend stack implementation
- Integrated Node.js + API framework + middleware
- End-to-end backend architecture development
- Full-stack backend optimization

#### Phase 3: API Development & Integration
1. API endpoint implementation & testing
2. Database integration & data modeling
3. Middleware configuration & security setup
4. Performance optimization & scaling preparation

#### Phase 4: Testing & Documentation
1. API testing & validation
2. Documentation generation & schema definition
3. Performance testing & optimization
4. Security testing & vulnerability assessment

### Level-Specific Execution

#### Junior Backend Developer (L1)
- Basic Node.js server implementation
- Simple API endpoint development
- Standard middleware usage
- Basic database integration

#### Senior Backend Developer (L2)
- Advanced Node.js architecture & optimization
- Complex API framework design & implementation
- Custom middleware development & security
- Backend architecture leadership & scaling
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Node.js runtime & JavaScript/TypeScript
- API frameworks (Express, Fastify, Koa, NestJS)
- Database systems (SQL, NoSQL, ORMs)
- Authentication & security libraries
- Testing frameworks & API documentation tools
- Performance monitoring & optimization tools
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Backend Development Protection
```python
def enforce_backend_stack_isolation(task_content):
    """Physical isolation of frontend concerns in backend development"""
    
    # 1. Frontend Concern Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Frontend Pattern Detection
    forbidden_patterns = [
        r'\b(frontend|ui|ux|css|html|react)\b',
        r'\b(browser|client|dom|styling|responsive)\b',
        r'\b(component|jsx|hooks|state\s+management)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Frontend concern detected in backend stack")
    
    # 3. Backend Scope Validation
    if not validate_backend_scope(task_body):
        raise ConstraintViolation("Invalid backend development scope")
    
    return task_body
```

### OUT Scope (Universal)
- Frontend development & UI implementation ❌
- Database administration & infrastructure ❌
- DevOps & deployment management ❌
- UI/UX design & user experience ❌
- Client-side optimization & browser compatibility ❌

### Backend Stack Constraints
- Backend-only development & server-side logic
- API development & data processing
- Security & authentication implementation
- Performance optimization & scalability
- Modern backend best practices & patterns

### Mode-Specific Constraints
**NODEJS_RUNTIME**: Node.js ecosystem only, no other runtimes
**API_FRAMEWORKS**: API development only, no business logic
**MIDDLEWARE**: Middleware logic only, no endpoint implementation
**UNIFIED_BACKEND**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- API standards compliance (REST, GraphQL)
- Security best practices & data protection
- Performance optimization & scalability
- Code quality & maintainability
- Modern backend architecture patterns
<!-- END_BLOCK -->
