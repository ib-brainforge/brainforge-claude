---
name: /plan-council
description: Multi-perspective feature planning with N parallel agents
allowed_tools: [Read, Task]
---

# Purpose

Get multiple perspectives on how to implement a feature. Spawns N planning agents
in parallel (configured via `PLANNING_AGENTS_COUNT` env var, default 5).

Each agent analyzes from a different perspective:
1. **Pragmatic** - Fastest path, minimal changes
2. **Architectural** - Long-term maintainability
3. **Risk-Aware** - Edge cases, security, rollback
4. **User-Centric** - UX impact, accessibility
5. **Performance** - Efficiency, optimization

**CRITICAL**: Do NOT plan yourself. Spawn `planning-council`.

## Usage

```
/plan-council "Add inline-edit mode to form fields"
/plan-council "Implement OAuth2 authentication"
```

## Configuration

Set in `.env` file:
```bash
PLANNING_AGENTS_COUNT=5   # Number of parallel planning agents
```

## What To Do

**IMMEDIATELY spawn the orchestrator. Do NOT do any work yourself.**

```
[main] Detected multi-perspective planning request
[main] Spawning planning-council...

Task: spawn planning-council
Prompt: |
  Analyze feature from multiple perspectives.
  Feature: [USER'S FEATURE DESCRIPTION]
  Target: [TARGET SERVICE if mentioned]
  $REPOS_ROOT = [current working directory]

  Spawn $PLANNING_AGENTS_COUNT plan-analyst agents in parallel.
  Each with different perspective.
  Aggregate results and present unified comparison.
```

## Flow Diagram

```
/plan-council "Add inline edit"
       │
       ▼
┌─────────────────┐
│ planning-council│ ◄── You spawn ONLY this
└────────┬────────┘
         │ (reads PLANNING_AGENTS_COUNT from .env)
         │
         ├──► plan-analyst (Pragmatic)    ─┐
         ├──► plan-analyst (Architectural) │
         ├──► plan-analyst (Risk-Aware)    ├── PARALLEL
         ├──► plan-analyst (User-Centric)  │
         └──► plan-analyst (Performance)  ─┘
                      │
                      ▼
              ┌──────────────┐
              │  Aggregate   │
              │  & Compare   │
              └──────┬───────┘
                     │
                     ▼
              Present 5 approaches
              with recommendation
```

## Output Example

```
# Feature Planning: Add inline-edit mode

## Common Ground (All Agents Agree)
- Add `editable` prop to BaseInput
- Create useEditableState hook

## Approaches

### 1. Pragmatic Approach ⚡
Reuse existing EditableText component...
**Effort:** 6 hours | **Risk:** Low

### 2. Architectural Approach 🏗️
Create new Editable HOC pattern...
**Effort:** 12 hours | **Risk:** Low

### 3. Risk-Aware Approach 🛡️
Add validation layer and rollback...
**Effort:** 10 hours | **Risk:** Very Low

### 4. User-Centric Approach 👤
Focus on click-to-edit UX with feedback...
**Effort:** 8 hours | **Risk:** Medium

### 5. Performance Approach ⚡
Lazy-load edit mode, optimize re-renders...
**Effort:** 10 hours | **Risk:** Medium

## 🎯 Recommendation: User-Centric
This is a user-facing feature, UX should be priority.

**Which approach would you like to proceed with?**
```

## After User Chooses

When user selects an approach, spawn `feature-implementor`:

```
[main] User selected: User-Centric approach
[main] Spawning feature-implementor...

Task: spawn feature-implementor
Prompt: |
  Implement feature using User-Centric approach.
  Feature: Add inline-edit mode
  Approach: [details from plan-analyst User-Centric]
  $REPOS_ROOT = [path]
```

## Related Commands

- `/plan-feature "description"` - Single-perspective planning (faster, simpler)
- `/implement-feature "description"` - Skip planning, go straight to implementation
