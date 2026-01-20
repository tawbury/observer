[Optimized: 2026-01-19]

# Dev DevOps Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified DevOps operations with intelligent service switching
- System monitoring, serverless architecture, and autoscaling integration
- Single entry point for all DevOps needs with automatic service detection
- **Scope**: Comprehensive DevOps engine that replaces 3 specialized operations skills with intelligent routing
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Service Detection Engine
```python
def detect_devops_mode(input_data, keywords):
    """Intelligent service switching based on DevOps needs"""
    
    # Monitoring Mode
    if any(kw in keywords.lower() for kw in ['monitoring', 'logging', 'alerting', 'dashboard', 'metrics']):
        return 'MONITORING'
    
    # Serverless Mode  
    elif any(kw in keywords.lower() for kw in ['serverless', 'lambda', 'function', 'event', 'faas']):
        return 'SERVERLESS'
        
    # Autoscaling Mode
    elif any(kw in keywords.lower() for kw in ['autoscaling', 'scaling', 'elastic', 'load', 'capacity']):
        return 'AUTOSCALING'
        
    # Unified DevOps Mode (default)
    else:
        return 'UNIFIED_DEVOPS'
```

### Unified DevOps Pipeline

#### Phase 1: Operations Analysis & Planning
1. System architecture analysis & service level objectives definition
2. Business importance assessment & operating policy review
3. Event-driven requirements & scalability analysis
4. Monitoring, logging, and alerting requirements assessment

#### Phase 2: Mode-Specific Implementation

**MONITORING Mode**:
- System monitoring architecture design & construction
- Log collection & analysis system implementation
- Alerting & incident response automation
- Metrics collection strategies & dashboard design

**SERVERLESS Mode**:
- Serverless architecture design & implementation
- Event-driven system development
- FaaS (Function as a Service) utilization
- Serverless function implementation & event pipeline design

**AUTOSCALING Mode**:
- Autoscaling strategy design & implementation
- Elastic resource management & capacity planning
- Load-based scaling & performance optimization
- Cost-effective scaling policies & resource optimization

**UNIFIED_DEVOPS Mode**:
- Comprehensive DevOps operations implementation
- Integrated monitoring + serverless + autoscaling
- End-to-end operations architecture development
- Full-stack DevOps optimization & automation

#### Phase 3: Operations Implementation
1. Monitoring systems setup & alerting configuration
2. Serverless functions deployment & event pipeline implementation
3. Autoscaling policies configuration & resource management
4. Incident response procedures & operational automation

#### Phase 4: Optimization & Automation
1. Performance monitoring & optimization
2. Cost optimization & resource efficiency
3. Automation enhancement & operational excellence
4. Continuous improvement & operational maturity

### Level-Specific Execution

#### Junior DevOps Engineer (L1)
- Basic monitoring setup & alerting configuration
- Simple serverless function deployment
- Standard autoscaling policy implementation
- Basic operational automation

#### Senior DevOps Engineer (L2)
- Advanced monitoring architecture & observability
- Complex serverless architecture & event-driven systems
- Sophisticated autoscaling strategies & cost optimization
- DevOps leadership & operational excellence
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- System architecture definitions & service level objectives
- Business importance definitions & operating policies
- Event specifications & scalability requirements
- Monitoring, logging, and alerting requirements

### Output
**Unified Output Schema**:
- Monitoring dashboards & log collection pipelines
- Serverless functions & event pipeline designs
- Autoscaling configurations & resource management strategies
- Incident response procedures & operational automation
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Monitoring platforms (Prometheus, Grafana, ELK stack)
- Serverless platforms (AWS Lambda, Azure Functions, Google Cloud Functions)
- Autoscaling services & load balancers
- Container orchestration platforms (Kubernetes)
- Infrastructure as Code tools (Terraform, CloudFormation)
- CI/CD pipelines & automation tools
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced DevOps Protection
```python
def enforce_devops_isolation(task_content):
    """Physical isolation of application development in DevOps"""
    
    # 1. Application Development Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Application Pattern Detection
    forbidden_patterns = [
        r'\b(frontend|backend|api|endpoint|application\s+code)\b',
        r'\b(ui|ux|user\s+interface|business\s+logic)\b',
        r'\b(database|query|data\s+model|schema)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Application development detected in DevOps")
    
    # 3. DevOps Scope Validation
    if not validate_devops_scope(task_body):
        raise ConstraintViolation("Invalid DevOps scope")
    
    return task_body
```

### OUT Scope (Universal)
- Application development & business logic ❌
- Frontend/backend implementation & API development ❌
- Database design & data modeling ❌
- User interface & user experience ❌
- Application-specific features & functionality ❌

### DevOps Constraints
- Operations & infrastructure management only
- Monitoring, logging, and alerting systems
- Serverless architecture & event-driven systems
- Autoscaling & resource management
- Modern DevOps best practices & automation

### Mode-Specific Constraints
**MONITORING**: Monitoring systems only, no application code
**SERVERLESS**: Serverless functions only, no business logic
**AUTOSCALING**: Resource scaling only, no application features
**UNIFIED_DEVOPS**: Combined constraints with enhanced scope protection

### Quality & Standards Constraints
- DevOps standards compliance & best practices
- Reliability & availability requirements
- Security & compliance in operations
- Cost optimization & resource efficiency
- Modern operational excellence patterns
<!-- END_BLOCK -->
