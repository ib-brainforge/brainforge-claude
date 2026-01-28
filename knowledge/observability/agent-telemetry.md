# Agent Telemetry System

## Overview

Telemetry is collected **automatically via Claude Code hooks** - agents don't need to manually log anything.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTOMATIC TELEMETRY VIA HOOKS                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Claude Code Hooks (.claude/settings.json)                          │
│     │                                                                │
│     ├── PreToolUse (Task tool)  →  Log [START] when agent spawned   │
│     │                                                                │
│     ├── PostToolUse (Task tool) →  Log [COMPLETE] when agent done   │
│     │                                                                │
│     ├── SubagentStop            →  Log subagent completion          │
│     │                                                                │
│     └── Stop                    →  Log session end                  │
│                                                                      │
│  All logs written to: .claude/agent-activity.log                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Configuration

**Location:** `.claude/` folder in your repository root.

### Hooks Settings (`.claude/settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [{ "type": "command", "command": "CLAUDE_HOOK_EVENT=PreToolUse .claude/hooks/telemetry.sh" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [{ "type": "command", "command": "CLAUDE_HOOK_EVENT=PostToolUse .claude/hooks/telemetry.sh" }]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "CLAUDE_HOOK_EVENT=SubagentStop .claude/hooks/telemetry.sh" }]
      }
    ]
  }
}
```

### Telemetry Script (`.claude/hooks/telemetry.sh`)

The script automatically:
- Parses JSON payload from Claude Code
- Extracts agent name from Task tool input
- Logs start/complete events with timestamps
- Tracks tool_use_id for correlation

## What Gets Tracked

| Event | When | Data |
|-------|------|------|
| `[START]` | Agent spawned (PreToolUse on Task) | Agent name, ID, timestamp |
| `[COMPLETE]` | Agent finished (PostToolUse on Task) | Agent name, status, timestamp |
| `[SUBAGENT_COMPLETE]` | Subagent done | Subagent name, tool_use_id |
| `[SESSION_END]` | Session finished | Session ID |

## Log Format

Location: `.claude/agent-activity.log`

```
[2026-01-28T10:30:00+00:00] [START] [feature-implementor] id=agent-1234567890123 tool_use_id=xyz event=PreToolUse
[2026-01-28T10:30:05+00:00] [START] [backend-implementor] id=agent-1234567890456 tool_use_id=abc event=PreToolUse
[2026-01-28T10:30:05+00:00] [START] [frontend-implementor] id=agent-1234567890789 tool_use_id=def event=PreToolUse
[2026-01-28T10:31:20+00:00] [COMPLETE] [backend-implementor] tool_use_id=abc status=complete event=PostToolUse
[2026-01-28T10:31:25+00:00] [COMPLETE] [frontend-implementor] tool_use_id=def status=complete event=PostToolUse
[2026-01-28T10:32:00+00:00] [COMPLETE] [feature-implementor] tool_use_id=xyz status=complete event=PostToolUse
```

## Viewing Telemetry

### Commands

| Need | Command |
|------|---------|
| Full execution tree | `/agent-trace` |
| Overall stats | `/agent-stats` |
| Did validators run? | `grep validator .claude/agent-activity.log` |
| Were PRs created? | `grep git-workflow-manager .claude/agent-activity.log` |
| Recent activity | `tail -20 .claude/agent-activity.log` |

### Quick Queries

```bash
# Show all agent starts
grep "\[START\]" .claude/agent-activity.log

# Show all completions
grep "\[COMPLETE\]" .claude/agent-activity.log

# Show validation runs
grep -E "validator" .claude/agent-activity.log

# Show git workflow
grep "git-workflow-manager" .claude/agent-activity.log

# Count agents spawned
grep -c "\[START\]" .claude/agent-activity.log
```

## Benefits of Hook-Based Telemetry

1. **Agents stay focused** - No telemetry code in agent files
2. **Consistent logging** - All agents logged the same way
3. **Can't be skipped** - Hooks run automatically
4. **Easy to extend** - Add more hooks without changing agents
5. **Centralized config** - One place to manage telemetry

## Extending Telemetry

To add more tracking:

1. **Add new hook event** in `.claude/settings.json`
2. **Update telemetry.sh** to handle new event type
3. **No agent changes needed**

Example - track all Edit operations:
```json
{
  "PostToolUse": [
    {
      "matcher": "Edit",
      "hooks": [{ "type": "command", "command": "CLAUDE_HOOK_EVENT=PostToolUse .claude/hooks/telemetry.sh" }]
    }
  ]
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No logs appearing | Check `.claude/hooks/telemetry.sh` is executable |
| Hook not running | Verify `.claude/settings.json` syntax |
| Missing jq errors | Script falls back to grep/sed parsing |
| Permission denied | Run `chmod +x .claude/hooks/telemetry.sh` |
