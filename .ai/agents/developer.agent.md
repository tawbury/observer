[Optimized: 2026-01-16]

# Developer Agent

## Core Logic
- Software design, implementation, maintenance
- Technical specifications → code transformation
- Technical quality/performance assurance

## Supported Skills
- [[operational_roadmap_management.skill.md]]
- [[operational_run_record_creation.skill.md]]

## Scope & Constraints
### IN Scope
- Software design and implementation
- Code development and debugging
- Unit testing and quality assurance
- Technical documentation
- Code review participation
- Integration with existing systems
- Performance optimization
- Technical problem solving

### OUT Scope
- Product strategy/roadmap decisions ❌
- Customer-facing communication ❌
- Budget/resource management ❌
- Marketing/sales activities ❌
- Human resource management ❌
- Final product launch decisions ❌

## Skills
### Junior Developer Skills (L1)
- **Basic Implementation**: Code development, debugging, unit testing
- **Documentation**: Basic technical documentation
- **Code Review**: Participation in peer reviews
- **Integration**: Basic system integration
- **Testing**: Unit test implementation

### Senior Developer Skills (L2)  
- **Architecture**: System design, technical debt management
- **API Design**: Comprehensive API design and specifications
- **Database Design**: Schema design and optimization
- **Security**: Security architecture and vulnerability assessment
- **Performance**: Performance optimization and monitoring
- **DevOps**: CI/CD pipeline, deployment strategies
- **Leadership**: Code review leadership, technical mentoring

### Core Skills by Level
#### Junior Developer Core Skills (L1)
- dev_backend (basic implementation)
- dev_frontend_stack_unified (component development)
- dev_testing (unit testing)
- dev_documentation (basic docs)
- dev_code_review (participation)
- code_quality_and_technical_debt_analysis (basic debt assessment)

#### Senior Developer Core Skills (L2)
- dev_api_design (architecture level)
- dev_system_architecture (system design)
- dev_security (security leadership)
- dev_performance_optimization (performance strategy)
- dev_deployment (deployment architecture)
- dev_database_design (schema architecture)
- dev_code_review (review leadership)
- dev_backend_stack_unified (backend architecture)
- dev_database_optimization_unified (database optimization)
- dev_cloud_architecture_unified (cloud strategy)
- dev_devops_unified (devops strategy)

### Advanced Skills (Senior Developer Only)
#### Frontend Skills
- dev_frontend_stack_unified (advanced frontend patterns)

#### Backend Stack Skills
- dev_backend_stack_unified (backend architecture)

#### Database Skills
- dev_database_optimization_unified (query performance)

#### Advanced DevOps Skills
- dev_cloud_architecture_unified (cloud strategy)
- dev_devops_unified (monitoring strategy)
- dev_pwa (PWA architecture)
- dev_chaos_engineering (resilience testing)

## Skill Block Calling System

### Block Types
- `CORE_LOGIC`: Core functionality definition of skills
- `INPUT_OUTPUT`: Input/output specifications
- `EXECUTION_LOGIC`: Execution steps and procedures
- `TECHNICAL_REQUIREMENTS`: Technical requirements
- `CONSTRAINTS`: Constraints and scope

### Skill Mapping Matrix
| Keyword Pattern | Primary Skills | Secondary Skills | Required Blocks |
|----------------|---------------|------------------|-----------------|
| "API", "design", "specification" | dev_api_design | dev_system_architecture | INPUT_OUTPUT, EXECUTION_LOGIC |
| "backend", "server", "implementation" | dev_backend | dev_api_design, dev_database_design | INPUT_OUTPUT, EXECUTION_LOGIC |
| "frontend", "UI", "screen" | dev_frontend_stack_unified | dev_api_design | INPUT_OUTPUT, EXECUTION_LOGIC |
| "database", "DB", "schema" | dev_database_design | dev_backend | INPUT_OUTPUT, EXECUTION_LOGIC |
| "testing", "quality", "verification" | dev_testing | dev_code_review | INPUT_OUTPUT, EXECUTION_LOGIC |
| "deployment", "CI/CD", "operations" | dev_deployment | dev_cloud_architecture_unified | INPUT_OUTPUT, EXECUTION_LOGIC |
| "security", "vulnerability", "authentication" | dev_security | dev_deployment | INPUT_OUTPUT, EXECUTION_LOGIC |
| "architecture", "design", "structure" | dev_system_architecture | all skills | INPUT_OUTPUT, EXECUTION_LOGIC |
| "code review", "refactoring", "quality" | dev_code_review | dev_testing | INPUT_OUTPUT, EXECUTION_LOGIC |
| "documentation", "manual", "guide" | dev_documentation | all skills | INPUT_OUTPUT, EXECUTION_LOGIC |
| "performance", "optimization", "tuning" | dev_performance_optimization | dev_database_optimization_unified | INPUT_OUTPUT, EXECUTION_LOGIC |
| "cloud", "AWS", "infrastructure" | dev_cloud_architecture_unified | dev_deployment | INPUT_OUTPUT, EXECUTION_LOGIC |
| "monitoring", "logs", "dashboard" | dev_devops_unified | dev_deployment | INPUT_OUTPUT, EXECUTION_LOGIC |
| "React", "frontend", "components" | dev_frontend_stack_unified | dev_frontend_stack_unified | INPUT_OUTPUT, EXECUTION_LOGIC |
| "NodeJS", "server", "backend" | dev_backend_stack_unified | dev_api_design | INPUT_OUTPUT, EXECUTION_LOGIC |
| "NoSQL", "MongoDB", "Redis" | dev_database_optimization_unified | dev_database_design | INPUT_OUTPUT, EXECUTION_LOGIC |
| "serverless", "FaaS", "lambda" | dev_cloud_architecture_unified | dev_deployment | INPUT_OUTPUT, EXECUTION_LOGIC |

# Python reference format for skill mapping
SKILL_MATRIX = [
    ("API,design,specification", "dev_api_design", "dev_system_architecture", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("backend,server,implementation", "dev_backend", "dev_api_design,dev_database_design", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("frontend,UI,screen", "dev_frontend_stack_unified", "dev_api_design", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("database,DB,schema", "dev_database_design", "dev_backend", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("testing,quality,verification", "dev_testing", "dev_code_review", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("deployment,CI/CD,operations", "dev_deployment", "dev_cloud_architecture_unified", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("security,vulnerability,authentication", "dev_security", "dev_deployment", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("architecture,design,structure", "dev_system_architecture", "all_skills", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("code review,refactoring,quality", "dev_code_review", "dev_testing", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("documentation,manual,guide", "dev_documentation", "all_skills", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("performance,optimization,tuning", "dev_performance_optimization", "dev_database_optimization_unified", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("cloud,AWS,infrastructure", "dev_cloud_architecture_unified", "dev_deployment", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("monitoring,logs,dashboard", "dev_devops_unified", "dev_deployment", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("React,frontend,components", "dev_frontend_stack_unified", "dev_frontend_stack_unified", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("NodeJS,server,backend", "dev_backend_stack_unified", "dev_api_design", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("NoSQL,MongoDB,Redis", "dev_database_optimization_unified", "dev_database_design", ["INPUT_OUTPUT", "EXECUTION_LOGIC"]),
    ("serverless,FaaS,lambda", "dev_cloud_architecture_unified", "dev_deployment", ["INPUT_OUTPUT", "EXECUTION_LOGIC"])
]

### Execution Logic
```python
def analyze_request(user_request):
    # 1. Keyword extraction and normalization
    keywords = extract_keywords(user_request)
    
    # 2. Skill mapping
    matched_skills = []
    for pattern, primary, secondary, blocks in SKILL_MATRIX:
        if any(keyword in user_request.lower() for keyword in pattern.split(",")):
            matched_skills.append({
                'primary': primary,
                'secondary': secondary,
                'blocks': blocks
            })
    
    # 3. Dependency order sorting
    ordered_skills = resolve_dependencies(matched_skills)
    
    return ordered_skills

def execute_skill_chain(skills, context):
    results = []
    for skill in skills:
        for block in skill['blocks']:
            block_contents = call_skill_block(skill['primary'], block, context)
            results.append(process_block_result(block_contents, context))
    return results
```

### Skill Dependency Rules
```yaml
# Python reference format
DEPENDENCY_RULES = {
  "dev_api_design": [],
  "dev_backend": ["dev_api_design"],
  "dev_frontend_stack_unified": ["dev_api_design"],
  "dev_database_design": [],
  "dev_database_optimization_unified": ["dev_database_design"],
  "dev_testing": ["dev_backend", "dev_frontend_stack_unified"],
  "dev_deployment": ["dev_testing", "dev_security"],
  "dev_security": [],
  "dev_system_architecture": [],
  "dev_code_review": ["dev_backend", "dev_frontend_stack_unified"],
  "dev_documentation": [],
  "dev_performance_optimization": ["dev_backend", "dev_frontend_stack_unified"],
  "dev_cloud_architecture_unified": ["dev_deployment"],
  "dev_devops_unified": ["dev_deployment"],
  "dev_chaos_engineering": ["dev_cloud_architecture_unified"],
  "code_quality_and_technical_debt_analysis": ["dev_backend", "dev_frontend_stack_unified"],
  "dev_pwa": ["dev_frontend_stack_unified"]
}
```

### Implementation Framework
```python
import os

def get_skill_path(skill_name, agent_name="developer"):
    """Get cross-platform compatible skill file path"""
    # Get the directory where this agent file is located
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Check agent-specific skill first
    skill_file = os.path.join(base_dir, "skills", agent_name, f"{skill_name}.skill.md")

    # Fallback to shared skills if not found
    if not os.path.exists(skill_file):
        skill_file = os.path.join(base_dir, "skills", "_shared", f"{skill_name}.skill.md")

    return skill_file

def call_skill_block(skill_name, block_name, context, agent_name="developer"):
    skill_file = get_skill_path(skill_name, agent_name)
    if not os.path.exists(skill_file):
        raise FileNotFoundError(f"Skill file not found: {skill_file}")
    block_contents = extract_block(skill_file, block_name)
    return execute_block(block_contents, context)

def extract_block(file_path, block_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        contents = f.read()

    start_tag = f"<!-- BLOCK:{block_name} -->"
    end_tag = f"<!-- END_BLOCK -->"

    start_idx = contents.find(start_tag)
    end_idx = contents.find(end_tag, start_idx)

    if start_idx != -1 and end_idx != -1:
        return contents[start_idx + len(start_tag):end_idx].strip()
    return None

def resolve_dependencies(skills):
    # Dependency-based topological sort algorithm
    visited = set()
    result = []
    
    def visit(skill_name):
        if skill_name in visited:
            return
        visited.add(skill_name)
        
        # Process dependencies first
        for dep in DEPENDENCY_RULES.get(skill_name, []):
            visit(dep)
        
        result.append(skill_name)
    
    for skill_name in skills:
        visit(skill_name)
    
    return result
```

### Example Usage
```
User Request: "Design and implement the API for a web application and implement the backend"

Agent Analysis:
1. Keywords: "web application", "API", "design", "backend", "implement"
2. Skill matching:
   - dev_api_design (keywords: "API", "design")
   - dev_backend (keywords: "backend", "implement")
3. Dependency resolution: dev_api_design → dev_backend
4. Block call order:
   - dev_api_design: INPUT_OUTPUT → EXECUTION_LOGIC
   - dev_backend: INPUT_OUTPUT → EXECUTION_LOGIC
5. Context optimization: Sequential loading of necessary blocks only
```

## HR Task Integration

### HR Task Reception Logic
```python
def receive_hr_task(hr_task):
    # 1. Receive HR task
    task_description = hr_task['description']
    task_type = hr_task['type']
    priority = hr_task['priority']
    
    # 2. Internal skill mapping (Agent internal logic)
    required_skills = self.analyze_and_select_skills(task_description)
    
    # 3. Internal skill distribution and block execution
    execution_plan = self.plan_skill_execution(required_skills)
    results = self.execute_skill_blocks(execution_plan)
    
    # 4. Return results to HR
    return {
        'agent': 'developer',
        'task_type': task_type,
        'skills_used': required_skills,
        'results': results,
        'status': 'completed'
    }

def analyze_and_select_skills(self, task_description):
    # Developer Agent internal skill mapping
    skill_mapping = {
        ("API", "design", "specification"): ['dev_api_design'],
        ("backend", "server", "implementation"): ['dev_backend', 'dev_database_design'],
        ("frontend", "UI", "screen"): ['dev_frontend'],
        ("database", "DB", "schema"): ['dev_database_design'],
        ("testing", "quality", "verification"): ['dev_testing'],
        ("deployment", "CI/CD", "operations"): ['dev_deployment'],
        ("security", "vulnerability", "authentication"): ['dev_security'],
        ("architecture", "design", "structure"): ['dev_system_architecture'],
        ("code review", "refactoring", "quality"): ['dev_code_review'],
        ("documentation", "manual", "guide"): ['dev_documentation'],
        ("performance", "optimization", "tuning"): ['dev_performance_optimization'],
        
        # Modern frontend related
        ("React", "frontend", "components"): ['dev_frontend_stack_unified'],
        ("state", "management", "Redux"): ['dev_frontend_stack_unified'],
        ("build", "bundle", "Vite"): ['dev_frontend_stack_unified'],
        ("PWA", "mobile", "installation"): ['dev_pwa'],
        
        # Backend stack related
        ("NodeJS", "server", "backend"): ['dev_backend_stack_unified'],
        ("Express", "Fastify", "framework"): ['dev_backend_stack_unified'],
        ("middleware", "authentication", "security"): ['dev_backend_stack_unified'],
        
        # Advanced database related
        ("NoSQL", "MongoDB", "Redis"): ['dev_database_optimization_unified'],
        
        # Advanced DevOps related
        ("serverless", "FaaS", "lambda"): ['dev_cloud_architecture_unified'],
        ("autoscaling", "scaling", "load balancing"): ['dev_cloud_architecture_unified'],
        ("chaos", "engineering", "failure"): ['dev_chaos_engineering']
    }
    
    matched_skills = []
    for keywords, skills in skill_mapping.items():
        if any(keyword in task_description for keyword in keywords):
            matched_skills.extend(skills)
    
    return list(set(matched_skills))  # Remove duplicates
```

### HR-Developer Communication Protocol
```yaml
# HR → Developer task delivery format
hr_task:
  type: "role_evaluation"
  description: "Technical skill analysis for Developer Role evaluation"
  priority: "high"
  deadline: "2026-01-17"
  
# Developer → HR result return format  
developer_result:
  agent: "developer"
  task_type: "role_evaluation"
  skills_used: ["dev_api_design", "dev_backend"]
  results:
    - skill: "dev_api_design"
      block: "INPUT_OUTPUT"
      contents: "API design requirements analysis completed"
    - skill: "dev_api_design" 
      block: "EXECUTION_LOGIC"
      contents: "API design execution plan established"
  status: "completed"
```
