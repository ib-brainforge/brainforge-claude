# Knowledge Correction Skill

Investigate and correct misconceptions in knowledge files.

## Triggers

Invoke this skill when user says:
- `/update-knowledge "..."` (explicit command)
- "the knowledge is wrong about..."
- "that's not how we do it, we actually..."
- "correct the knowledge..."
- "fix the knowledge about..."
- "the docs say X but we use Y"
- "actually, we use X not Y" (when referring to patterns/tech)

## Quick Reference

| Aspect | Value |
|--------|-------|
| Agent | `knowledge-investigator` |
| Model | sonnet |
| Updates | Base knowledge (*.md), NOT learned (*.yaml) |
| Log | `.claude/knowledge-corrections.log` |

## How to Invoke

When detecting a misconception report:

```
Task: spawn knowledge-investigator
Prompt: |
  Investigate and correct misconception.
  $MISCONCEPTION = "[USER'S DESCRIPTION OF WHAT'S WRONG]"
  $REPOS_ROOT = [path to repos]
  $KNOWLEDGE_AREA = [auto-detect or specify: architecture|validation|packages|all]
```

## Workflow

```
┌────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE CORRECTION FLOW                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. USER REPORTS MISCONCEPTION                                      │
│     └──► "We use AuditableEntity not BaseEntity"                   │
│                                                                     │
│  2. INVESTIGATE CODEBASE                                            │
│     └──► Grep/Glob/Read to find actual patterns                    │
│     └──► Count occurrences, find evidence                          │
│                                                                     │
│  3. COMPARE WITH KNOWLEDGE                                          │
│     └──► Read relevant knowledge files                             │
│     └──► Identify discrepancy                                      │
│                                                                     │
│  4. CORRECT KNOWLEDGE                                               │
│     └──► Edit *.md files with accurate info                        │
│     └──► Add correction comment with date                          │
│                                                                     │
│  5. LOG & REPORT                                                    │
│     └──► Log to knowledge-corrections.log                          │
│     └──► Report what was changed                                   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

## Knowledge Areas

| Area | Files | Examples |
|------|-------|----------|
| `architecture` | system-architecture.md, service-boundaries.md, design-patterns.md, tech-stack.md | Service structure, communication patterns, frameworks |
| `validation` | backend-patterns.md, frontend-patterns.md, security-standards.md | Code patterns, grep patterns, validation rules |
| `packages` | core-packages.md, package-config.md, repo-config.md | Dependencies, versions, package rules |

## Example Corrections

### Pattern Name Wrong
```
Misconception: "we use IGenericRepository not IRepository"
Action: Update backend-patterns.md grep patterns
```

### Tech Stack Outdated
```
Misconception: "we're on .NET 8 not .NET 6"
Action: Update tech-stack.md framework versions
```

### Architecture Incorrect
```
Misconception: "auth-service uses events not HTTP to call user-service"
Action: Update service-boundaries.md communication patterns
```

## Output Format

The agent returns:
```json
{
  "status": "CORRECTED|VERIFIED|NO_CHANGE_NEEDED",
  "misconception": "...",
  "findings": {
    "knowledge_said": "...",
    "actual_state": "..."
  },
  "corrections": [
    {
      "file": "...",
      "old_value": "...",
      "new_value": "..."
    }
  ]
}
```

## Main Agent Instructions

When user reports a knowledge misconception:

1. **Detect trigger** - Match against trigger phrases above
2. **Extract misconception** - What does user say is wrong?
3. **Spawn agent** - Use knowledge-investigator
4. **Report results** - Show what was corrected (if anything)

```
[main] Detected knowledge correction request
[main] Misconception: "we use AuditableEntity not BaseEntity"
[main] Spawning knowledge-investigator...
```
