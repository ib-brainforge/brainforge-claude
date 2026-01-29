# Bug Fix Workflow Pattern

This document defines the shared workflow pattern used by both `bug-fix-orchestrator` and `bug-triage` agents.

## Common Workflow Steps

Both bug-fixing agents follow the same core workflow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SHARED BUG FIX WORKFLOW PATTERN                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 0: GIT SETUP (HARD GATE)                                              │
│     └──► Spawn git-workflow-manager (ACTION=start-feature)                  │
│     └──► Pull latest develop, create fix branch                             │
│     └──► Branch: fix/[ticket-id] or fix/[description]                       │
│                                                                              │
│  STEP 1: FIX THE BUG(S)                                                      │
│     └──► Spawn bug-fixer agent(s)                                           │
│     └──► Capture: files_modified, status, business summary                   │
│     └──► If failed → STOP and report                                         │
│                                                                              │
│  STEP 2: BUILD VERIFICATION (HARD GATE)                                     │
│     └──► dotnet build + dotnet test (backend)                               │
│     └──► pnpm build + pnpm test (frontend)                                  │
│     └──► Must pass before proceeding                                        │
│                                                                              │
│  STEP 3: PATTERN VALIDATION                                                  │
│     └──► Determine validator type from file extensions                       │
│     └──► Spawn backend-pattern-validator (for .cs files)                     │
│     └──► Spawn frontend-pattern-validator (for .tsx/.ts files)               │
│     └──► If validation fails → STOP and report                               │
│                                                                              │
│  STEP 4: COMMIT CHANGES                                                      │
│     └──► Spawn commit-manager                                                │
│     └──► Include business description in commit                              │
│                                                                              │
│  STEP 5: CREATE PR (HARD GATE)                                              │
│     └──► Spawn git-workflow-manager (ACTION=finish-feature)                 │
│     └──► Push fix branch, create GitHub PR to develop                       │
│                                                                              │
│  STEP 6: REPORT                                                              │
│     └──► Generate business-focused summary table with PR link               │
│     └──► Return complete report                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Differences

| Aspect | bug-fix-orchestrator | bug-triage |
|--------|---------------------|------------|
| **Entry Point** | `/fix-bug-direct "description"` | `/fix-bugs-jira TICKET-ID` |
| **Input Source** | Direct user description | Jira ticket |
| **Bug Count** | Single bug | Multiple bugs |
| **Jira Integration** | No | Yes (fetch, update, comment) |
| **Branch Naming** | `fix/[description]` | `fix/[TICKET-ID]` |
| **Post-Fix Action** | Report only | Update Jira ticket |

## Shared Components

### 1. Git Workflow Manager Integration

Both agents MUST use `git-workflow-manager` for:
- **Start**: Pull latest develop, create feature branch
- **Finish**: Sync with develop, push, create PR

### 2. Build Verification

Both agents MUST verify builds pass before committing:
```bash
# Backend
cd $REPO && dotnet build --no-restore && dotnet test --no-build

# Frontend
cd $REPO && pnpm build && pnpm test --passWithNoTests
```

After 3 failures, use `AskUserQuestion` to ask user how to proceed.

### 3. Pattern Validation

Both agents MUST spawn validators based on file types:
- `.cs`, `.csproj` → `backend-pattern-validator`
- `.tsx`, `.ts`, `.jsx`, `.js` → `frontend-pattern-validator`

### 4. Commit Manager

Both agents MUST use `commit-manager` with:
- Type: `fix`
- Scope: Affected service name
- Description: Business-focused resolution

### 5. Business-Focused Reporting

Both agents MUST produce **business-focused** summaries:

```
| Issue | Resolution |
|-------|------------|
| [What user experienced] | [What now works] |
```

**NOT** technical details like file names or function calls.

## Why Two Agents?

While the core workflow is identical, the agents differ in:

1. **Entry point complexity**: Jira requires ticket fetching and parsing
2. **Multi-bug handling**: bug-triage handles prioritization and parallel fixing
3. **Jira lifecycle**: bug-triage updates ticket status and adds comments
4. **Branch naming convention**: Jira-based uses ticket ID

## Shared Knowledge Files

Both agents load:
- `knowledge/architecture/system-architecture.md` - Service map
- `knowledge/architecture/service-boundaries.md` - Service dependencies

Additionally, `bug-triage` loads:
- `knowledge/jira/jira-config.md` - Jira configuration
