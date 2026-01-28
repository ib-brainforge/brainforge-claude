# Recipe: Generate Output Files

## Purpose

Generate human-readable plans and machine-readable task exports.

## Output Files

| File | Format | Purpose |
|------|--------|---------|
| `feature-{name}-plan.md` | Markdown | Human-readable implementation plan |
| `feature-{name}-tasks.json` | JSON | Import to Jira/GitHub/Linear |
| `feature-{name}-validation.json` | JSON | Validation results |

## Plan Document Generation

```bash
python tools/feature-analysis.py write-plan \
  --feature "$FEATURE_NAME" \
  --plan /tmp/validated-plan.json \
  --output "$OUTPUT_DIR/feature-$FEATURE_NAME-plan.md"
```

### Plan Document Structure

```markdown
# Feature: {name}

## Overview
{description}

## Affected Services
- {service list}

## Design Patterns Applied
- {pattern list with rationale}

## Implementation Phases

### Phase 1: {name}
**Dependencies:** {deps}
**Deliverables:** {deliverables}

#### Tasks
- [ ] Task 1 (S)
- [ ] Task 2 (M)

### Phase 2: ...

## Risks & Mitigations
- {risk}: {mitigation}

## Testing Strategy
- {test types and coverage}
```

## Task Export Formats

```bash
# GitHub Issues
python tools/feature-analysis.py export-tasks \
  --plan /tmp/validated-plan.json \
  --format github-issues \
  --output "$OUTPUT_DIR/feature-$FEATURE_NAME-tasks.json"

# Jira
--format jira

# Linear
--format linear
```

### GitHub Issues Format

```json
{
  "issues": [
    {
      "title": "Task title",
      "body": "Description...",
      "labels": ["feature:{name}", "phase:1"],
      "milestone": "Feature: {name}"
    }
  ]
}
```
