# Architecture Validation & Multi-Agent System

## CRITICAL: Agent Routing Rules

**You MUST use the multi-agent system for these requests. Do NOT do the work yourself.**

| User Request Pattern | Agent to Spawn | Command |
|---------------------|----------------|---------|
| "fix bugs from Jira/ticket" | `bug-triage` | `/fix-bugs-jira TICKET-ID` |
| "fix bug" / "there's a bug" / "I noticed a bug" | `bug-fix-orchestrator` | `/fix-bug-direct "description"` |
| "plan feature" / "analyze feature" (simple) | `feature-planner` | `/plan-feature "description"` |
| "plan feature" (multi-perspective) | `planning-council` | `/plan-council "description"` |
| "implement feature" / "build feature" | `feature-implementor` | `/implement-feature "description"` |
| "validate/check architecture" | `validation` skill | `/validate` |
| "commit changes" | `commit-manager` | `/commit` |
| "update packages" | `package-release` skill | `/update-packages` |
| "knowledge is wrong" / "we actually use X" / "fix knowledge" | `knowledge-investigator` | `/update-knowledge "description"` |
| "create/update grafana dashboard" | `grafana-dashboard-manager` | `/update-dashboard SERVICE` |
| "write docs" / "create documentation" / "document..." | `confluence-writer` | `/write-docs "topic"` |
| "sync docs to Confluence" / "sync documentation" | `docs-sync-agent` | `/sync-docs` |
| "implement infra" / "add kubernetes" / "deploy service" / "infrastructure change" | `infrastructure-implementor` | `/implement-infra "description"` |

---

## 📋 Command Decision Trees

### Bug Fixing Decision Tree

```
Do you have a bug to fix?
    │
    ├── YES, I have a Jira ticket
    │   └── Use: /fix-bugs-jira TICKET-ID
    │       → Fetches ticket, parses bugs, fixes all, updates Jira
    │
    └── YES, but NO Jira ticket (just a description)
        └── Use: /fix-bug-direct "description"
            → Fixes the bug directly from your description
```

### Planning & Implementation Decision Tree

```
Do you want to plan or implement a feature?
    │
    ├── JUST PLAN (don't implement yet)
    │   │
    │   ├── I want a quick, focused plan
    │   │   └── Use: /plan-feature "description"
    │   │       → Single perspective, fast, uses validators
    │   │
    │   └── I want multiple perspectives / thorough analysis
    │       └── Use: /plan-council "description"
    │           → Spawns N agents with different viewpoints
    │           → Pragmatic, Architectural, Risk-Aware, User-Centric, Performance
    │
    └── PLAN AND IMPLEMENT (full workflow)
        └── Use: /implement-feature "description"
            → Plans THEN implements THEN validates THEN commits
            → Complete end-to-end workflow
```

### Documentation Decision Tree

```
Do you need documentation on Confluence?
    │
    ├── CREATE new documentation (from codebase exploration)
    │   └── Use: /write-docs "topic"
    │       → Uses confluence-writer agent
    │       → Explores code, writes docs, pushes to Confluence
    │       → Best for: New technical/business documentation
    │
    └── SYNC existing documentation (repo ↔ Confluence)
        └── Use: /sync-docs
            → Uses docs-sync-agent
            → Bidirectional sync between repos and Confluence
            → Best for: Keeping existing docs in sync
```

### Telemetry Decision Tree

```
Do you want to see agent execution info?
    │
    └── Use: /agent-telemetry
        │
        ├── --stats     → Aggregate summary (tokens, agents, warnings)
        ├── --trace     → Full execution tree of last workflow
        ├── --context   → Context usage breakdown by agent
        ├── --warnings  → Show only warnings
        └── --parallel  → Parallel execution analysis
```

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

---

## ⚠️ CRITICAL: Interactive Questions for Blockers

**PROBLEM**: Subagents output text when they hit blockers, then stop silently. User has no interactive way to respond.

**SOLUTION**: All orchestrating agents MUST use `AskUserQuestion` when they hit blockers requiring user decisions.

### When to Use AskUserQuestion (not just output text)

| Blocker Type | Example | Required Action |
|--------------|---------|-----------------|
| HTTP 4xx/5xx error | `400: Quiz must have questions` | Ask: create test data, skip, investigate, abort? |
| Multiple valid approaches | "Could use polling or WebSocket" | Ask: which approach? |
| Missing resource | "Entity doesn't exist" | Ask: create it, skip, abort? |
| Validation failure | "Pattern check failed" | Ask: proceed anyway, fix, abort? |
| Ambiguous requirement | "Not clear if X or Y" | Ask: clarify the requirement |
| Can't determine root cause | "Multiple possible causes" | Ask: which to investigate? |
| Build/test failure | "Build failed after 3 attempts" | Ask: show error, skip, abort? |
| Merge conflict | "Conflict with develop" | Ask: show conflicts, abort, reset? |

### Required Behavior

```markdown
# WRONG - just outputs text and stops
[feature-implementor] Error: Quiz must have at least one question.
What should I do?

# CORRECT - uses interactive question
[feature-implementor] Error encountered. Asking user...
AskUserQuestion:
  questions:
    - question: "API returned '400: Quiz must have questions'. How should I proceed?"
      header: "API Error"
      options:
        - label: "Create test quiz data"
          description: "I'll add sample questions so the endpoint works"
        - label: "Skip this step"
          description: "Continue, test manually later"
        - label: "Show me the error"
          description: "I'll show the full error for investigation"
        - label: "Abort workflow"
          description: "Stop the implementation"
      multiSelect: false
```

### After User Responds

The subagent continues with the user's decision. If the subagent already exited, the main conversation re-spawns it with context including the user's choice.

---

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

**For infrastructure implementation:**
```
Task: spawn infrastructure-implementor
Prompt: |
  Implement infrastructure changes.
  Feature: [USER'S DESCRIPTION]
  $INFRA_ROOT = [path to infrastructure repository]
  $REPOS_ROOT = [path to repos]

  Complete all work autonomously:
  1. Analyze existing patterns
  2. Create/modify Kubernetes resources
  3. Validate manifests
  4. Report changes with REVIEW: comments
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
| `/fix-bugs-jira TICKET-ID` | Fix bugs from Jira ticket (uses bug-triage) |
| `/fix-bug-direct "description"` | Fix single bug you describe (no Jira needed) |
| `/plan-feature "description"` | Plan feature (single perspective, fast) |
| `/plan-council "description"` | Plan feature (N perspectives in parallel, thorough) |
| `/implement-feature "description"` | Plan AND implement feature (full workflow) |
| `/validate` | Run architecture validation |
| `/commit` | Generate and execute commits |
| `/agent-telemetry` | Show agent execution info (--stats, --trace, --context, --warnings) |
| `/update-knowledge "misconception"` | Investigate & correct wrong knowledge (fixes *.md files) |
| `/update-dashboard SERVICE` | Create/update Grafana dashboard for service observability |
| `/write-docs "topic"` | Create technical/business documentation on Confluence |
| `/sync-docs` | Sync existing documentation between repos and Confluence |
| `/implement-infra "description"` | Implement infrastructure changes (Kubernetes, GitOps, IaC) |
| `/git-sync` | Sync current feature branch with latest develop (prevents merge conflicts) |
| `/git-cleanup` | Clean up after merged PR (switch to develop, delete old feature branch) |

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
- `infrastructure-implementor` - Implements Kubernetes/GitOps/IaC changes (spawned by feature-implementor or directly)
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
    │    ┌────────────────┬────────────────┬────────────────┬────────────────┐
    │    │ backend-impl   │ frontend-impl  │ core-impl      │ infra-impl     │
    │    │ (.cs files)    │ (.tsx files)   │ (packages)     │ (k8s/gitops)   │
    │    └───────┬────────┴───────┬────────┴───────┬────────┴───────┬────────┘
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

## ⚠️ Build Verification - HARD GATE

**ALL code changes MUST pass build and tests before commit.**

Each implementor/fixer runs build & test after their work:
- **Backend**: `dotnet build && dotnet test`
- **Frontend**: `pnpm build && pnpm test`

The orchestrator runs a final verification before commit step.

If build fails after 3 attempts, use `AskUserQuestion` to ask user how to proceed.

---

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
3. **Always sync with develop before finishing** (prevents merge conflicts)
4. **Always create PR back to develop**
5. **All orchestrators call `git-workflow-manager` at START and END**

**Branch naming:**
- Features: `feature/[ticket]-[description]` or `feature/[description]`
- Fixes: `fix/[ticket]-[description]` or `fix/[description]`

**The `git-workflow-manager` agent enforces this and is called by:**
- `feature-implementor` (Step 0 and Step 7)
- `bug-fix-orchestrator` (Step 0 and Step 5)
- `bug-triage` (Step 0 and Step 10)

**Git Workflow Lifecycle:**
```
1. START: git-workflow-manager (start-feature)
   └── Pull latest develop, create/checkout feature branch
   └── If branch exists: merge latest develop into it

2. WORK: Implement, build, test, commit

3. SYNC (optional): /git-sync
   └── Merge latest develop into feature branch mid-work

4. FINISH: git-workflow-manager (finish-feature)
   └── Sync with develop, push, create PR

5. AFTER MERGE: /git-cleanup
   └── Switch to develop, pull, delete old feature branch
```

## Knowledge Files

All agents load patterns from `knowledge/`:
- `knowledge/architecture/` - System design, boundaries
- `knowledge/validation/` - Pattern validation rules
- `knowledge/packages/` - Package config
- `knowledge/jira/` - Jira config
- `knowledge/infrastructure/` - Infrastructure patterns (Kubernetes, GitOps, IaC)

## Single Writer Pattern

**ONLY `commit-manager` writes to learned YAML files.**
All other agents READ from knowledge but do NOT write.

This prevents concurrent write conflicts.
