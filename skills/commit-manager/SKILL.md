---
name: commit-manager
description: |
  Intelligent commit message generation across multiple repositories.
  Analyzes changes, detects commit type, generates conventional commits.
  ALSO: Single writer for learned knowledge - records architectural changes after commits.
triggers:
  - /commit
  - commit changes
  - generate commit
  - push changes
---

# Purpose

Generate intelligent, consistent commit messages across all repositories.
Analyzes diffs, detects change types (feat/fix/chore/etc), and manages
multi-repo commits with two-phase commit protocol.

**IMPORTANT**: This is the ONLY skill/agent that writes to learned knowledge files.
After committing significant changes (multi-service features), it records learnings.

# Usage

```
/commit                              # Commit all staged changes
/commit --repo user-service          # Single repo
/commit --scope frontend             # All frontend repos
/commit --dry-run                    # Preview without committing
/commit --push                       # Commit and push
/commit --skip-validation            # Skip pre-commit validation
```

# Variables

- `$REPOS_ROOT (path)`: Path to repositories (default: .)
- `$REPO (string, optional)`: Specific repo to commit
- `$SCOPE (string, optional)`: frontend|backend|all
- `$DRY_RUN (bool)`: Preview only (default: true)
- `$PUSH (bool)`: Push after commit (default: false)
- `$SKIP_VALIDATION (bool)`: Skip pre-commit validation (default: false)
- `$TICKET_ID (string, optional)`: Ticket/issue ID to include

# Knowledge References

Load commit conventions:
```
knowledge/commit-conventions.md      → Commit message format and rules
knowledge/packages/repo-config.md    → Repo-specific commit rules
```

For recording learnings (single writer):
```
knowledge/architecture/system-architecture.learned.yaml   → To record features
knowledge/architecture/service-boundaries.learned.yaml    → To record communications
knowledge/architecture/tech-stack.learned.yaml            → To record dependency changes
```

# Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COMMIT MANAGER WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. LOAD KNOWLEDGE                                                           │
│     └──► Read commit-conventions.md                                          │
│                                                                              │
│  2. DISCOVER CHANGES                                                         │
│     └──► Bash: git status --porcelain (for each repo)                        │
│                                                                              │
│  3. ANALYZE EACH REPO                                                        │
│     └──► Bash: git diff --cached                                             │
│          Determine commit type from changes                                  │
│                                                                              │
│  4. PRE-COMMIT VALIDATION (multi-service feat only)                          │
│     └──► Spawn validators in parallel                                        │
│          PASS → Continue | WARN → Prompt user | FAIL → Abort                 │
│                                                                              │
│  5. TWO-PHASE COMMIT                                                         │
│     Phase 1: Stage all repos                                                 │
│     Phase 2: Verify staging (check for secrets, unexpected files)            │
│     Phase 3: Commit all repos                                                │
│                                                                              │
│  6. PUSH (if requested)                                                      │
│     └──► Bash: git push                                                      │
│                                                                              │
│  7. RECORD LEARNINGS (if significant)                                        │
│     └──► Spawn knowledge-updater (only for multi-service feat)               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Instructions

## 1. Load Knowledge
```
Read: knowledge/commit-conventions.md
Read: knowledge/packages/repo-config.md
```

## 2. Discover Changed Repositories

Find all repos:
```
Glob: $REPOS_ROOT/*/
```

Check each for changes:
```
Bash: cd [repo] && git status --porcelain
```

Identify repos with staged, unstaged, or untracked changes.

## 3. Analyze Changes (For Each Repo)

### 3.1 Get Diff
```
Bash: cd [repo] && git diff --cached --stat
Bash: cd [repo] && git diff --cached
```

For unstaged:
```
Bash: cd [repo] && git diff --stat
```

### 3.2 Categorize Changed Files
```
Glob: [repo]/src/**/*          → Source files
Glob: [repo]/test/**/*         → Test files
Glob: [repo]/docs/**/*         → Documentation
Glob: [repo]/*.json            → Config files
```

### 3.3 Detect Commit Type

| Type | Trigger Patterns |
|------|------------------|
| `feat` | New files in src/, new exports, new endpoints |
| `fix` | Changes to existing logic, bug-related keywords |
| `refactor` | Restructuring without behavior change |
| `perf` | Performance-related changes |
| `test` | Test files only |
| `docs` | Documentation only |
| `style` | Formatting, whitespace |
| `chore` | Config, build, dependencies |
| `ci` | CI/CD pipeline changes |

### 3.4 Detect Breaking Changes

Flag as BREAKING if:
- Public API signatures changed
- Exports removed
- Required parameters added
- Database migrations present

Check patterns:
```
Grep: "BREAKING" in [repo]/CHANGELOG.md
Grep: "@deprecated" in [repo]/src/**/*
```

### 3.5 Generate Commit Message

Format (from knowledge/commit-conventions.md):
```
<type>(<scope>): <subject>

<body>

<footer>
```

Rules:
- Subject: imperative, <50 chars, no period
- Scope: component/module affected
- Body: what and why (not how)
- Footer: BREAKING CHANGE, ticket refs

## 4. Pre-Commit Validation (Multi-Service Changes)

**Only if**: Changes span multiple repos AND include `feat` type
**Skip if**: `$SKIP_VALIDATION` is true

```
Task: spawn backend-pattern-validator (for backend repos)
Task: spawn frontend-pattern-validator (for frontend repos)
```

On validation result:
- **PASS** → Proceed to commit
- **WARN** → Show warnings, ask user to proceed or abort
- **FAIL** → Show errors, abort commits

## 5. Two-Phase Commit (if not dry-run)

### Phase 1: Stage All Repositories
```
For each repo:
  Bash: cd [repo] && git add [specific-files]
```

### Phase 2: Verify Staging
```
For each repo:
  Bash: cd [repo] && git diff --cached --stat
```

Verify:
- All expected files are staged
- No unexpected files staged
- No secrets detected:
```
Grep: "password\s*=" in [staged files]
Grep: "api_key\s*=" in [staged files]
Grep: "secret\s*=" in [staged files]
```

**If verification fails** → Abort all:
```
For each repo:
  Bash: cd [repo] && git reset HEAD
```
Report error and exit.

### Phase 3: Commit All Repositories
Only proceed if Phase 2 passed for ALL repos:
```
For each repo:
  Bash: cd [repo] && git commit -m "[generated_message]"
```

## 6. Push (if enabled)
```
For each repo:
  Bash: cd [repo] && git push origin [current_branch]
```

Push failures don't affect commits - user can retry manually.

## 7. Record Learned Knowledge (SINGLE WRITER)

**This is the ONLY place where learned knowledge is recorded.**

### 7.1 Determine What to Record

Only record if significant:
- **Features**: feat commits touching multiple repos
- **Communications**: New event published/consumed
- **Breaking Changes**: Any BREAKING commit
- **Dependencies**: New package added to multiple services

Skip recording if:
- Only test/doc changes
- Single file fix
- Refactor without behavior change
- Style/formatting only

### 7.2 Record Learnings

If significant changes detected:

```
Task: spawn knowledge-updater
Prompt: |
  $KNOWLEDGE_TYPE = system-architecture
  $SOURCE_AGENT = commit-manager
  $TICKET = $TICKET_ID
  $SOURCE_COMMITS = [list of commit SHAs]
  $LEARNING = {
    "type": "feature",
    "description": "[summarize from commit messages]",
    "ticket": "$TICKET_ID",
    "affected_services": [
      {"name": "[repo-name]", "changes": ["[from commit]"]}
    ],
    "breaking": [true if any breaking commits]
  }
```

If new service communication detected:
```
Task: spawn knowledge-updater
Prompt: |
  $KNOWLEDGE_TYPE = service-boundaries
  $SOURCE_AGENT = commit-manager
  $LEARNING = {
    "type": "communication",
    "from": "[calling service]",
    "to": "[called service]",
    "type": "event|http",
    "contract": "[event name or endpoint]",
    "ticket": "$TICKET_ID"
  }
```

# Commit Type Detection Rules

| Pattern | Type |
|---------|------|
| New files, new functions | `feat` |
| Bug fixes, error handling | `fix` |
| Dependencies, configs | `chore` |
| Code restructuring | `refactor` |
| Documentation changes | `docs` |
| Test files | `test` |
| Formatting only | `style` |
| Performance improvements | `perf` |
| CI/CD changes | `ci` |

# Report Format

```json
{
  "skill": "commit-manager",
  "status": "PASS|WARN|FAIL",
  "repositories": [
    {
      "name": "repo-name",
      "path": "/path/to/repo",
      "branch": "feature/xyz",
      "changes": {
        "files_changed": 5,
        "insertions": 120,
        "deletions": 30
      },
      "commit": {
        "type": "feat",
        "scope": "auth",
        "subject": "add OAuth2 support",
        "breaking": false,
        "message": "full message here"
      },
      "actions": {
        "committed": true,
        "pushed": true,
        "commit_sha": "abc123"
      }
    }
  ],
  "summary": {
    "repos_processed": 3,
    "commits_created": 3,
    "pushed": 3,
    "breaking_changes": 0
  },
  "validation": {
    "ran": true,
    "status": "PASS",
    "warnings": []
  },
  "learnings_recorded": {
    "features": 1,
    "communications": 0,
    "breaking_changes": 0,
    "skipped_reason": null
  }
}
```

# Important Notes

1. **Single Writer Pattern**: Only this skill writes to learned YAML files.
   This prevents concurrent write conflicts from parallel operations.

2. **Two-Phase Commit**: Ensures all repos commit together or none do.
   Prevents partial failures across multi-repo changes.

3. **Pre-Commit Validation**: Only runs for multi-service feat changes.
   Can be skipped with `--skip-validation` flag.

4. **Dry-Run Default**: `$DRY_RUN` defaults to true. Use `--execute` to commit.

# Related Skills

- `validation` - Run before committing to check compliance
- `feature-planning` - Plan features before implementation
- `package-release` - Update package versions after commits
