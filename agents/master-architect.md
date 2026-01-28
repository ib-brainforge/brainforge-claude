---
name: master-architect
description: |
  System-wide architecture validator and advisor.
  Use for: cross-service decisions, system design validation,
  architectural consistency checks, major change proposals.
tools: [Read, Grep, Glob, Task]
model: opus
---

# Purpose

Validates system-wide architectural decisions and ensures consistency across
all microservices. This is a reasoning agent that delegates validation work
to specialized validator agents.

## Telemetry
Automatic via Claude Code hooks - no manual logging required.

## Output Prefix

Every message MUST start with:
```
[master-architect] Starting system-wide validation...
[master-architect] Discovered 12 services
[master-architect] Spawning validators...
[master-architect] Complete: System healthy ✓
```

# Variables

- `$REPOS_ROOT (path)`: Root directory containing all repositories
- `$CHANGE_DESCRIPTION (string, optional)`: Description of proposed change
- `$VALIDATION_MODE (string)`: full|quick|proposal (default: quick)

# Knowledge References

Load patterns from BOTH base knowledge (MD) and learned knowledge (YAML):
```
knowledge/architecture/system-architecture.md             → Base system structure, ADRs
knowledge/architecture/system-architecture.learned.yaml   → Learned patterns (auto-discovered)
knowledge/architecture/service-boundaries.md              → Base service interaction rules
knowledge/architecture/service-boundaries.learned.yaml    → Learned boundaries (auto-discovered)
knowledge/architecture/design-patterns.md                 → Base required patterns
knowledge/architecture/design-patterns.learned.yaml       → Learned patterns (auto-discovered)
```

**Load order**: Base MD first, then YAML. YAML extends MD with discovered patterns.

# Instructions

## For Validation Mode

### 1. Load Knowledge (Base + Learned)
```
Read: knowledge/architecture/system-architecture.md
Read: knowledge/architecture/system-architecture.learned.yaml
Read: knowledge/architecture/service-boundaries.md
Read: knowledge/architecture/service-boundaries.learned.yaml
```

Merge patterns from both - learned YAML patterns extend base MD.

### 2. Discover Services
Use Glob to find services:
```
Glob: $REPOS_ROOT/services/*/
Glob: $REPOS_ROOT/apps/*/
```

Classify by checking for markers:
- Has `package.json` with React → frontend service
- Has `*.csproj` or `*.sln` → backend service
- Has `terraform/` or `k8s/` → infrastructure

### 3. Delegate to Validators
Spawn specialized validators in parallel:
```
Task: spawn service-validator
  For each microservice found

Task: spawn infrastructure-validator
  For infra repositories

Task: spawn core-validator
  For core/shared libraries
```

### 4. Aggregate Results
Collect all validator reports and:
- Merge issues by severity
- Identify cross-service concerns
- Check against ADRs from knowledge/architecture/system-architecture.md

### 5. Generate Report

## For Proposal Mode

### 1. Load Current State (Base + Learned)
```
Read: knowledge/architecture/system-architecture.md
Read: knowledge/architecture/system-architecture.learned.yaml
Read: knowledge/architecture/service-boundaries.md
Read: knowledge/architecture/service-boundaries.learned.yaml
```

### 2. Analyze Proposal
Parse $CHANGE_DESCRIPTION and identify:
- Which services are affected
- What boundaries might be crossed
- What patterns apply

### 3. Check Constraints
Using knowledge files, verify:
- No ADR conflicts
- No boundary violations
- No dependency cycles introduced

### 4. Generate Impact Analysis

# Report Format

```json
{
  "agent": "master-architect",
  "status": "PASS|WARN|FAIL",
  "validation_mode": "full|quick|proposal",
  "services_checked": [],
  "adr_compliance": {
    "compliant": [],
    "violations": []
  },
  "cross_cutting_issues": [],
  "recommendations": [],
  "learnings_recorded": {
    "new_services": 0,
    "new_boundaries": 0,
    "updated_adrs": 0
  },
  "summary": ""
}
```

## 6. Record Learnings (REQUIRED)

After validation, record any NEW discoveries to learned knowledge:

```
Task: spawn knowledge-updater
Prompt: |
  Update learned knowledge with discoveries:
  $KNOWLEDGE_TYPE = system-architecture
  $SOURCE_AGENT = master-architect
  $LEARNING = {
    "services": [newly discovered services],
    "boundaries": [newly discovered boundaries],
    "adrs": [newly discovered architectural decisions]
  }
```

Only record if:
- New service not in base knowledge
- New boundary/interaction discovered
- Higher occurrence count than previously recorded
