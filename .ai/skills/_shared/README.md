# Shared Skills Framework

Cross-agent reusable skill frameworks that reduce duplication and standardize patterns.

---

## Overview

This directory contains unified frameworks that multiple agents can reference instead of maintaining duplicate logic.

## Available Frameworks

| Framework | Purpose | Used By Agents |
|-----------|---------|----------------|
| [analytics_framework.skill.md](analytics_framework.skill.md) | Unified analytics patterns | PM, Contents-Creator, HR, Finance |
| [optimization_framework.skill.md](optimization_framework.skill.md) | Unified optimization patterns | Developer, Finance, Contents-Creator |
| [research_framework.skill.md](research_framework.skill.md) | Unified research patterns | PM, Contents-Creator, Finance |

## Usage Pattern

Agent-specific skills should **reference** these frameworks rather than duplicate logic:

```markdown
<!-- In agent-specific skill file -->
## Framework Reference
This skill uses the unified analytics framework.
See: .ai/skills/_shared/analytics_framework.skill.md

### Mode Configuration
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

1. **Context Reduction**: ~60% reduction in duplicate content
2. **Consistency**: Single source of truth for shared patterns
3. **Maintenance**: Update once, benefit all agents
4. **Quality**: Unified quality standards across agents

## Block Structure

All frameworks follow the standard block structure:
- `CORE_LOGIC`: Mode detection and core functionality
- `INPUT_OUTPUT`: Standardized I/O specifications
- `EXECUTION_LOGIC`: Step-by-step execution patterns
- `TECHNICAL_REQUIREMENTS`: Technical standards
- `CONSTRAINTS`: Scope limitations
- `RELATED_SKILLS`: Cross-references to agent skills

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial consolidation |
