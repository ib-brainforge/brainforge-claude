# Recipe: Validate Implementation Plan

## Purpose

Validate the synthesized plan against architectural rules and patterns.

## Validation Dimensions

The plan-validator agent checks 8 dimensions:

| Dimension | What It Checks |
|-----------|----------------|
| **Completeness** | All affected services have tasks |
| **Dependencies** | Correct ordering, no cycles |
| **Patterns** | Follows required design patterns |
| **Security** | Auth, authorization, data protection |
| **Performance** | Caching, query optimization, scaling |
| **Testing** | Unit, integration, E2E coverage |
| **Deployment** | CI/CD, rollback, feature flags |
| **Documentation** | API docs, ADRs, runbooks |

## Validation Levels

- **strict**: Fail on any warning
- **standard**: Fail on errors, warn on issues (default)
- **lenient**: Only fail on blockers

## Spawning Validator

```
Task: spawn plan-validator
Prompt: |
  Validate implementation plan:
  Feature: $FEATURE_NAME
  Plan: [synthesized plan]
  Level: $VALIDATION_LEVEL

  Check all 8 dimensions, return issues and recommendations.
```

## Output Format

```json
{
  "status": "PASS|WARN|FAIL",
  "dimensions": {
    "completeness": { "status": "PASS", "issues": [] },
    "dependencies": { "status": "WARN", "issues": [...] },
    ...
  },
  "blockers": [],
  "warnings": [...],
  "recommendations": [...]
}
```

## Knowledge Dependencies

- `knowledge/architecture/design-patterns.md` - Pattern requirements
- `knowledge/validation/backend-patterns.md` - What to avoid
- `knowledge/architecture/service-boundaries.md` - Service rules
