#!/bin/bash
# Agent Telemetry Hook Script
# Automatically logs agent activity without requiring manual telemetry in agent files
#
# Called by Claude Code hooks with:
#   $CLAUDE_HOOK_EVENT - The event type (PreToolUse, PostToolUse, SubagentStop)
#   stdin - JSON payload with event details

set -e

# Configuration
LOG_DIR="${REPOS_ROOT:-.}/.claude"
LOG_FILE="$LOG_DIR/agent-activity.log"
TELEMETRY_DIR="$LOG_DIR/telemetry"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$TELEMETRY_DIR"

# Read JSON payload from stdin
PAYLOAD=$(cat)

# Get timestamp
TIMESTAMP=$(date -Iseconds)

# Parse event type from environment or payload
EVENT_TYPE="${CLAUDE_HOOK_EVENT:-unknown}"

# Extract common fields from payload using jq (if available) or grep/sed
if command -v jq &> /dev/null; then
    TOOL_NAME=$(echo "$PAYLOAD" | jq -r '.tool_name // .toolName // "unknown"' 2>/dev/null || echo "unknown")
    TOOL_INPUT=$(echo "$PAYLOAD" | jq -r '.tool_input // .input // "{}"' 2>/dev/null || echo "{}")
    SESSION_ID=$(echo "$PAYLOAD" | jq -r '.session_id // .sessionId // "unknown"' 2>/dev/null || echo "unknown")
    TOOL_USE_ID=$(echo "$PAYLOAD" | jq -r '.tool_use_id // .toolUseId // ""' 2>/dev/null || echo "")
else
    # Fallback without jq
    TOOL_NAME=$(echo "$PAYLOAD" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/' || echo "unknown")
    SESSION_ID="unknown"
    TOOL_USE_ID=""
fi

# Handle different event types
case "$EVENT_TYPE" in
    "PreToolUse")
        # Log when a tool is about to be used
        if [ "$TOOL_NAME" = "Task" ]; then
            # Extract agent name from Task tool input
            AGENT_NAME=$(echo "$TOOL_INPUT" | grep -o 'spawn[[:space:]]*[a-zA-Z-]*' | head -1 | sed 's/spawn *//' || echo "unknown-agent")
            AGENT_ID="agent-$(date +%s%N | cut -c1-13)"
            echo "[$TIMESTAMP] [START] [$AGENT_NAME] id=$AGENT_ID tool_use_id=$TOOL_USE_ID event=PreToolUse" >> "$LOG_FILE"
        else
            # Log other tool uses for debugging (optional - can be disabled)
            : # echo "[$TIMESTAMP] [TOOL] [$TOOL_NAME] tool_use_id=$TOOL_USE_ID" >> "$LOG_FILE"
        fi
        ;;

    "PostToolUse")
        # Log when a tool completes
        if [ "$TOOL_NAME" = "Task" ]; then
            AGENT_NAME=$(echo "$TOOL_INPUT" | grep -o 'spawn[[:space:]]*[a-zA-Z-]*' | head -1 | sed 's/spawn *//' || echo "unknown-agent")
            # Extract status from result if available
            STATUS=$(echo "$PAYLOAD" | jq -r '.result.status // "complete"' 2>/dev/null || echo "complete")
            echo "[$TIMESTAMP] [COMPLETE] [$AGENT_NAME] tool_use_id=$TOOL_USE_ID status=$STATUS event=PostToolUse" >> "$LOG_FILE"
        fi
        ;;

    "SubagentStop")
        # Log when a subagent finishes
        SUBAGENT_NAME=$(echo "$PAYLOAD" | jq -r '.subagent_name // .name // "subagent"' 2>/dev/null || echo "subagent")
        echo "[$TIMESTAMP] [SUBAGENT_COMPLETE] [$SUBAGENT_NAME] tool_use_id=$TOOL_USE_ID event=SubagentStop" >> "$LOG_FILE"
        ;;

    "Stop")
        # Log session end
        echo "[$TIMESTAMP] [SESSION_END] session=$SESSION_ID" >> "$LOG_FILE"
        ;;

    *)
        # Unknown event type - log for debugging
        echo "[$TIMESTAMP] [EVENT] type=$EVENT_TYPE tool=$TOOL_NAME" >> "$LOG_FILE"
        ;;
esac

# Exit successfully (don't block the tool execution)
exit 0
