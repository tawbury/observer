# Shared Skills Framework

Operational loop skills and cross-agent framework components.

---

## Operational Loop Skills (v2.0 Core)

The operational loop requires two shared skills executed by all agents:

| Skill | Purpose | Agents |
|-------|---------|--------|
| [[operational_roadmap_management.skill.md]] | Create/update Roadmap; track phase/session/task status; manage loop continuity | All agents |
| [[operational_run_record_creation.skill.md]] | Create Run Records as execution evidence; propose Roadmap updates | All agents |

**Loop Pattern**:
1. Roadmap defines phases/sessions and Task status
2. Agents execute Tasks using domain-specific skills
3. Run Records document what happened, what changed, propose next steps
4. Roadmap updated based on Run Record evidence
5. Next session reads Roadmap + Run Records to resume

**Session Resilience**: If interrupted, repository state (Roadmap + Run Records) is the source of truth for resumption.

---

## Cross-Agent Framework Components

Reusable skill frameworks that multiple agents reference to reduce duplication:

| Framework | Purpose | Used By Agents |
|-----------|---------|----------------|
| [[analytics_framework.skill.md]] | Unified analytics patterns | PM, Contents-Creator, HR, Finance |
| [[optimization_framework.skill.md]] | Unified optimization patterns | Developer, Finance, Contents-Creator |
| [[research_framework.skill.md]] | Unified research patterns | PM, Contents-Creator, Finance |

### Framework Usage Pattern

Agent-specific skills **reference** (not duplicate) framework logic:

```markdown
## Framework Reference
This skill extends: [[analytics_framework.skill.md]]

## Mode Configuration
- **Mode**: PRODUCT
- **Analysis Types**: DESCRIPTIVE, PREDICTIVE
```

## Mode Mapping by Agent

### Analytics Framework Modes
| Agent | Primary Mode | Secondary Modes |
|-------|--------------|-----------------|
| PM | PRODUCT | - |
| Contents-Creator | AUDIENCE | CONTENT |
| HR | TALENT | - |
| Finance | FINANCIAL | - |

### Optimization Framework Modes
| Agent | Primary Mode | Secondary Modes |
|-------|--------------|-----------------|
| Developer | PERFORMANCE | PROCESS |
| Finance | COST | PROCESS |
| Contents-Creator | CONTENT | PROCESS |

### Research Framework Modes
| Agent | Primary Mode | Secondary Modes |
|-------|--------------|-----------------|
| PM | USER | MARKET |
| Contents-Creator | AUDIENCE | - |
| Finance | TREND | MARKET |

## Benefits

1. **Context Reduction**: ~60% reduction in duplicate content (frameworks only)
2. **Session Resilience**: Operational loop skills enable interrupted session recovery
3. **Consistency**: Single source of truth for shared patterns and operational rules
4. **Maintenance**: Update once, benefit all agents
5. **Quality**: Unified standards across agents

## Block Structure

All skills follow the standard block structure:
- `CORE_LOGIC` or process steps
- `INPUTS`
- `OUTPUTS`
- `EVIDENCE_RULES`: How to validate execution evidence (Run Records, decisions, artifacts)
- `CONSTRAINTS`
- `RELATED_SKILLS`: Cross-references to agent-specific skills

## Integration Points

- **Roadmap & Run Record**: Core operational loop templates ([[../templates/roadmap_template.md]], [[../templates/run_record_template.md]])
- **All agent workflows**: Every agent executes both operational loop skills
- **Evidence discipline**: Run Records capture execution proof per [[operational_run_record_creation.skill.md]]

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial framework consolidation |
| 2.0 | 2026-01-21 | Added operational loop skills as v2.0 core; reorganized for loop-first structure |
