[Optimized: 2026-01-19]

# HR Context Intelligence Unified Skill

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Unified context intelligence with read-only system awareness
- Agent-Role-Skill relationship observation, inventory management, and gap recognition
- Single entry point for all context intelligence needs with automatic domain detection
- **Scope**: Comprehensive context intelligence engine that replaces 3 specialized read-only skills with intelligent routing
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
**Universal Input Schema**:
- System structure data (agent definitions, skill mappings, role relationships)
- Configuration information (skill catalogs, agent-skill mappings, role requirements)
- Analysis parameters (scope, depth, focus areas)
- Context requirements (visibility level, reporting format)

### Output
**Unified Output Schema**:
- System structure relationship maps & analysis
- Skill inventory catalogs & availability reports
- Gap identification reports & inconsistency lists
- System configuration visibility & ecosystem status
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic

### Mode Detection Engine
```python
def detect_context_mode(input_data, keywords):
    """Intelligent mode switching based on context intelligence needs"""
    
    # Context Awareness Mode
    if any(kw in keywords.lower() for kw in ['structure', 'relationship', 'mapping', 'system', 'agent']):
        return 'CONTEXT_AWARENESS'
    
    # Skill Inventory Mode  
    elif any(kw in keywords.lower() for kw in ['inventory', 'catalog', 'list', 'available', 'skill']):
        return 'SKILL_INVENTORY'
        
    # Gap Recognition Mode
    elif any(kw in keywords.lower() for kw in ['gap', 'missing', 'inconsistency', 'coverage', 'alignment']):
        return 'GAP_RECOGNITION'
        
    # Unified Mode (default)
    else:
        return 'UNIFIED'
```

### Unified Context Intelligence Pipeline

#### Phase 1: System Structure Analysis
1. Agent definition file scanning & structure analysis
2. Skill mapping relationship extraction & organization
3. Role-Skill correlation identification
4. System configuration visibility generation

#### Phase 2: Mode-Specific Processing

**CONTEXT_AWARENESS Mode**:
- Agent-Role-Skill relationship mapping
- System structure visualization & analysis
- Ecosystem status awareness & reporting
- Structure relationship consistency verification

**SKILL_INVENTORY Mode**:
- Skill definition file scanning & listing
- Skill category identification & classification
- Responsibility scope analysis & characteristic extraction
- Skill availability tracking & monitoring

**GAP_RECOGNITION Mode**:
- Role requirements vs skill definitions comparison
- Missing skill identification & listing
- Scope inconsistency detection & classification
- Definition inconsistency awareness & reporting

**UNIFIED Mode**:
- Comprehensive system structure analysis
- Complete skill inventory management
- Integrated gap recognition & reporting
- Holistic context intelligence synthesis

#### Phase 3: Analysis & Synthesis
1. Structure relationship consistency verification
2. Skill characteristic cataloging & classification
3. Missing skill identification & impact analysis
4. System configuration optimization recommendations

#### Phase 4: Reporting & Visualization
1. Relationship maps & structure diagrams
2. Inventory catalogs & availability reports
3. Gap analysis reports & inconsistency lists
4. Ecosystem status summaries & insights

### Read-Only Enforcement Protocol
```python
def enforce_readonly_access(operation):
    """Strict read-only access enforcement for all context intelligence operations"""
    
    readonly_operations = [
        'scan', 'analyze', 'identify', 'extract', 'observe',
        'verify', 'catalog', 'classify', 'track', 'monitor'
    ]
    
    forbidden_operations = [
        'create', 'modify', 'delete', 'update', 'change',
        'allocate', 'recommend', 'decide', 'execute', 'implement'
    ]
    
    if any(op in operation.lower() for op in forbidden_operations):
        raise ConstraintViolation("Write operation detected in read-only context intelligence")
    
    return operation
```

### Level-Specific Execution

#### Junior Analyst (L1)
- Basic system structure scanning
- Simple skill inventory listing
- Standard gap identification
- Basic report generation

#### Senior Analyst (L2)
- Advanced relationship analysis
- Complex structure visualization
- Strategic gap assessment
- Comprehensive system insights
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- File system access permissions (read-only)
- Markdown parsing & analysis tools
- Relationship analysis & mapping algorithms
- Structure visualization & diagramming tools
- Inventory management & tracking systems
- Gap analysis & comparison frameworks
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints

### Enhanced Read-Only Protection
```python
def enforce_context_intelligence_isolation(task_content):
    """Physical isolation of write operations in context intelligence"""
    
    # 1. Write Operation Detection
    task_body = extract_body_content(task_content)
    
    # 2. Forbidden Write Pattern Detection
    forbidden_patterns = [
        r'\b(create|modify|delete|update|change|allocate)\b',
        r'\b(recommend|decide|execute|implement|manage)\b',
        r'\b(approve|reject|assign|deploy|configure)\b'
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, task_body, re.IGNORECASE):
            raise ConstraintViolation("Write operation detected in read-only context intelligence")
    
    # 3. Read-Only Scope Validation
    if not validate_readonly_scope(task_body):
        raise ConstraintViolation("Invalid read-only scope in context intelligence")
    
    return task_body
```

### OUT Scope (Universal)
- Agent definition creation/modification ❌
- Skill mapping changes or modifications ❌
- Role requirements changes or updates ❌
- System configuration modifications ❌
- Decision-making, judgment, or recommendations ❌
- Gap resolution or filling actions ❌

### Context Intelligence Constraints
- Read-only access only permitted
- Structure relationship observation only
- Judgment/execution complete separation
- No side effects or system changes
- Objective analysis & reporting only

### Mode-Specific Constraints
**CONTEXT_AWARENESS**: No system modifications, observation only
**SKILL_INVENTORY**: No skill creation/modification, cataloging only
**GAP_RECOGNITION**: No gap resolution, identification only
**UNIFIED**: Combined read-only constraints with enhanced protection

### Analysis Constraints
- Objective criteria application only
- No subjective interpretation or bias
- Evidence-based analysis & reporting
- Complete separation from decision-making
<!-- END_BLOCK -->
