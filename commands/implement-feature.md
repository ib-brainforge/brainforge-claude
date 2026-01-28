---
name: /implement-feature
description: Implement a feature end-to-end using the multi-agent system
allowed_tools: [Read, Task]
---

# Purpose

Implement a feature from start to finish: plan → build → validate → update deps → commit.

**CRITICAL**: Do NOT implement features yourself. Spawn `feature-implementor`.

## Usage

```
/implement-feature "Add inline-edit mode to BaseInput component"
/implement-feature "Add OAuth2 authentication to user-service"
```

## What To Do

**IMMEDIATELY spawn the orchestrator. Do NOT do any work yourself.**

```
[main] Detected feature implementation request
[main] Spawning feature-implementor...

Task: spawn feature-implementor
Prompt: |
  Implement feature end-to-end.
  Feature: [USER'S FEATURE DESCRIPTION]
  Target: [TARGET SERVICE if mentioned]
  $REPOS_ROOT = [current working directory]

  MUST complete full workflow:
  1. Plan
  2. Implement
  3. Validate
  4. Update dependencies (if core package changed)
  5. Commit all changes
```

## If User Answers a Question

When user provides feedback/decision during the workflow, **RE-SPAWN the orchestrator**:

```
[main] User provided decision, re-spawning feature-implementor...

Task: spawn feature-implementor
Prompt: |
  CONTINUE feature implementation with user decision.
  Original feature: [ORIGINAL DESCRIPTION]
  User decision: [WHAT USER CHOSE]
  Previous work: [SUMMARY OF WHAT WAS DONE]
  $REPOS_ROOT = [current working directory]

  Resume and complete remaining steps:
  - Validate all changes
  - Update dependencies in consuming projects
  - Commit everything
```

**NEVER continue the work yourself after user feedback!**

## Flow Diagram

```
/implement-feature "Add inline edit"
       │
       ▼
┌─────────────────────┐
│ feature-implementor │ ◄── You spawn ONLY this
└──────────┬──────────┘
           │
           ├──► feature-planner (Step 1: Plan)
           │
           ├──► [makes changes] (Step 2: Implement)
           │
           ├──► validators (Step 3: Validate)
           │         │
           │    ┌────┴────┐
           │    ▼         ▼
           │  backend   frontend
           │  validator validator
           │
           ├──► [update package.json] (Step 4: Deps)
           │
           └──► commit-manager (Step 5: Commit)
                     │
                     ▼
               Complete Report
```

## What Gets Committed

The `feature-implementor` ensures ALL changes are committed:

1. **Core package changes** (if any)
2. **Consumer project updates** (package.json version bumps)
3. **Feature implementation** in target service

## Related Commands

- `/plan-feature "description"` - Planning only (no implementation)
- `/fix-bug "description"` - Fix a single bug
- `/validate` - Validate architecture
