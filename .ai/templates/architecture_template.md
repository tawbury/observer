# Architecture Document Template

## Purpose
Standard template for system architecture documentation

## Template Structure

```markdown
# Meta
- Project Name: 
- File Name: 
- Document ID: 
- Status: Draft
- Created Date: {{CURRENT_DATE}}
- Last Updated: {{CURRENT_DATE}}
- Author: {{USER}}
- Reviewer: {{REVIEWER}}
- Parent Document: 
- Related Reference: 
- Version: 

---

# [Project Name] Architecture Document

---

## Overview
### Architecture Vision
- System architecture vision and goals
- Technical principles and philosophy
- Long-term scalability considerations

### System Boundaries
- System scope and boundaries
- External interfaces and integrations
- System responsibilities and limitations

## Architecture Principles
### Core Principles
- [Principle 1]: [Description and rationale]
- [Principle 2]: [Description and rationale]
- [Principle 3]: [Description and rationale]

### Design Guidelines
- Modularity and separation of concerns
- Scalability and performance considerations
- Security and compliance requirements
- Maintainability and extensibility principles

## System Structure
### High-Level Architecture
- System overview diagram
- Major components and relationships
- Data flow and interaction patterns

### Component Architecture
- [Component 1]: [Description, responsibilities, interfaces]
- [Component 2]: [Description, responsibilities, interfaces]
- [Component 3]: [Description, responsibilities, interfaces]

### Data Architecture
- Data model and relationships
- Data flow patterns
- Storage and persistence strategy

## Technology Stack
### Backend Technologies
- [Technology 1]: [Purpose and justification]
- [Technology 2]: [Purpose and justification]
- [Technology 3]: [Purpose and justification]

### Frontend Technologies
- [Technology 1]: [Purpose and justification]
- [Technology 2]: [Purpose and justification]
- [Technology 3]: [Purpose and justification]

### Infrastructure
- [Infrastructure 1]: [Purpose and configuration]
- [Infrastructure 2]: [Purpose and configuration]
- [Infrastructure 3]: [Purpose and configuration]

## Implementation Plan
### Development Phases
#### Phase 1: Foundation
- [Goals and deliverables]
- [Timeline and resources]
- [Success criteria]

#### Phase 2: Core Features
- [Goals and deliverables]
- [Timeline and resources]
- [Success criteria]

#### Phase 3: Advanced Features
- [Goals and deliverables]
- [Timeline and resources]
- [Success criteria]

### Technical Roadmap
- [Milestone 1]: [Description and timeline]
- [Milestone 2]: [Description and timeline]
- [Milestone 3]: [Description and timeline]

## Decision Items
### Architecture Decisions
- [Decision 1]: [Context, options, decision, rationale]
- [Decision 2]: [Context, options, decision, rationale]
- [Decision 3]: [Context, options, decision, rationale]

### Trade-offs
- [Trade-off 1]: [Options considered and chosen approach]
- [Trade-off 2]: [Options considered and chosen approach]
- [Trade-off 3]: [Options considered and chosen approach]

## Quality Attributes
### Performance
- Response time requirements
- Throughput requirements
- Scalability targets
- Performance monitoring strategy

### Security
- Security requirements and controls
- Authentication and authorization
- Data protection measures
- Security testing approach

### Reliability
- Availability requirements
- Fault tolerance strategies
- Disaster recovery plans
- Monitoring and alerting

### Maintainability
- Code quality standards
- Documentation requirements
- Testing strategies
- Deployment and maintenance procedures

## Integration Points
### External Systems
- [System 1]: [Interface specifications]
- [System 2]: [Interface specifications]
- [System 3]: [Interface specifications]

### APIs
- [API 1]: [Endpoint, format, authentication]
- [API 2]: [Endpoint, format, authentication]
- [API 3]: [Endpoint, format, authentication]

## Deployment Architecture
### Environment Architecture
- Development environment
- Testing environment
- Production environment
- Disaster recovery environment

### Infrastructure Components
- [Component 1]: [Configuration and purpose]
- [Component 2]: [Configuration and purpose]
- [Component 3]: [Configuration and purpose]

### Monitoring and Observability
- Logging strategy
- Metrics collection
- Alerting and notification
- Performance monitoring

## Risk Assessment
### Technical Risks
- [Risk 1]: [Impact, probability, mitigation]
- [Risk 2]: [Impact, probability, mitigation]
- [Risk 3]: [Impact, probability, mitigation]

### Operational Risks
- [Risk 1]: [Impact, probability, mitigation]
- [Risk 2]: [Impact, probability, mitigation]
- [Risk 3]: [Impact, probability, mitigation]

## Evolution Strategy
### Future Considerations
- Scalability evolution paths
- Technology migration strategies
- Architecture evolution roadmap

### Maintenance Strategy
- Regular review cycles
- Update and upgrade procedures
- Technical debt management

## Field Descriptions

### Meta Fields
- **Project Name**: Project name
- **File Name**: File name (auto-generated)
- **Document ID**: Document unique ID
- **Status**: Document status (Draft/Review/Approved)
- **Created Date**: Creation date
- **Last Updated**: Last update date
- **Author**: Author
- **Parent Document**: Parent document reference
- **Related Reference**: Related reference documents
- **Version**: Document version (1.0, 1.1, 2.0, etc.)

## Usage Rules
1. File name format: `architecture_<project>_<version>.md`
2. Storage location: `docs/dev/archi/`
3. Meta section and main text separated by `---`
4. All required fields must not be empty
5. Update version when making significant changes

## Features
- **Technical Focus**: Emphasis on technical architecture and implementation
- **Comprehensive Coverage**: Includes all aspects of system architecture
- **Decision Documentation**: Records important architectural decisions
- **Evolution Planning**: Includes future evolution and maintenance strategies

## Related Documents
- `.ai/templates/prd_template.md` - Product requirements template
- `.ai/templates/spec_template.md` - Specification template
- `.ai/workflows/software_development.workflow.md` - Software development workflow
- `.ai/.cursorrules` - System rules
