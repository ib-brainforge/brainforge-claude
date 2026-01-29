---
name: /agent-telemetry
description: Show agent execution statistics, traces, and observability dashboard
allowed_tools: [Read, Bash]
---

# Purpose

Unified command for all agent telemetry and observability. Combines stats, traces, context usage, and warnings into a single command with flags.

## Usage

```
/agent-telemetry                    # Default: Show last session summary
/agent-telemetry --stats            # Aggregate statistics and summaries
/agent-telemetry --trace            # Full execution tree of last workflow
/agent-telemetry --context          # Context usage breakdown by agent
/agent-telemetry --warnings         # Show only warnings
/agent-telemetry --parallel         # Parallel execution analysis
/agent-telemetry --last N           # Show last N sessions
/agent-telemetry --session ID       # Show specific session
```

## Flag Combinations

You can combine flags:
```
/agent-telemetry --stats --warnings     # Stats with only warnings
/agent-telemetry --trace --context      # Tree with context breakdown
/agent-telemetry --last 5 --warnings    # Last 5 sessions, warnings only
```

---

## Commands to Execute

### Default / --stats: Session Summary

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "                    AGENT EXECUTION SUMMARY                     "
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get last session stats
LAST_SESSION=$(grep "\[SESSION\]" .claude/agent-activity.log | tail -1)
echo "Last Session: $LAST_SESSION"
echo ""

# Count agents
TOTAL_AGENTS=$(grep -c "\[COMPLETE\]" .claude/agent-activity.log | tail -1)
echo "Total Agents Spawned: $TOTAL_AGENTS"

# Total tokens
TOTAL_TOKENS=$(grep "\[COMPLETE\]" .claude/agent-activity.log | tail -20 | grep -oP 'tokens=\K[0-9]+' | awk '{sum+=$1} END {print sum}')
echo "Total Context Tokens: $TOTAL_TOKENS"

# Warnings
WARNINGS=$(grep -c "\[WARN\]" .claude/agent-activity.log | tail -1)
echo "Warnings: $WARNINGS"
echo ""
```

### --trace: Full Execution Tree

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

# Find all related agents
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                           EXECUTION TREE                                     │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Build tree from logs
WORKFLOW_START_LINE=$(grep -n "$WORKFLOW_ID" .claude/agent-activity.log | head -1 | cut -d: -f1)

tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -E "\[START\]|\[COMPLETE\]|\[SPAWN\]" | head -50 | while read line; do
  TIMESTAMP=$(echo "$line" | grep -oP '^\[[^\]]+' | tr -d '[]' | cut -dT -f2 | cut -d+ -f1)

  if echo "$line" | grep -q "\[START\]"; then
    AGENT=$(echo "$line" | grep -oP '\[START\] \[\K[^\]]+')
    DEPTH=$(echo "$line" | grep -oP 'depth=\K[0-9]+' || echo "0")
    MODEL=$(echo "$line" | grep -oP 'model=\K[a-z]+' || echo "?")
    INDENT=$(printf '%*s' $((DEPTH * 4)) '')

    # Icon coding
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

# Validation Summary
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                           VALIDATION SUMMARY                                 │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

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

if ! tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -q "validator"; then
  echo "  ⚠️  No validators were run!"
fi

echo ""

# Git Workflow
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│                           GIT WORKFLOW                                       │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo ""

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

if ! tail -n +$WORKFLOW_START_LINE .claude/agent-activity.log | grep -q "git-workflow-manager"; then
  echo "  ⚠️  Git workflow manager was NOT invoked!"
fi

echo ""
```

### --context: Context Usage Breakdown

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "                   CONTEXT USAGE BY AGENT                       "
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Agent                          | Model   | Tokens    | Status | Duration"
echo "-------------------------------|---------|-----------|--------|----------"

grep "\[COMPLETE\]" .claude/agent-activity.log | tail -20 | while read line; do
  AGENT=$(echo "$line" | grep -oP '\[\K[^\]]+(?=\] id=)')
  TOKENS=$(echo "$line" | grep -oP 'tokens=\K[0-9]+')
  STATUS=$(echo "$line" | grep -oP 'status=\K[A-Z]+')
  DURATION=$(echo "$line" | grep -oP 'duration=\K[0-9]+')
  MODEL=$(echo "$line" | grep -oP 'model=\K[a-z]+' || echo "sonnet")

  # Warning indicator
  INDICATOR=""
  if [ "$TOKENS" -gt 15000 ]; then INDICATOR="⚠️ "; fi
  if [ "$TOKENS" -gt 30000 ]; then INDICATOR="🔴 "; fi

  printf "%-30s | %-7s | %9s | %6s | %6ss %s\n" "$AGENT" "$MODEL" "$TOKENS" "$STATUS" "$DURATION" "$INDICATOR"
done

echo ""
echo "Legend: ⚠️  = >15k tokens (consider splitting)  🔴 = >30k tokens (should split)"
echo ""

# Total
TOTAL=$(grep "\[COMPLETE\]" .claude/agent-activity.log | tail -20 | grep -oP 'tokens=\K[0-9]+' | awk '{sum+=$1} END {print sum}')
echo "TOTAL CONTEXT: $TOTAL tokens"
echo ""
```

### --warnings: Show Warnings Only

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "                        WARNINGS                                "
echo "═══════════════════════════════════════════════════════════════"
echo ""

grep "\[WARN\]" .claude/agent-activity.log | tail -20 | while read line; do
  TIME=$(echo "$line" | grep -oP '^\[[^\]]+')
  AGENT=$(echo "$line" | grep -oP '\[WARN\] \[\K[^\]]+')
  MSG=$(echo "$line" | grep -oP '\] \K.*$' | tail -c +$(echo "$AGENT" | wc -c))
  echo "$TIME [$AGENT] $MSG"
done

if [ $(grep -c "\[WARN\]" .claude/agent-activity.log) -eq 0 ]; then
  echo "No warnings found ✓"
fi
echo ""
```

### --parallel: Parallel Execution Analysis

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "                   PARALLEL EXECUTION ANALYSIS                  "
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Peak parallelism: [analyzing...]"

# Group by parent to show parallel spawns
grep "\[SPAWN\]" .claude/agent-activity.log | tail -20 | while read line; do
  PARENT=$(echo "$line" | grep -oP '\[SPAWN\] \[\K[^\]]+')
  CHILD=$(echo "$line" | grep -oP 'child=\K.*$')
  echo "  $PARENT spawned → $CHILD"
done

echo ""
```

---

## Icons Reference

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

## Related Commands

- `/implement-feature` - Full workflow (generates telemetry)
- `/fix-bug-direct` - Bug fix workflow (generates telemetry)
- `/fix-bugs-jira` - Multi-bug workflow (generates telemetry)
- `/plan-council` - Multi-perspective planning (generates telemetry)
