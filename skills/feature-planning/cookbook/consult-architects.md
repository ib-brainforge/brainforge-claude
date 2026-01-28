# Recipe: Consult Architectural Subagents

## Purpose

Gather architectural guidance from specialized subagents in parallel.

## Subagent Roster

| Agent | Responsibility | Output |
|-------|----------------|--------|
| `master-architect` | System-wide constraints | Constraints, communication patterns |
| `frontend-pattern-validator` | UI/UX patterns | Component patterns, state management |
| `backend-pattern-validator` | API patterns | API design, database changes |
| `core-validator` | Library impact | Shared utilities, breaking changes |
| `infrastructure-validator` | Deployment | CI/CD, scaling needs |
| `design-pattern-advisor` | Pattern recommendations | Recommended patterns, examples |

## Parallel Execution

All subagents should be spawned in parallel for efficiency:

```
Task: spawn [agent-name]
Prompt: |
  Analyze [aspect] for feature:
  Feature: $FEATURE_NAME
  Description: $DESCRIPTION
  Affected: [from discovery]

  Provide: [expected outputs]
```

## Consultation Order

1. First wave (parallel):
   - design-pattern-advisor (suggest mode)
   - master-architect
   - frontend-pattern-validator
   - backend-pattern-validator

2. Second wave (parallel, after discovery):
   - core-validator
   - infrastructure-validator

## Merging Results

Collect outputs to temp files:
- `/tmp/master-input.json`
- `/tmp/frontend-input.json`
- `/tmp/backend-input.json`
- `/tmp/core-input.json`
- `/tmp/infra-input.json`
- `/tmp/design-patterns-input.json`

## Knowledge Dependencies

Each subagent references:
- `knowledge/architecture/design-patterns.md`
- `knowledge/validation/backend-patterns.md`
- `knowledge/architecture/tech-stack.md`
- `knowledge/packages/core-packages.md`
