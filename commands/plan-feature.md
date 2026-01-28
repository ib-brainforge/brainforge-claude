---
name: /plan-feature
description: Plan and analyze a feature using the multi-agent system
allowed_tools: [Read, Task]
---

# Purpose

Analyze a feature request and create a comprehensive implementation plan using the agent swarm.
This command delegates to the `feature-planner` agent which orchestrates multiple subagents.

**CRITICAL**: Do NOT attempt to plan or analyze features yourself. The feature-planner agent handles everything.

## Usage

```
/plan-feature TICKET-ID
/plan-feature "Feature description"
```

## Arguments

- `TICKET_ID` or `FEATURE_DESCRIPTION`: Either a Jira ticket ID (e.g., PROJ-123) or a quoted feature description

## Workflow

### 1. Determine Input Type

If argument looks like a ticket ID (e.g., PROJ-123, BF-456):
- Will fetch from Jira first

If argument is a description:
- Use directly as feature description

### 2. Spawn feature-planner Agent

```
Task: spawn feature-planner
Prompt: |
  Plan feature implementation.

  Input: [TICKET_ID or FEATURE_DESCRIPTION]
  $REPOS_ROOT = [current working directory]
  $OUTPUT_DIR = ./plans

  If ticket ID provided:
  - Fetch ticket details from Jira first
  - Extract feature requirements from ticket

  Workflow:
  1. Analyze feature requirements
  2. Discover affected services
  3. Spawn architectural subagents (parallel):
     - master-architect
     - frontend-pattern-validator
     - backend-pattern-validator
     - core-validator
     - infrastructure-validator
  4. Synthesize implementation plan
  5. Validate plan with plan-validator
  6. Output plan document and task breakdown
```

### 3. Return Results

The feature-planner will return:
- Implementation plan document
- Task breakdown (phases, dependencies)
- Validation status
- Estimated effort

## What Gets Spawned

```
/plan-feature PROJ-123
       │
       ▼
┌─────────────────┐
│ feature-planner │ ◄── Main orchestrator
└────────┬────────┘
         │
         ├──► jira-integration (if ticket ID)
         │
         ├──► master-architect ──────────┐
         ├──► frontend-pattern-validator │ Parallel
         ├──► backend-pattern-validator  │ consultation
         ├──► core-validator ────────────┤
         └──► infrastructure-validator ──┘
                      │
                      ▼
              ┌───────────────┐
              │ plan-validator│
              └───────────────┘
                      │
                      ▼
               Output: Plan + Tasks
```

## Example Output Location

```
./plans/feature-PROJ-123-plan.md
./plans/feature-PROJ-123-tasks.json
```

## Related Commands

- `/fix-bugs TICKET-ID` - Fix bugs from a Jira ticket
- `/validate` - Validate current architecture
