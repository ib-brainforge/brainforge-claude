---
name: feature-planning
description: |
  Comprehensive feature analysis and implementation planning.
  Gathers architectural inputs, generates phased plans, validates against rules.
triggers:
  - /plan-feature
  - plan feature
  - create implementation plan
  - design feature
---

# Purpose

Analyze feature requests, consult architectural subagents, and produce validated
implementation plans for full-stack features (frontend + backend slices).

# Usage

```
/plan-feature "user-auth" "Login, logout, password reset with OAuth"
/plan-feature "notifications" "Real-time notifications via WebSocket"
/plan-feature "dashboard" "Admin analytics dashboard with charts"
```

# Variables

- `$FEATURE_NAME (string)`: Short identifier (kebab-case)
- `$DESCRIPTION (string)`: Detailed feature requirements
- `$REPOS_ROOT (path)`: Path to repositories (default: .)
- `$OUTPUT_DIR (path)`: Where to write plans (default: ./feature-plans)
- `$VALIDATION_LEVEL (string)`: strict|standard|lenient (default: standard)

# Knowledge References

Load base knowledge AND recent changes from learned YAML:

```
knowledge/architecture/system-architecture.md              → Base system structure
knowledge/architecture/system-architecture.learned.yaml    → Recent features, decisions
knowledge/architecture/service-boundaries.md               → Base interaction rules
knowledge/architecture/service-boundaries.learned.yaml     → Recent communications
knowledge/architecture/design-patterns.md                  → Required patterns
knowledge/architecture/tech-stack.md                       → Framework versions
knowledge/architecture/tech-stack.learned.yaml             → Recent dependency changes
knowledge/packages/core-packages.md                        → Shared libraries
```

**Note**: This skill READS learned YAML but does NOT write to it.
Recording happens in `commit-manager` after implementation is committed.

# Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FEATURE PLANNING WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: DISCOVERY                                                          │
│  ─────────────────                                                           │
│  • Load knowledge (base MD + learned YAML)                                   │
│  • Parse feature requirements                                                │
│  • Identify affected services using Glob/Grep                                │
│                                                                              │
│  PHASE 2: ARCHITECTURAL CONSULTATION                                         │
│  ───────────────────────────────────                                         │
│  Spawn parallel subagents:                                                   │
│    ├──► master-architect ──► System constraints                              │
│    ├──► frontend-pattern-validator ──► UI patterns                           │
│    ├──► backend-pattern-validator ──► API patterns                           │
│    ├──► core-validator ──► Library impacts                                   │
│    └──► infrastructure-validator ──► Deployment needs                        │
│                                                                              │
│  PHASE 3: SYNTHESIS                                                          │
│  ─────────────────                                                           │
│  • Combine all architectural inputs                                          │
│  • Identify dependencies and sequencing                                      │
│  • Generate phased task breakdown                                            │
│                                                                              │
│  PHASE 4: VALIDATION                                                         │
│  ───────────────────                                                         │
│  Spawn: plan-validator                                                       │
│    • Check 8 validation dimensions                                           │
│    • Verify pattern compliance                                               │
│                                                                              │
│  PHASE 5: OUTPUT                                                             │
│  ────────────────                                                            │
│  • Write plan document (Markdown)                                            │
│  • Write task breakdown (JSON)                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Instructions

## Phase 1: Discovery

### 1.1 Load Knowledge (Base + Learned)
```
Read: knowledge/architecture/system-architecture.md
Read: knowledge/architecture/system-architecture.learned.yaml
Read: knowledge/architecture/service-boundaries.md
Read: knowledge/architecture/service-boundaries.learned.yaml
Read: knowledge/architecture/design-patterns.md
Read: knowledge/architecture/tech-stack.md
Read: knowledge/architecture/tech-stack.learned.yaml
Read: knowledge/packages/core-packages.md
```

Check learned YAML for:
- Recent features affecting same services (avoid conflicts)
- Recent breaking changes to consider
- Recently established communications

### 1.2 Parse Feature Request
Extract from $DESCRIPTION:
- Core functionality
- User stories / acceptance criteria
- Integration points
- Data requirements

### 1.3 Identify Affected Services

Discover services:
```
Glob: $REPOS_ROOT/*/                → Find all repositories
```

Classify each service:
```
Glob: [repo]/package.json           → Frontend (check for React/Vue)
Glob: [repo]/*.csproj               → .NET backend
Glob: [repo]/go.mod                 → Go backend
```

Search for feature-related code:
```
Grep: "[feature keywords]" in [service]/src/**/*
```

### 1.4 Analyze Current State
For each affected service:
```
Grep: "interface" in [service]/src/**/*     → Existing interfaces
Grep: "\[Route\(" in [service]/src/**/*     → Current endpoints
Grep: "class.*Entity" in [service]/src/**/* → Existing entities
```

## Phase 2: Architectural Consultation

**Spawn these subagents in PARALLEL:**

### Master Architect
```
Task: spawn master-architect
Prompt: |
  Analyze feature for architectural fit:
  Feature: $FEATURE_NAME
  Description: $DESCRIPTION
  Affected services: [from discovery]

  Provide:
  - System-wide architectural constraints
  - Cross-service communication requirements
  - Data flow recommendations
  - Potential architectural concerns
```

### Frontend Analysis
```
Task: spawn frontend-pattern-validator
Prompt: |
  Analyze frontend requirements:
  Feature: $FEATURE_NAME
  Description: $DESCRIPTION

  Provide:
  - Recommended component patterns
  - State management approach
  - UI consistency requirements
```

### Backend Analysis
```
Task: spawn backend-pattern-validator
Prompt: |
  Analyze backend requirements:
  Feature: $FEATURE_NAME
  Description: $DESCRIPTION

  Provide:
  - API design recommendations
  - Database schema changes
  - Security considerations
```

### Core Library Impact
```
Task: spawn core-validator
Prompt: |
  Analyze core library impact:
  Feature: $FEATURE_NAME

  Provide:
  - Shared utilities needed
  - Core package changes required
  - Breaking change risks
```

### Infrastructure
```
Task: spawn infrastructure-validator
Prompt: |
  Analyze infrastructure needs:
  Feature: $FEATURE_NAME

  Provide:
  - Deployment changes needed
  - Environment configurations
  - Scaling considerations
```

## Phase 3: Synthesis

### 3.1 Aggregate Inputs
Collect all subagent responses and identify:
- Common themes and requirements
- Conflicting recommendations (if any)
- Critical path dependencies

### 3.2 Generate Implementation Plan

Structure the plan as Markdown:

```markdown
# Feature: $FEATURE_NAME

## Overview
[Summary from synthesis]

## Architectural Decisions
[Key decisions with rationale]

## Implementation Phases

### Phase 1: Foundation
- [ ] Task 1.1: ...
- [ ] Task 1.2: ...

### Phase 2: Backend Implementation
- [ ] Task 2.1: ...

### Phase 3: Frontend Implementation
- [ ] Task 3.1: ...

### Phase 4: Integration
- [ ] Task 4.1: ...

### Phase 5: Testing & Validation
- [ ] Task 5.1: ...

## Dependencies
[Ordered list]

## Risk Assessment
[Identified risks and mitigations]

## Estimated Effort
[Complexity and time estimates]
```

## Phase 4: Validation

```
Task: spawn plan-validator
Prompt: |
  Validate implementation plan:
  Feature: $FEATURE_NAME
  Plan: [generated plan]
  Level: $VALIDATION_LEVEL

  Check:
  - Architectural rule compliance
  - Service boundary constraints
  - Pattern compliance
  - Security requirements
  - Dependency ordering
```

Handle validation results:
- PASS → Proceed to output
- WARN → Note warnings in plan, proceed
- FAIL → Revise plan based on feedback, re-validate

## Phase 5: Output

Write plan document:
```
Write: $OUTPUT_DIR/feature-$FEATURE_NAME-plan.md
```

Write task breakdown (optional):
```
Write: $OUTPUT_DIR/feature-$FEATURE_NAME-tasks.json
```

# Report Format

```json
{
  "skill": "feature-planning",
  "status": "PASS|WARN|FAIL",
  "feature": {
    "name": "user-auth",
    "description": "Login, logout, password reset"
  },
  "discovery": {
    "affected_services": ["auth-service", "user-frontend"],
    "frontend_components": ["LoginForm", "ResetPassword"],
    "backend_endpoints": ["/api/auth/*"],
    "database_changes": true
  },
  "plan": {
    "phases": 5,
    "total_tasks": 24,
    "estimated_days": 8,
    "complexity": "medium"
  },
  "validation": {
    "status": "PASS",
    "warnings": [],
    "blockers": []
  },
  "artifacts": {
    "plan_document": "feature-user-auth-plan.md",
    "task_export": "feature-user-auth-tasks.json"
  }
}
```

# Note on Learnings

**This skill does NOT record learnings.**

Recording happens in `commit-manager` AFTER implementation is complete.
This ensures single-writer pattern and prevents concurrent write conflicts.

The flow is:
1. feature-planner → creates plan
2. User implements the plan
3. commit-manager → commits changes AND records learnings

# Task Export Formats

The task JSON can be formatted for:
- GitHub Issues
- Jira
- Linear

# Related Skills

After plan is approved:
- `design-patterns` - Validate implementation follows patterns
- `validation` - Validate implementation as you build
- `commit-manager` - Commit changes and record learnings
