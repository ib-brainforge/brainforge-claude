---
name: jira-integration
description: |
  Jira ticket integration for fetching tickets, parsing bug lists,
  and updating ticket status after work is complete.
triggers:
  - /jira
  - /ticket
  - jira ticket
  - fetch ticket
  - from jira
---

# Purpose

Integrate with Jira to fetch ticket details, parse bug lists from descriptions,
and update tickets after work is complete. All Jira configuration loaded from
knowledge files.

# Usage

```bash
/jira PROJ-123                       # Fetch and display ticket
/jira PROJ-123 --parse-bugs          # Parse bugs from description
/jira PROJ-123 --update "Fixed"      # Update ticket status
/jira PROJ-123 --comment "Done"      # Add comment to ticket
/jira PROJ-123 --link abc123         # Link commit to ticket
```

# Variables

- `$TICKET_ID (string)`: Jira ticket ID (e.g., PROJ-123)
- `$ACTION (string)`: fetch|parse-bugs|update|comment|link (default: fetch)
- `$STATUS (string, optional)`: New status for update action
- `$COMMENT (string, optional)`: Comment text to add
- `$COMMIT_SHA (string, optional)`: Commit SHA to link

# Knowledge References

Load Jira configuration from:

```
knowledge/jira/jira-config.md         → Jira URL, project keys, workflows
```

**Note**: This skill does NOT record learnings. Only `commit-manager` writes to learned YAML files.

# Configuration

## Environment Variables (in .env file)

Create a `.env` file in your **project root** (same level as `.claude` folder):
```
your-repos-root/
├── .env              ← Create this file here
├── .claude/
├── knowledge/
└── CLAUDE.md
```

Contents:
```bash
# .env (add to .gitignore!)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER=your-email@domain.com
JIRA_API_TOKEN=your-api-token
```

## Loading Environment Variables

**IMPORTANT**: Before any Jira API call, load the .env file:
```bash
# Load .env and make variables available
set -a && source .env && set +a
```

Or inline with the curl command:
```bash
(set -a && source .env && set +a && curl -s -u "$JIRA_USER:$JIRA_API_TOKEN" "$JIRA_URL/rest/api/3/issue/$TICKET_ID")
```

# Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       JIRA INTEGRATION WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ACTION: fetch                                                               │
│  ─────────────                                                               │
│  1. Load knowledge for Jira config                                           │
│  2. Call Jira REST API to get ticket                                         │
│  3. Return formatted ticket details                                          │
│                                                                              │
│  ACTION: parse-bugs                                                          │
│  ──────────────────                                                          │
│  1. Fetch ticket (as above)                                                  │
│  2. Parse description for bug patterns                                       │
│  3. Return structured bug list                                               │
│                                                                              │
│  ACTION: update                                                              │
│  ──────────────                                                              │
│  1. Transition ticket to new status                                          │
│  2. Return confirmation                                                      │
│                                                                              │
│  ACTION: comment                                                             │
│  ───────────────                                                             │
│  1. Add comment to ticket                                                    │
│  2. Return confirmation                                                      │
│                                                                              │
│  ACTION: link                                                                │
│  ────────────                                                                │
│  1. Add commit link as remote link or comment                                │
│  2. Return confirmation                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Instructions

## 1. Load Knowledge
```
Read: knowledge/jira/jira-config.md
```

Get:
- Jira base URL
- Project keys and their workflows
- Status transition mappings
- Bug parsing patterns

## 2. Action: Fetch Ticket

**IMPORTANT**: Always load .env before API calls:
```
Bash: set -a && source .env && set +a && curl -s -u "$JIRA_USER:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_URL/rest/api/3/issue/$TICKET_ID"
```

Parse response for:
- Summary (title)
- Description
- Status
- Assignee
- Labels
- Components
- Linked issues

### Format Output
```
Ticket: $TICKET_ID
Summary: [title]
Status: [status]
Type: [Bug/Story/Task]
Assignee: [name]

Description:
[description text]

Acceptance Criteria:
[if present]
```

## 3. Action: Parse Bugs

After fetching ticket, parse description for bug patterns.

### Common Bug List Patterns

**Numbered list:**
```
1. Bug description one
2. Bug description two
```

**Bullet list:**
```
- Bug description one
- Bug description two
```

**Checkbox list:**
```
[ ] Bug description one
[x] Bug description two (already fixed)
```

**Table format:**
```
| Bug | Severity | Component |
|-----|----------|-----------|
| Description | High | Auth |
```

### Parse Logic

Extract each bug as structured item:
```json
{
  "bugs": [
    {
      "id": 1,
      "description": "Bug description",
      "severity": "high|medium|low",
      "component": "component-name",
      "status": "open|fixed"
    }
  ]
}
```

## 4. Action: Update Status

### Get Available Transitions
```
Bash: curl -s -u "$JIRA_USER:$JIRA_API_TOKEN" \
  "$JIRA_URL/rest/api/3/issue/$TICKET_ID/transitions"
```

### Find Transition ID
Match $STATUS to available transitions (from knowledge or API response).

### Execute Transition
```
Bash: curl -s -X POST -u "$JIRA_USER:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_URL/rest/api/3/issue/$TICKET_ID/transitions" \
  -d '{"transition":{"id":"[transition-id]"}}'
```

## 5. Action: Add Comment

### Standard Comment
```
Bash: curl -s -X POST -u "$JIRA_USER:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_URL/rest/api/3/issue/$TICKET_ID/comment" \
  -d '{"body":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"$COMMENT"}]}]}}'
```

### Bug Fix Completion Comment (Required Format)

When bugs are fixed, post a **business-focused** table comment. Keep it simple and non-technical.

**Format:**
```
| Issue | Resolution |
|-------|------------|
| [Business description of problem] | [Business description of fix] |
```

**Example - CORRECT (Business Focus):**
```
| Issue | Resolution |
|-------|------------|
| Users couldn't log in with special characters in password | Login now accepts all valid password characters |
| Session was expiring too quickly | Session timeout extended to expected duration |
| Error messages were confusing | Clear guidance now shown when login fails |
```

**Example - WRONG (Too Technical):**
```
| Issue | Resolution |
|-------|------------|
| Password not URL-encoded in auth.cs line 45 | Added Uri.EscapeDataString() call |
```

**Jira Table Syntax (ADF format):**
```bash
COMMENT=$(cat <<'EOF'
| Issue | Resolution |
|-------|------------|
| [issue 1] | [resolution 1] |
| [issue 2] | [resolution 2] |
EOF
)

curl -s -X POST -u "$JIRA_USER:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_URL/rest/api/3/issue/$TICKET_ID/comment" \
  -d "{\"body\":{\"type\":\"doc\",\"version\":1,\"content\":[{\"type\":\"table\",\"attrs\":{\"isNumberColumnEnabled\":false,\"layout\":\"default\"},\"content\":[{\"type\":\"tableRow\",\"content\":[{\"type\":\"tableHeader\",\"content\":[{\"type\":\"paragraph\",\"content\":[{\"type\":\"text\",\"text\":\"Issue\"}]}]},{\"type\":\"tableHeader\",\"content\":[{\"type\":\"paragraph\",\"content\":[{\"type\":\"text\",\"text\":\"Resolution\"}]}]}]}$(echo "$ROWS")]}]}}"
```

**Key Rules:**
- NO code references (no file names, line numbers, function names)
- NO technical jargon (no "URL encoding", "null check", "API endpoint")
- Write as if explaining to a business stakeholder
- Focus on what the user experiences, not what the code does

## 6. Action: Link Commit

Add commit as remote link:
```
Bash: curl -s -X POST -u "$JIRA_USER:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_URL/rest/api/3/issue/$TICKET_ID/remotelink" \
  -d '{
    "object": {
      "url": "[repo-url]/commit/$COMMIT_SHA",
      "title": "Commit: $COMMIT_SHA",
      "icon": {"url16x16": "https://github.com/favicon.ico"}
    }
  }'
```

Or add as comment:
```
Bash: [add comment with commit link]
```

# Report Format

## Fetch Result
```json
{
  "skill": "jira-integration",
  "action": "fetch",
  "status": "PASS",
  "ticket": {
    "id": "PROJ-123",
    "summary": "Fix authentication bugs",
    "status": "In Progress",
    "type": "Bug",
    "assignee": "John Doe",
    "description": "...",
    "labels": ["backend", "auth"],
    "components": ["auth-service"]
  }
}
```

## Parse Bugs Result
```json
{
  "skill": "jira-integration",
  "action": "parse-bugs",
  "status": "PASS",
  "ticket_id": "PROJ-123",
  "bugs": [
    {
      "id": 1,
      "description": "Login fails with special characters in password",
      "severity": "high",
      "component": "auth-service"
    },
    {
      "id": 2,
      "description": "Session timeout not working correctly",
      "severity": "medium",
      "component": "auth-service"
    }
  ],
  "total_bugs": 2
}
```

## Update Result
```json
{
  "skill": "jira-integration",
  "action": "update",
  "status": "PASS",
  "ticket_id": "PROJ-123",
  "old_status": "In Progress",
  "new_status": "Done"
}
```

# Error Handling

| Error | Action |
|-------|--------|
| 401 Unauthorized | Check JIRA_API_TOKEN |
| 404 Not Found | Invalid ticket ID |
| 400 Bad Request | Invalid transition or payload |
| No bugs found | Return empty list, warn user |

# Note on Learnings

**This skill does NOT record learnings.**

Jira interactions are operational tasks. Only `commit-manager` records
learnings after code changes are committed.

# Related Skills

- `commit-manager` - Commits with Jira ticket linking
- `feature-planning` - Plan implementation from ticket

# Related Agents

- `bug-triage` - Processes parsed bugs into actionable tasks
- `bug-fixer` - Applies fixes based on bug descriptions
