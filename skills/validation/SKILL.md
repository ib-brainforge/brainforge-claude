---
name: validation
description: |
  Architectural validation across repositories.
  Domain-agnostic - references knowledge/ for project-specific rules.
triggers:
  - /validate
  - validate architecture
  - check architecture
  - run validation
---

# Purpose

Run comprehensive architectural validation across all services. Domain-agnostic skill that references `knowledge/` for project-specific rules.

# Usage

```bash
/validate                           # Validate all services
/validate --scope frontend          # Frontend services only
/validate --scope backend           # Backend services only
/validate --service user-service    # Single service
/validate --quick                   # Structure only (fast)
```

# Variables

- `$SCOPE (string)`: all|frontend|backend|infrastructure
- `$SERVICE (string, optional)`: Specific service to validate
- `$QUICK (bool)`: Skip deep analysis (default: false)
- `$REPOS_ROOT (path)`: Root directory containing repositories

# Knowledge References

Load base knowledge (this skill does NOT write to learned YAML - only reads):

```
knowledge/architecture/system-architecture.md         → System structure, service map
knowledge/architecture/service-boundaries.md          → Allowed service communications
knowledge/architecture/design-patterns.md             → Required patterns
knowledge/architecture/tech-stack.md                  → Framework versions
knowledge/validation/backend-patterns.md              → Backend validation rules
knowledge/validation/frontend-patterns.md             → Frontend validation rules
```

**Note**: Validators do NOT record learnings. Only `commit-manager` writes to learned YAML files.

# Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│  1. LOAD KNOWLEDGE    → Read all pattern files                   │
│  2. DISCOVER          → Glob to find services                    │
│  3. CLASSIFY          → Determine frontend/backend/infra         │
│  4. VALIDATE PARALLEL → Spawn validator subagents                │
│  5. AGGREGATE         → Combine results                          │
│  6. REPORT            → Return validation report                 │
└─────────────────────────────────────────────────────────────────┘
```

# Instructions

## 1. Load Knowledge

```
Read: knowledge/architecture/system-architecture.md
Read: knowledge/architecture/service-boundaries.md
Read: knowledge/architecture/design-patterns.md
Read: knowledge/architecture/tech-stack.md
Read: knowledge/validation/backend-patterns.md
Read: knowledge/validation/frontend-patterns.md
```

## 2. Discover Services

```
Glob: $REPOS_ROOT/*/               → Find all repositories
```

For each discovered repo, classify by checking for:
```
Glob: [repo]/package.json          → Frontend (React/Vue/Angular)
Glob: [repo]/*.csproj              → .NET backend
Glob: [repo]/go.mod                → Go backend
Glob: [repo]/pom.xml               → Java backend
Glob: [repo]/terraform/            → Infrastructure
```

## 3. Filter by Scope

Based on $SCOPE, filter discovered services:
- `frontend`: Only repos with package.json containing React/Vue/Angular
- `backend`: Only repos with .csproj, go.mod, pom.xml
- `infrastructure`: Only repos with terraform/, pulumi/, k8s/
- `all`: Include all services

If $SERVICE specified, validate only that service.

## 4. Validate Services (Parallel Subagents)

### For Backend Services
```
Task: spawn backend-pattern-validator
Prompt: |
  Validate backend service: [service-path]
  Load patterns from knowledge/validation/backend-patterns.md
  Check against knowledge/architecture/design-patterns.md
  Return JSON validation report
```

### For Frontend Services
```
Task: spawn frontend-pattern-validator
Prompt: |
  Validate frontend service: [service-path]
  Load patterns from knowledge/validation/frontend-patterns.md
  Check against knowledge/architecture/design-patterns.md
  Return JSON validation report
```

### For Infrastructure
```
Task: spawn infrastructure-validator
Prompt: |
  Validate infrastructure: [service-path]
  Check against knowledge/architecture/system-architecture.md
  Return JSON validation report
```

### For Service Boundaries
```
Task: spawn master-architect
Prompt: |
  Validate service boundaries across all services.
  Load: knowledge/architecture/service-boundaries.md
  Load: knowledge/architecture/system-architecture.md
  Check for forbidden communications.
  Return JSON validation report
```

## 5. Aggregate Results

Combine all subagent reports:
- Collect all PASS/WARN/FAIL statuses
- Merge issues by category
- Calculate overall status (FAIL if any FAIL, WARN if any WARN, else PASS)

## 6. Quick Mode (if $QUICK)

Skip subagent spawning. Only check:
```
Glob: [service]/src/**/*           → Verify structure exists
Read: [service]/package.json       → Check dependencies
Grep: "TODO" in [service]/src/**/* → Find outstanding TODOs
```

# Validation Categories

| Category | Validator Agent | Knowledge Source |
|----------|-----------------|------------------|
| Structure | (built-in) | system-architecture.md |
| Backend Patterns | backend-pattern-validator | backend-patterns.md |
| Frontend Patterns | frontend-pattern-validator | frontend-patterns.md |
| Service Boundaries | master-architect | service-boundaries.md |
| Infrastructure | infrastructure-validator | system-architecture.md |

# Report Format

```json
{
  "skill": "validation",
  "status": "PASS|WARN|FAIL",
  "summary": {
    "services_checked": 40,
    "passed": 38,
    "warnings": 1,
    "failures": 1
  },
  "categories": {
    "structure": { "status": "PASS" },
    "patterns": { "status": "WARN", "issues": [...] },
    "boundaries": { "status": "PASS" },
    "dependencies": { "status": "FAIL", "issues": [...] }
  },
  "services": [
    {
      "name": "user-service",
      "type": "backend",
      "status": "PASS",
      "issues": []
    }
  ],
  "critical_issues": [...],
  "recommendations": [...]
}
```

# Note on Learnings

**This skill does NOT record learnings.**

Validation findings are observations, not changes. Only `commit-manager` records
architectural learnings after actual code changes are committed.

# Related Skills

- `design-patterns` - Detailed pattern validation
- `feature-planning` - Plan fixes for issues
- `commit-manager` - Commit validation fixes
