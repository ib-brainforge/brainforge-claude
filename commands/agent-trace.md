# /agent-trace Command

Show the complete execution trace of a workflow - who spawned who, what ran, what was validated.

## Usage

```
/agent-trace                    # Show last workflow trace
/agent-trace --session ID       # Show specific session
/agent-trace --last N           # Show last N workflows
```

## Purpose

When you run `/implement-feature` or `/fix-bug`, many agents are spawned. This command shows:
- **Full execution tree** - Every agent that ran
- **What validators ran** - backend, frontend, core validators
- **Git workflow steps** - branch creation, PR creation
- **Timing** - How long each step took
- **Status** - What passed, what failed

## Commands to Execute

### Show Last Workflow Trace

```bash
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                        WORKFLOW EXECUTION TRACE                            ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Find the last workflow (feature-implementor, bug-fix-orchestrator, or bug-triage)
LAST_WORKFLOW=$(grep -E "\[START\].*\[(feature-implementor|bug-fix-orchestrator|bug-triage)\]" .claude/agent-activity.log | tail -1)

if [ -z "$LAST_WORKFLOW" ]; then
  echo "No workflow found in logs."
  exit 0
fi

# Extract session info
WORKFLOW_ID=$(echo "$LAST_WORKFLOW" | grep -oP 'id=\K[^ ]+')
WORKFLOW_NAME=$(echo "$LAST_WORKFLOW" | grep -oP '\[START\] \[\K[^\]]+')
WORKFLOW_START=$(echo "$LAST_WORKFLOW" | grep -oP '^\[[^\]]+' | tr -d '[]')

echo "Workflow: $WORKFLOW_NAME"
echo "ID: $WORKFLOW_ID"
echo "Started: $WORKFLOW_START"
echo ""

# Find all related agents (same parent chain)
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                           EXECUTION TREE                                     │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Build tree from logs - get all entries after workflow start
WORKFLOW_START_LINE=$(grep -n "$WORKFLOW_ID" .claude/agent-activity.log | head -1 | cut -d: -f1)

# Show all START/COMPLETE after that line
tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -E "\[START\]|\[COMPLETE\]|\[SPAWN\]" | head -50 | while read line; do
  TIMESTAMP=$(echo "$line" | grep -oP '^\[[^\]]+' | tr -d '[]' | cut -dT -f2 | cut -d+ -f1)

  if echo "$line" | grep -q "\[START\]"; then
    AGENT=$(echo "$line" | grep -oP '\[START\] \[\K[^\]]+')
    DEPTH=$(echo "$line" | grep -oP 'depth=\K[0-9]+' || echo "0")
    MODEL=$(echo "$line" | grep -oP 'model=\K[a-z]+' || echo "?")
    INDENT=$(printf '%*s' $((DEPTH * 4)) '')

    # Color coding based on agent type
    ICON="▶"
    if echo "$AGENT" | grep -q "validator"; then ICON="🔍"; fi
    if echo "$AGENT" | grep -q "git-workflow"; then ICON="🔀"; fi
    if echo "$AGENT" | grep -q "commit"; then ICON="💾"; fi
    if echo "$AGENT" | grep -q "planner\|council\|analyst"; then ICON="📋"; fi
    if echo "$AGENT" | grep -q "fixer"; then ICON="🔧"; fi

    printf "%s %s├── %s %s [%s]\n" "$TIMESTAMP" "$INDENT" "$ICON" "$AGENT" "$MODEL"
  fi

  if echo "$line" | grep -q "\[COMPLETE\]"; then
    AGENT=$(echo "$line" | grep -oP '\[COMPLETE\] \[\K[^\]]+')
    STATUS=$(echo "$line" | grep -oP 'status=\K[A-Z]+')
    DURATION=$(echo "$line" | grep -oP 'duration=\K[0-9]+')
    TOKENS=$(echo "$line" | grep -oP 'tokens=\K[0-9]+')
    DEPTH=$(echo "$line" | grep -oP 'depth=\K[0-9]+' || echo "0")
    INDENT=$(printf '%*s' $((DEPTH * 4)) '')

    # Status icon
    STATUS_ICON="✓"
    if [ "$STATUS" = "WARN" ]; then STATUS_ICON="⚠"; fi
    if [ "$STATUS" = "FAIL" ]; then STATUS_ICON="✗"; fi

    printf "%s %s└── %s %s (%ss, %s tokens)\n" "$TIMESTAMP" "$INDENT" "$STATUS_ICON" "$AGENT" "$DURATION" "$TOKENS"
  fi
done

echo ""
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                           VALIDATION SUMMARY                                 │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Extract validator results
echo "Validators Run:"
tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -E "\[COMPLETE\].*validator" | head -10 | while read line; do
  VALIDATOR=$(echo "$line" | grep -oP '\[\K[^\]]+(?=-validator\])')
  STATUS=$(echo "$line" | grep -oP 'status=\K[A-Z]+')

  if [ "$STATUS" = "PASS" ]; then
    echo "  ✅ ${VALIDATOR}-validator: PASS"
  elif [ "$STATUS" = "WARN" ]; then
    echo "  ⚠️  ${VALIDATOR}-validator: WARN"
  else
    echo "  ❌ ${VALIDATOR}-validator: FAIL"
  fi
done

# Check if no validators ran
if ! tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -q "validator"; then
  echo "  ⚠️  No validators were run!"
fi

echo ""
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                           GIT WORKFLOW                                       │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Extract git workflow steps
tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep "git-workflow-manager" | head -10 | while read line; do
  if echo "$line" | grep -q "\[START\]"; then
    ACTION=$(echo "$line" | grep -oP 'action="\K[^"]+' || echo "unknown")
    echo "  🔀 Started: $ACTION"
  fi
  if echo "$line" | grep -q "\[COMPLETE\]"; then
    STATUS=$(echo "$line" | grep -oP 'status=\K[A-Z]+')
    PRS=$(echo "$line" | grep -oP 'prs=\K[0-9]+' || echo "0")
    if [ "$STATUS" = "SUCCESS" ] || [ "$STATUS" = "PASS" ]; then
      echo "  ✅ Completed: $PRS PRs created"
    else
      echo "  ❌ Failed"
    fi
  fi
done

# Check if git workflow didn't run
if ! tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -q "git-workflow-manager"; then
  echo "  ⚠️  Git workflow manager was NOT invoked!"
  echo "     (Changes may not have been pushed to a feature branch)"
fi

echo ""
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                              SUMMARY                                         │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Count agents
AGENT_COUNT=$(tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -c "\[COMPLETE\]" | head -1)
TOTAL_TOKENS=$(tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep "\[COMPLETE\]" | head -20 | grep -oP 'tokens=\K[0-9]+' | awk '{sum+=$1} END {print sum}')
TOTAL_DURATION=$(tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep "\[COMPLETE\]" | head -20 | grep -oP 'duration=\K[0-9]+' | awk '{sum+=$1} END {print sum}')

echo "  Agents spawned:    $AGENT_COUNT"
echo "  Total tokens:      $TOTAL_TOKENS"
echo "  Total duration:    ${TOTAL_DURATION}s"
echo ""

# Final status
WORKFLOW_END=$(tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -E "\[COMPLETE\].*\[$WORKFLOW_NAME\]" | head -1)
if [ -n "$WORKFLOW_END" ]; then
  FINAL_STATUS=$(echo "$WORKFLOW_END" | grep -oP 'status=\K[A-Z]+')
  if [ "$FINAL_STATUS" = "PASS" ] || [ "$FINAL_STATUS" = "SUCCESS" ]; then
    echo "  Final Status: ✅ $FINAL_STATUS"
  else
    echo "  Final Status: ❌ $FINAL_STATUS"
  fi
else
  echo "  Final Status: ⏳ Still running or incomplete"
fi
echo ""
```

## Example Output

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        WORKFLOW EXECUTION TRACE                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

Workflow: feature-implementor
ID: fi-1738012345678
Started: 2026-01-27T14:30:00+01:00

┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION TREE                                     │
└─────────────────────────────────────────────────────────────────────────────┘

14:30:00 ├── ▶ feature-implementor [sonnet]
14:30:02     ├── 🔀 git-workflow-manager [sonnet]
14:30:05     └── ✓ git-workflow-manager (3s, 1200 tokens)
14:30:06     ├── 📋 feature-planner [opus]
14:30:45     └── ✓ feature-planner (39s, 8500 tokens)
14:30:46     ├── 🔧 (implementation - direct edits)
14:31:20     ├── 🔍 backend-pattern-validator [sonnet]
14:31:35     └── ✓ backend-pattern-validator (15s, 4200 tokens)
14:31:36     ├── 🔍 frontend-pattern-validator [sonnet]
14:31:52     └── ✓ frontend-pattern-validator (16s, 3800 tokens)
14:31:53     ├── 💾 commit-manager [sonnet]
14:32:10     └── ✓ commit-manager (17s, 3500 tokens)
14:32:11     ├── 🔀 git-workflow-manager [sonnet]
14:32:25     └── ✓ git-workflow-manager (14s, 2100 tokens)
14:32:26 └── ✓ feature-implementor (146s, 25000 tokens)

┌─────────────────────────────────────────────────────────────────────────────┐
│                           VALIDATION SUMMARY                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Validators Run:
  ✅ backend-pattern-validator: PASS
  ✅ frontend-pattern-validator: PASS

┌─────────────────────────────────────────────────────────────────────────────┐
│                           GIT WORKFLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

  🔀 Started: start-feature
  ✅ Completed: Branch feature/BF-123-add-lease-date created
  🔀 Started: finish-feature
  ✅ Completed: 2 PRs created

┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUMMARY                                         │
└─────────────────────────────────────────────────────────────────────────────┘

  Agents spawned:    7
  Total tokens:      48300
  Total duration:    146s

  Final Status: ✅ PASS
```

## What It Shows

| Section | Information |
|---------|-------------|
| **Execution Tree** | Visual tree of all agents spawned, with timing and tokens |
| **Validation Summary** | Which validators ran and their status |
| **Git Workflow** | Branch creation, PR creation status |
| **Summary** | Total agents, tokens, duration, final status |

## Icons

| Icon | Meaning |
|------|---------|
| ▶ | Generic agent start |
| 📋 | Planning agent (planner, council, analyst) |
| 🔧 | Fixer agent (bug-fixer, implementation) |
| 🔍 | Validator agent |
| 🔀 | Git workflow agent |
| 💾 | Commit manager |
| ✓ | Completed successfully |
| ⚠ | Completed with warnings |
| ✗ | Failed |

## Troubleshooting

**"No validators were run!"**
- The workflow may have skipped validation
- Check if `feature-implementor` or `bug-fix-orchestrator` was used
- Direct edits without orchestrators don't run validators

**"Git workflow manager was NOT invoked!"**
- Changes may have been committed directly to current branch
- No PR was created
- Use `/implement-feature` or `/fix-bug` to ensure proper workflow

## Related Commands

- `/agent-stats` - Overall telemetry dashboard
- `/implement-feature` - Runs full workflow with validation
- `/fix-bug` - Runs full fix workflow with validation
