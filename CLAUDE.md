# Architecture Validation & Multi-Agent System

## CRITICAL: Agent Routing Rules

**You MUST use the multi-agent system for these requests. Do NOT do the work yourself.**

| User Request Pattern | Agent to Spawn | Command |
|---------------------|----------------|---------|
| "fix bugs from Jira/ticket" | `bug-triage` | `/fix-bugs TICKET-ID` |
| "fix bug" / "there's a bug" / "I noticed a bug" | `bug-fix-orchestrator` | `/fix-bug "description"` |
| "plan feature" / "analyze feature" (simple) | `feature-planner` | `/plan-feature "description"` |
| "plan feature" (multi-perspective) | `planning-council` | `/plan-council "description"` |
| "implement feature" / "build feature" | `feature-implementor` | `/implement-feature "description"` |
| "validate/check architecture" | `validation` skill | `/validate` |
| "commit changes" | `commit-manager` | `/commit` |
| "update packages" | `package-release` skill | `/update-packages` |
| "knowledge is wrong" / "we actually use X" / "fix knowledge" | `knowledge-investigator` | `/update-knowledge "description"` |
| "create/update grafana dashboard" | `grafana-dashboard-manager` | `/update-dashboard SERVICE` |
| "write docs" / "create documentation" / "document..." | `confluence-writer` | `/write-docs "topic"` |

---

## ⚠️ CRITICAL: Never Break Orchestration

**PROBLEM**: When user answers a question, main conversation "takes over" and does work manually, skipping validation/commit/dependency updates.

**RULES**:
1. **NEVER do implementation work yourself** - Always spawn agents
2. **NEVER continue work after user feedback** - Re-spawn the orchestrator with context
3. **If user answers a question** - Spawn agent again with their answer included
4. **If agent reports needing decision** - After user decides, spawn agent again

**Example - WRONG:**
```
Agent: "Should I use approach A or B?"
User: "Use A"
Main: *starts implementing A directly* ← WRONG!
```

**Example - CORRECT:**
```
Agent: "Should I use approach A or B?"
User: "Use A"
Main: [main] Re-spawning feature-implementor with user decision...
Task: spawn feature-implementor
Prompt: |
  Continue feature implementation.
  User decision: Use approach A
  ... [include previous context]
```

**After ANY user interaction during a workflow, you MUST re-spawn the appropriate orchestrator.**

### How to Spawn Agents

When a request matches the patterns above, use the Task tool:

**For bug fixes (from Jira):**
```
Task: spawn bug-triage
Prompt: |
  Fix bugs from Jira ticket: [TICKET-ID]
  $TICKET_ID = [TICKET-ID]
  $REPOS_ROOT = [path to repos]
```

**For feature planning (no Jira needed):**
```
Task: spawn feature-planner
Prompt: |
  Plan feature implementation.
  Feature: [USER'S FEATURE DESCRIPTION]
  $REPOS_ROOT = [path to repos]
  $OUTPUT_DIR = ./plans
```

**For multi-perspective planning (spawns N agents in parallel):**
```
Task: spawn planning-council
Prompt: |
  Analyze feature from multiple perspectives.
  Feature: [USER'S FEATURE DESCRIPTION]
  Target: [TARGET SERVICE if specified]
  $REPOS_ROOT = [path to repos]

  Spawn $PLANNING_AGENTS_COUNT plan-analyst agents in parallel.
  Each with different perspective (Pragmatic, Architectural, Risk-Aware, User-Centric, Performance).
  Aggregate results and present comparison with recommendation.
```

**For feature implementation (plan + build):**
```
Task: spawn feature-implementor
Prompt: |
  Implement feature end-to-end.
  Feature: [USER'S FEATURE DESCRIPTION]
  Target: [TARGET SERVICE if specified]
  $REPOS_ROOT = [path to repos]

  MUST complete full workflow:
  1. Plan → 2. Implement → 3. Validate → 4. Update deps → 5. Commit
```

**After user answers a question mid-workflow:**
```
Task: spawn feature-implementor
Prompt: |
  CONTINUE feature implementation with user decision.
  Original feature: [FEATURE]
  User decision: [WHAT USER CHOSE]
  Previous context: [WHAT WAS DONE SO FAR]
  $REPOS_ROOT = [path to repos]

  Resume from step [N] and complete remaining steps.
```

**For single bug fix (no Jira):**
```
Task: spawn bug-fix-orchestrator
Prompt: |
  Fix bug based on user description.
  $BUG_DESCRIPTION = [USER'S BUG DESCRIPTION]
  $REPOS_ROOT = [path to repos]
```

**For knowledge correction:**
```
Task: spawn knowledge-investigator
Prompt: |
  Investigate and correct misconception.
  $MISCONCEPTION = [WHAT USER SAYS IS WRONG]
  $REPOS_ROOT = [path to repos]
  $KNOWLEDGE_AREA = all
```

**NEVER** do the agent's work yourself. The agents have:
- Specific workflows to follow
- Validation steps
- Knowledge file loading
- Observability (logging, prefixes)
- Proper error handling

### Observability

When spawning agents, prefix your output:
```
[main] Detected Jira bug fix request
[main] Spawning bug-triage agent for BF-119...
```

---

## Skills (Entry Points)

| Skill | Trigger | Description |
|-------|---------|-------------|
| `validation` | `/validate` | Run architecture validation |
| `feature-planning` | `/plan-feature "name" "desc"` | Plan feature implementation |
| `design-patterns` | `/patterns` | Validate/suggest design patterns |
| `commit-manager` | `/commit` | Generate commits across repos |
| `package-release` | `/update-packages` | Update NPM/NuGet packages |
| `docs-sync` | `/sync-docs` | Sync to Confluence |
| `jira-integration` | `/jira TICKET-ID` | Fetch/update Jira tickets |
| `knowledge-correction` | `/update-knowledge "..."` | Investigate & fix knowledge misconceptions |

## Commands

| Command | Description |
|---------|-------------|
| `/fix-bugs TICKET-ID` | Fix multiple bugs from Jira ticket (uses bug-triage) |
| `/fix-bug "description"` | Fix single bug you describe (no Jira needed) |
| `/plan-feature "description"` | Plan feature (single perspective, fast) |
| `/plan-council "description"` | Plan feature (N perspectives in parallel, thorough) |
| `/implement-feature "description"` | Plan AND implement feature (full workflow) |
| `/validate` | Run architecture validation |
| `/commit` | Generate and execute commits |
| `/agent-stats` | Show agent telemetry dashboard (tokens, call tree, warnings) |
| `/agent-trace` | Show full execution tree of last workflow (validators, git, timing) |
| `/update-knowledge "misconception"` | Investigate & correct wrong knowledge (fixes *.md files) |
| `/update-dashboard SERVICE` | Create/update Grafana dashboard for service observability |
| `/write-docs "topic"` | Write technical/business documentation to Confluence |

## Agent System

### Orchestrating Agents (spawn subagents)
- `bug-triage` - Orchestrates bug fixing from Jira (multi-bug)
- `bug-fix-orchestrator` - Orchestrates single bug fix (no Jira)
- `planning-council` - Multi-perspective planning (spawns N plan-analyst agents)
- `feature-planner` - Single-perspective planning (simpler/faster)
- `feature-implementor` - Implements features end-to-end (plan→build→validate→commit)
- `commit-manager` - Commits + records learnings (SINGLE WRITER for learned.yaml)
- `master-architect` - Architectural oversight
- `knowledge-investigator` - Investigates & corrects base knowledge (*.md files)
- `grafana-dashboard-manager` - Creates/updates Grafana dashboards for observability
- `confluence-writer` - Creates technical/business documentation on Confluence
- `git-workflow-manager` - **HARD GATE** for GitFlow (develop → feature branch → PR)

### Worker Agents (do specific tasks)
- `bug-fixer` - Applies individual bug fixes (spawned by orchestrators)
- `plan-analyst` - Analyzes from specific perspective (spawned by planning-council)
- `backend-implementor` - Implements C#/.NET code autonomously (spawned by feature-implementor)
- `frontend-implementor` - Implements React/TS code autonomously (spawned by feature-implementor)
- `core-implementor` - Implements shared package changes (spawned by feature-implementor)
- `backend-pattern-validator` - Validates C#/.NET patterns
- `frontend-pattern-validator` - Validates React/TS patterns
- `knowledge-updater` - Writes to learned YAML files (spawned by commit-manager)

### Workflow Pattern (Autonomous & Parallel)

```
User Request
    │
    ▼
[main] Detect request type
    │
    ▼
Task: spawn [orchestrator-agent]
    │
    ├──► [git-workflow-manager] HARD GATE: setup feature branch
    │
    ├──► [feature-planner] analyze & identify work streams
    │
    ├──► PARALLEL IMPLEMENTATION ←── KEY: Multiple implementors simultaneously
    │    ┌────────────────┬────────────────┬────────────────┐
    │    │ backend-impl   │ frontend-impl  │ core-impl      │
    │    │ (.cs files)    │ (.tsx files)   │ (packages)     │
    │    └───────┬────────┴───────┬────────┴───────┬────────┘
    │            └────────────────┴────────────────┘
    │                         WAIT FOR ALL
    │
    ├──► PARALLEL VALIDATION
    │    ┌────────────────────┬────────────────────┐
    │    │ backend-validator  │ frontend-validator │
    │    └────────────────────┴────────────────────┘
    │
    ├──► [commit-manager] commits all changes
    │
    ├──► [git-workflow-manager] HARD GATE: create PR to develop
    │
    └──► Returns report with PR link

NO STOPPING BETWEEN STEPS - Fully autonomous execution
Only stops for: security issues, breaking changes, unresolvable conflicts
```

## ⚠️ GitFlow - HARD GATE

**ALL code changes MUST go through this workflow:**

```
main (production)
  │
  └── develop (latest development)
        │
        ├── feature/BF-123-description
        ├── fix/BF-456-bug-description
        └── ...
```

**Rules:**
1. **Never commit directly to develop or main**
2. **Always create feature/fix branch from latest develop**
3. **Always create PR back to develop**
4. **All orchestrators call `git-workflow-manager` at START and END**

**Branch naming:**
- Features: `feature/[ticket]-[description]` or `feature/[description]`
- Fixes: `fix/[ticket]-[description]` or `fix/[description]`

**The `git-workflow-manager` agent enforces this and is called by:**
- `feature-implementor` (Step 0 and Step 6)
- `bug-fix-orchestrator` (Step 0 and Step 4)
- `bug-triage` (Step 0 and Step 8)

## Knowledge Files

All agents load patterns from `knowledge/`:
- `knowledge/architecture/` - System design, boundaries
- `knowledge/validation/` - Pattern validation rules
- `knowledge/packages/` - Package config
- `knowledge/jira/` - Jira config

## Single Writer Pattern

**ONLY `commit-manager` writes to learned YAML files.**
All other agents READ from knowledge but do NOT write.

This prevents concurrent write conflicts.
