---
name: /fix-bugs-jira
description: Fix bugs from a Jira ticket. Use /fix-bug-direct for direct bug descriptions.
allowed_tools: [Read, Task]
---

# Purpose

Fix all bugs listed in a Jira ticket. **Requires a Jira ticket ID.**

Use this when you have a Jira ticket with bugs to fix.

**CRITICAL**: Do NOT attempt to fix bugs yourself. The bug-triage agent handles everything.

## When to Use This vs /fix-bug-direct

| Scenario | Command |
|----------|---------|
| You have a Jira ticket with bugs listed | `/fix-bugs-jira TICKET-ID` ← **This one** |
| You have a bug description, no Jira ticket | `/fix-bug-direct "..."` |

# Arguments

- `TICKET_ID` (required): Jira ticket ID (e.g., BF-119, PROJ-123)
- `--dry-run`: Preview fixes without committing (default: false)
- `--skip-validation`: Skip pattern validation (default: false)

# Usage

```
/fix-bugs-jira BF-119
/fix-bugs-jira PROJ-123 --dry-run
/fix-bugs-jira BF-119 --skip-validation
```

# Knowledge References

The bug-triage agent will load these (you don't need to):
```
knowledge/jira/jira-config.md                → Jira configuration
knowledge/architecture/system-architecture.md → Service map
knowledge/architecture/service-boundaries.md  → Service dependencies
```

# Workflow

## 1. Acknowledge and Log

Output:
```
[main] Detected Jira bug fix request for TICKET_ID
[main] Spawning bug-triage agent...
```

Log:
```
Bash: echo "[$(date -Iseconds)] [main] /fix-bugs-jira invoked for $TICKET_ID" >> .claude/agent-activity.log
```

## 2. Spawn bug-triage Agent

**This is the ONLY action you take. Do NOT do anything else.**

```
Task: spawn bug-triage
Prompt: |
  Fix bugs from Jira ticket.

  $TICKET_ID = [TICKET_ID from argument]
  $REPOS_ROOT = [current working directory or configured repos root]
  $DRY_RUN = [true if --dry-run flag, else false]
  $SKIP_VALIDATION = [true if --skip-validation flag, else false]

  Follow your workflow:
  1. Fetch ticket from Jira
  2. Parse bug list
  3. Analyze and prioritize
  4. Spawn bug-fixer for each bug
  5. Validate all fixes
  6. Commit with Jira linking
  7. Update Jira ticket

  Return structured report with subagents_spawned.
```

## 3. Report Results

After bug-triage returns, display summary:

```
[main] Bug triage complete

Ticket: TICKET_ID
Status: PASS/WARN/FAIL

Bugs Fixed: X/Y
- Bug #1: [description] ✓
- Bug #2: [description] ✓
- Bug #3: [description] ✗ (reason)

Commits:
- repo-name: abc123

Subagents Used:
- jira-integration (fetch, parse-bugs, comment)
- bug-fixer x3
- backend-pattern-validator
- commit-manager

See .claude/agent-activity.log for full trace.
```

# Error Handling

| Error | Action |
|-------|--------|
| Invalid ticket ID | Show usage, ask for correct format |
| Jira fetch fails | Report error from bug-triage |
| No bugs found | Report from bug-triage |
| Partial fixes | Show which succeeded/failed |

# What NOT To Do

**DO NOT**:
- Fetch the Jira ticket yourself
- Parse bugs yourself
- Fix bugs yourself
- Commit changes yourself
- Update Jira yourself

**The bug-triage agent does ALL of this.** Your only job is to spawn it.

# Example Session

User: `/fix-bugs-jira BF-119`

```
[main] Detected Jira bug fix request for BF-119
[main] Spawning bug-triage agent...

[bug-triage] Starting bug triage for ticket BF-119...
[bug-triage] Spawning jira-integration to fetch ticket...
[jira-integration] Fetching ticket BF-119...
[jira-integration] Complete: ticket fetched
[bug-triage] Parsed 2 bugs from ticket description
[bug-triage] Bug #1: Login fails with special characters (high)
[bug-triage] Bug #2: Session timeout incorrect (medium)
[bug-triage] Spawning bug-fixer for bug #1...
[bug-fixer] Starting fix for bug #1...
[bug-fixer] Found root cause in auth-service/src/login.cs
[bug-fixer] Fix applied, tests passing
[bug-triage] Spawning bug-fixer for bug #2...
[bug-fixer] Starting fix for bug #2...
[bug-fixer] Fix applied, tests passing
[bug-triage] Spawning backend-pattern-validator...
[backend-pattern-validator] Validation PASS
[bug-triage] Spawning commit-manager...
[commit-manager] Committed auth-service: abc123
[bug-triage] Spawning jira-integration to update ticket...
[jira-integration] Added comment to BF-119
[bug-triage] Complete: 2 bugs fixed, 0 failed

[main] Bug triage complete

Ticket: BF-119
Status: PASS

Bugs Fixed: 2/2
- Bug #1: Login fails with special characters ✓
- Bug #2: Session timeout incorrect ✓

Commits:
- auth-service: abc123

Subagents Used: 7
```
