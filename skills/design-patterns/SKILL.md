---
name: design-patterns
description: |
  Validate and suggest design patterns for your applications.
  All specific patterns and packages loaded from knowledge files.
triggers:
  - /patterns
  - /design-patterns
  - check patterns
  - suggest patterns
  - validate patterns
---

# Purpose

Validate existing code against established design patterns, suggest appropriate
patterns for new features, and ensure consistent use of core package components.
All specific patterns are defined in knowledge files.

# Usage

```bash
# Validate existing code
/patterns validate src/components/
/patterns validate src/services/

# Suggest patterns for a feature
/patterns suggest "feature description here"

# Review code changes
/patterns review                    # Review staged changes
/patterns review --pr 123           # Review PR
```

# Variables

- `$MODE (string)`: validate|suggest|review (default: validate)
- `$TARGET (string)`: File, directory, or feature description
- `$TECH_STACK (string)`: frontend|backend|both (auto-detect)
- `$STRICT (bool)`: Fail on pattern violations (default: false)
- `$REPOS_ROOT (path)`: Root directory containing repositories

# Knowledge References

Load ALL domain-specific information from knowledge files:

```
knowledge/architecture/design-patterns.md      → Required patterns for frontend/backend
knowledge/validation/backend-patterns.md       → Backend validation rules, anti-patterns
knowledge/validation/frontend-patterns.md      → Frontend validation rules, anti-patterns
knowledge/packages/core-packages.md            → Shared libraries and their APIs
knowledge/architecture/tech-stack.md           → Framework versions and conventions
```

**IMPORTANT**: Do not hardcode any framework names, package names, or specific
patterns in this skill. All such information must come from knowledge files.

**Note**: This skill does NOT record learnings. Only `commit-manager` writes to learned YAML files.

# Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DESIGN PATTERNS WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. LOAD KNOWLEDGE                                                           │
│     └──► Read design-patterns.md, backend/frontend-patterns.md,              │
│          core-packages.md                                                    │
│                                                                              │
│  MODE: validate                                                              │
│  ──────────────                                                              │
│  2. Detect tech stack (Glob for package.json, *.csproj)                      │
│  3. Scan for pattern usage (Grep against knowledge patterns)                 │
│  4. Check core component usage (Grep for imports)                            │
│  5. Detect anti-patterns (Grep for anti-pattern markers)                     │
│  6. Generate compliance report                                               │
│                                                                              │
│  MODE: suggest                                                               │
│  ─────────────                                                               │
│  2. Parse feature requirements                                               │
│  3. Match to pattern categories (from knowledge)                             │
│  4. Identify core components to use (from knowledge)                         │
│  5. Generate recommendations                                                 │
│                                                                              │
│  MODE: review                                                                │
│  ────────────                                                                │
│  2. Get code changes (git diff)                                              │
│  3. Analyze pattern compliance (against knowledge)                           │
│  4. Generate review comments                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Instructions

## 1. Load Knowledge First

Always start by reading:
```
Read: knowledge/architecture/design-patterns.md
Read: knowledge/validation/backend-patterns.md
Read: knowledge/validation/frontend-patterns.md
Read: knowledge/packages/core-packages.md
Read: knowledge/architecture/tech-stack.md
```

## Mode: Validate

### 2. Detect Tech Stack
```
Glob: $TARGET/package.json          → Frontend (check contents for React/Vue)
Glob: $TARGET/*.csproj              → .NET backend
Glob: $TARGET/go.mod                → Go backend
```

Read the found files to determine specific frameworks/versions.

### 3. Scan for Pattern Usage

For backend (patterns from knowledge):
```
Grep: "Repository" in $TARGET/src/**/*        → Repository pattern
Grep: "IMediator" in $TARGET/src/**/*         → CQRS/Mediator pattern
Grep: "Command" in $TARGET/src/**/*           → Command pattern
Grep: "Query" in $TARGET/src/**/*             → Query pattern
```

For frontend (patterns from knowledge):
```
Grep: "useState" in $TARGET/src/**/*          → React hooks
Grep: "useQuery" in $TARGET/src/**/*          → Data fetching
Grep: "createContext" in $TARGET/src/**/*     → Context API
```

### 4. Check Core Component Usage
```
Grep: "@core/" in $TARGET/src/**/*            → Core package imports
Grep: "from 'Core." in $TARGET/src/**/*       → .NET Core imports
```

### 5. Detect Anti-Patterns

For backend (from knowledge/validation/backend-patterns.md):
```
Grep: "new DbContext" in $TARGET/src/**/*     → Direct context instantiation
Grep: "Thread.Sleep" in $TARGET/src/**/*      → Blocking calls
Grep: "catch.*Exception" in $TARGET/src/**/*  → Generic exception handling
```

For frontend (from knowledge/validation/frontend-patterns.md):
```
Grep: "any" in $TARGET/src/**/*.ts            → TypeScript any usage
Grep: "eslint-disable" in $TARGET/src/**/*    → Linting bypasses
Grep: "// @ts-ignore" in $TARGET/src/**/*     → Type checking bypasses
```

### 6. Generate Compliance Report

Compile findings into report with:
- Patterns correctly used
- Patterns missing (should be used)
- Anti-patterns found
- Core component usage

## Mode: Suggest

### 2. Parse Feature Description

Extract keywords from $TARGET (feature description):
- Data operations → Repository, CQRS patterns
- User interactions → Command, Event patterns
- UI components → Component, Container patterns
- State management → Context, Store patterns

### 3. Spawn Design Pattern Advisor
```
Task: spawn design-pattern-advisor
Prompt: |
  Suggest patterns for feature: $TARGET
  Mode: suggest

  Use knowledge from:
  - knowledge/architecture/design-patterns.md
  - knowledge/packages/core-packages.md

  Provide:
  - Recommended patterns with rationale
  - Core components to use
  - Code examples
  - Common pitfalls to avoid
```

## Mode: Review

### 2. Get Changes
```
Bash: git diff --cached --name-only     → List changed files
Bash: git diff --cached                 → Get full diff
```

For PR review:
```
Bash: gh pr diff $PR_NUMBER             → Get PR diff
```

### 3. Analyze Changes

For each changed file:
```
Read: [changed-file]
```

Check against patterns from knowledge:
- New code follows required patterns
- No anti-patterns introduced
- Core components used correctly

### 4. Spawn Design Pattern Advisor
```
Task: spawn design-pattern-advisor
Prompt: |
  Review code changes:
  Changes: [from git diff]
  Mode: review

  Use knowledge from:
  - knowledge/architecture/design-patterns.md
  - knowledge/validation/backend-patterns.md
  - knowledge/validation/frontend-patterns.md

  For each file changed:
  - Check pattern compliance
  - Identify improvements
  - Suggest specific changes
```

# Report Format

```json
{
  "skill": "design-patterns",
  "mode": "validate|suggest|review",
  "status": "PASS|WARN|FAIL",
  "target": "src/services/",
  "tech_stack": {
    "frontend": "React 18",
    "backend": ".NET 8"
  },
  "score": {
    "pattern_compliance": 85,
    "core_component_usage": 90,
    "anti_pattern_free": 75,
    "overall": 83
  },
  "patterns": {
    "compliant": [
      {"pattern": "Repository", "locations": ["UserRepository.cs"]}
    ],
    "violations": [
      {"pattern": "CQRS", "issue": "Missing command handler", "location": "UserService.cs"}
    ],
    "missing": [
      {"pattern": "Mediator", "recommendation": "Use MediatR for command dispatch"}
    ]
  },
  "core_components": {
    "used_correctly": ["@core/ui/Button", "@core/forms/Input"],
    "should_use": ["@core/hooks/useApi"],
    "deprecated_usage": []
  },
  "anti_patterns": [
    {
      "pattern": "Direct DbContext",
      "location": "UserService.cs:45",
      "suggestion": "Inject via constructor"
    }
  ],
  "recommendations": [
    "Add IMediator to UserService for command handling",
    "Replace direct API calls with useApi hook"
  ]
}
```

# Note on Learnings

**This skill does NOT record learnings.**

Pattern observations are validation findings, not architectural changes.
Only `commit-manager` records learnings after actual code is committed.

# Related Skills

- `validation` - Full architectural validation
- `feature-planning` - Plan new features with patterns
- `commit-manager` - Commit pattern-compliant code
