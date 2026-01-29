---
name: /fix-bug-direct
description: Fix a bug described directly (no Jira required). Use /fix-bugs-jira for Jira tickets.
allowed_tools: [Read, Task]
---

# Purpose

Fix a bug based on your direct description. **No Jira ticket required.**

Use this when you have a bug to fix but no Jira ticket associated with it.

**CRITICAL**: Do NOT fix the bug yourself. Spawn the `bug-fix-orchestrator` agent.

## When to Use This vs /fix-bugs-jira

| Scenario | Command |
|----------|---------|
| You have a bug description, no Jira ticket | `/fix-bug-direct "..."` ← **This one** |
| You have a Jira ticket with bugs listed | `/fix-bugs-jira TICKET-ID` |

## Usage

```
/fix-bug-direct "Login fails when password contains special characters"
/fix-bug-direct "Dashboard shows wrong date format for Australian users"
```

## What To Do

**IMMEDIATELY spawn the orchestrator. Do NOT do any work yourself.**

```
[main] Detected bug fix request
[main] Spawning bug-fix-orchestrator...

Task: spawn bug-fix-orchestrator
Prompt: |
  Fix bug based on user description.
  $BUG_DESCRIPTION = [THE USER'S BUG DESCRIPTION]
  $REPOS_ROOT = [current working directory]
```

That's it. The orchestrator handles everything:
1. Spawns `bug-fixer` to find and apply the fix
2. Spawns `backend-pattern-validator` or `frontend-pattern-validator`
3. Spawns `commit-manager` to commit
4. Returns summary to user

## Flow Diagram

```
/fix-bug-direct "description"
       │
       ▼
┌──────────────────────┐
│ bug-fix-orchestrator │ ◄── You spawn ONLY this
└──────────┬───────────┘
           │
           ├──► bug-fixer (Step 1)
           │         │
           │         ▼
           ├──► pattern-validator (Step 2)
           │         │
           │         ▼
           └──► commit-manager (Step 3)
                     │
                     ▼
               Report to user
```

## Related Commands

- `/fix-bugs-jira TICKET-ID` - Fix bugs from Jira ticket (uses bug-triage)
