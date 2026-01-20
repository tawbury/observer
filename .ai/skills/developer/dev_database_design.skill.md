[Optimized: 2026-01-16]
[Related Skills: dev_query_optimization.skill.md, dev_nosql.skill.md]

# Dev Database Design Skill

> **Note**: This skill provides the foundation for database design.
> For query performance optimization, see `dev_query_optimization.skill.md`.
> For NoSQL database specialized design, see `dev_nosql.skill.md`.

<!-- BLOCK:CORE_LOGIC -->
## Core Logic
- Data model design & optimization
- Database schema structuring
- Data consistency & integrity guarantee
<!-- END_BLOCK -->

<!-- BLOCK:INPUT_OUTPUT -->
## Input/Output
### Input
- Business requirements definitions
- Data flow specifications
- API endpoint definitions
- Performance requirements

### Output
- Database schema design
- ERD (Entity Relationship Diagram)
- Index optimization strategies
- Data migration plans
- Query optimization guides
<!-- END_BLOCK -->

<!-- BLOCK:EXECUTION_LOGIC -->
## Execution Logic
1. Analyze business requirements & identify entities
2. Data modeling (conceptual → logical → physical)
3. Normalization & denormalization strategies
4. Index design & performance optimization
5. Data integrity constraint definitions
6. Security & access control design
7. Backup & recovery strategy establishment
8. Migration & management plans (version managed in Meta section Version field)
<!-- END_BLOCK -->

<!-- BLOCK:TECHNICALREQUIREMENTS -->
## Technical Requirements
- Database systems (PostgreSQL, MySQL, MongoDB)
- Modeling tools (ERD, Lucidchart)
- ORM frameworks (Prisma, SQLAlchemy)
- Database management tools
- Performance monitoring tools
<!-- END_BLOCK -->

<!-- BLOCK:CONSTRAINTS -->
## Constraints
### OUT Scope
- Application business logic implementation ❌
- Frontend interface development ❌
- Infrastructure management ❌
- Data analysis & reporting ❌

### Technical Constraints
- ACID property compliance (relational DB)
- Data duplication minimization
- Scalability-considered design
- Security & privacy regulation compliance
- Query performance optimization
<!-- END_BLOCK -->

## Related Skills
- **Query Optimization**: See `dev_query_optimization.skill.md` for query tuning and performance analysis
- **NoSQL Specialization**: See `dev_nosql.skill.md` for MongoDB, Redis, Cassandra design
