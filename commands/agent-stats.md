---
name: /agent-stats
description: Show agent telemetry and observability dashboard
allowed_tools: [Read, Bash]
---

# Purpose

Display agent execution statistics, call hierarchy, context usage, and warnings.
Helps you understand how work was distributed and identify agents that need optimization.

## Usage

```
/agent-stats                    # Show last session summary
/agent-stats --tree             # Show call hierarchy tree
/agent-stats --context          # Show context usage breakdown
/agent-stats --warnings         # Show only warnings
/agent-stats --last N           # Show last N sessions
/agent-stats --session ID       # Show specific session
```

## Commands to Execute

### Default: Last Session Summary

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

### --tree: Call Hierarchy

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "                      AGENT CALL TREE                           "
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Parse activity log to build tree
grep -E "\[START\]|\[SPAWN\]|\[COMPLETE\]" .claude/agent-activity.log | tail -50 | while read line; do
  if echo "$line" | grep -q "\[START\]"; then
    AGENT=$(echo "$line" | grep -oP '\[\K[^\]]+(?=\] id=)')
    DEPTH=$(echo "$line" | grep -oP 'depth=\K[0-9]+')
    INDENT=$(printf '%*s' $((DEPTH * 2)) '')
    echo "${INDENT}├── $AGENT"
  fi
done

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

### --parallel: Show Parallel Execution

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "                   PARALLEL EXECUTION ANALYSIS                  "
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Find max concurrent agents by analyzing timestamps
echo "Peak parallelism: [analyzing...]"

# Group by parent to show parallel spawns
grep "\[SPAWN\]" .claude/agent-activity.log | tail -20 | while read line; do
  PARENT=$(echo "$line" | grep -oP '\[SPAWN\] \[\K[^\]]+')
  CHILD=$(echo "$line" | grep -oP 'child=\K.*$')
  echo "  $PARENT spawned → $CHILD"
done

echo ""
```

## Visual Dashboard Output

When run, displays:

```
═══════════════════════════════════════════════════════════════
                    AGENT EXECUTION SUMMARY
═══════════════════════════════════════════════════════════════

Last Command: /plan-council "Add inline-edit"
Session: 2026-01-27T10:30:00Z
Duration: 2m 30s

┌─────────────────────────────────────────────────────────────┐
│ AGENTS SPAWNED: 7        TOTAL TOKENS: 95,200               │
│ MAX PARALLEL: 5          WARNINGS: 1                        │
└─────────────────────────────────────────────────────────────┘

CALL TREE:
├── planning-council (11,700 tokens, 150s)
│   ├── plan-analyst:Pragmatic (14,500 tokens, 70s)
│   ├── plan-analyst:Architectural (15,200 tokens, 90s) ⚠️
│   ├── plan-analyst:Risk-Aware (13,800 tokens, 80s)
│   ├── plan-analyst:User-Centric (14,100 tokens, 85s)
│   └── plan-analyst:Performance (13,500 tokens, 75s)
└── feature-implementor (12,400 tokens, 60s)

CONTEXT BREAKDOWN:
┌────────────────────────────┬──────────┬────────┐
│ Agent                      │ Tokens   │ Status │
├────────────────────────────┼──────────┼────────┤
│ planning-council           │   11,700 │ PASS   │
│ plan-analyst:Pragmatic     │   14,500 │ PASS   │
│ plan-analyst:Architectural │   15,200 │ PASS   │ ⚠️
│ plan-analyst:Risk-Aware    │   13,800 │ PASS   │
│ plan-analyst:User-Centric  │   14,100 │ PASS   │
│ plan-analyst:Performance   │   13,500 │ PASS   │
│ feature-implementor        │   12,400 │ PASS   │
├────────────────────────────┼──────────┼────────┤
│ TOTAL                      │   95,200 │        │
└────────────────────────────┴──────────┴────────┘

WARNINGS:
⚠️  [plan-analyst:Architectural] HIGH_CONTEXT tokens=15200 threshold=15000
    Recommendation: Consider splitting architectural analysis into
    sub-categories (patterns, scalability, maintainability)

RECOMMENDATIONS:
• plan-analyst:Architectural is approaching context limit
  → Consider adding more focused sub-analysts
• 5 agents ran in parallel efficiently
  → Current PLANNING_AGENTS_COUNT=5 is appropriate
```

## Related Commands

- `/validate` - Run validation
- `/plan-council` - Multi-perspective planning (generates telemetry)
