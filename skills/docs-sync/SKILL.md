---
name: docs-sync
description: |
  Documentation synchronization between code repositories and Confluence.
  Trigger: documentation updates, ADR changes, architecture docs sync,
  keeping Confluence in sync with code-level documentation.
triggers:
  - /sync-docs
  - sync documentation
  - update confluence
---

# Purpose

Synchronizes architecture documentation between code repositories and Confluence,
ensuring single source of truth with bi-directional awareness.

# Usage

```bash
/sync-docs                           # Sync all docs
/sync-docs --type adr                # Only ADRs
/sync-docs --type service-docs       # Only service docs
/sync-docs --dry-run                 # Preview changes
/sync-docs --direction pull          # Pull from Confluence
```

# Variables

- `$REPOS_ROOT (path)`: Root directory containing repositories
- `$DOC_TYPE (string)`: adr|service-docs|runbooks|all (default: all)
- `$DRY_RUN (bool)`: Preview only (default: true)
- `$DIRECTION (string)`: push|pull (default: push)
- `$CONFLUENCE_SPACE (string)`: Confluence space key

# Knowledge References

```
knowledge/architecture/system-architecture.md    → ADR templates, system structure
```

**Note**: This skill does NOT record learnings. Only `commit-manager` writes to learned YAML files.

# Configuration

Set your Confluence details in environment or config:
```yaml
confluence:
  base_url: "https://your-domain.atlassian.net/wiki"
  space_key: "ARCH"  # Your architecture space
  # API token via environment: CONFLUENCE_API_TOKEN

doc_sources:
  - type: adr
    repo_pattern: "**/docs/adr/*.md"
    confluence_parent: "Architecture Decision Records"
  - type: service-docs
    repo_pattern: "**/ARCHITECTURE.md"
    confluence_parent: "Service Architecture"
  - type: runbooks
    repo_pattern: "**/docs/runbooks/*.md"
    confluence_parent: "Runbooks"
```

# Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOCS-SYNC WORKFLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. LOAD KNOWLEDGE                                                           │
│     └──► Read system-architecture.md for ADR templates                       │
│                                                                              │
│  2. DISCOVER DOCS                                                            │
│     └──► Glob for doc files in repos                                         │
│                                                                              │
│  3. COMPARE (Push Direction)                                                 │
│     └──► Compare local docs vs Confluence                                    │
│          - Identify new, changed, deleted                                    │
│                                                                              │
│  4. SYNC                                                                     │
│     └──► Push: Create/update Confluence pages                                │
│     └──► Pull: Download Confluence pages to local                            │
│                                                                              │
│  5. REPORT                                                                   │
│     └──► Summary of changes made                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Instructions

## 1. Load Knowledge
```
Read: knowledge/architecture/system-architecture.md
```

## 2. Discover Documentation Files

Find docs based on type:

### ADRs
```
Glob: $REPOS_ROOT/**/docs/adr/*.md
```

### Service Docs
```
Glob: $REPOS_ROOT/**/ARCHITECTURE.md
Glob: $REPOS_ROOT/**/README.md
```

### Runbooks
```
Glob: $REPOS_ROOT/**/docs/runbooks/*.md
```

## 3. Read and Parse Documents

For each discovered doc:
```
Read: [doc-path]
```

Extract metadata:
- Title (from H1 or frontmatter)
- Last modified date
- Service/component name
- Doc type

## 4. Compare with Confluence (Push Direction)

### Get Confluence Pages
```
Bash: curl -s -u "$CONFLUENCE_USER:$CONFLUENCE_TOKEN" \
  "$CONFLUENCE_URL/rest/api/content?spaceKey=$SPACE&limit=500" \
  | jq '.results[] | {title, id, version: .version.number}'
```

Or use Confluence API via Task:
```
Task: spawn confluence-api-agent
Prompt: |
  List all pages in space: $CONFLUENCE_SPACE
  Under parent: [parent page for doc type]
  Return: page titles, IDs, and versions
```

### Compare
For each local doc:
- New: Local exists, Confluence doesn't
- Changed: Both exist, local modified after Confluence
- Deleted: Confluence exists, local doesn't
- Unchanged: Content matches

## 5. Sync Documents

### Push to Confluence

For new pages:
```
Bash: curl -X POST "$CONFLUENCE_URL/rest/api/content" \
  -H "Content-Type: application/json" \
  -u "$CONFLUENCE_USER:$CONFLUENCE_TOKEN" \
  -d '{"type":"page","title":"[title]","space":{"key":"[space]"},"body":{"storage":{"value":"[html-content]","representation":"storage"}}}'
```

For updates:
```
Bash: curl -X PUT "$CONFLUENCE_URL/rest/api/content/[page-id]" \
  -H "Content-Type: application/json" \
  -u "$CONFLUENCE_USER:$CONFLUENCE_TOKEN" \
  -d '{"version":{"number":[new-version]},"title":"[title]","type":"page","body":{"storage":{"value":"[html-content]","representation":"storage"}}}'
```

### Convert Markdown to Confluence Format

Before pushing, convert Markdown to Confluence storage format:
- Headers: `# Title` → `<h1>Title</h1>`
- Code blocks: Use `<ac:structured-macro>` for code
- Links: Convert to Confluence link format
- Images: Upload as attachments

### Pull from Confluence

For Confluence-primary docs:
```
Bash: curl -s -u "$CONFLUENCE_USER:$CONFLUENCE_TOKEN" \
  "$CONFLUENCE_URL/rest/api/content/[page-id]?expand=body.storage" \
  | jq -r '.body.storage.value'
```

Convert to Markdown and save:
```
Write: $REPOS_ROOT/[service]/docs/[doc-name].md
```

## 6. Dry Run Mode

If $DRY_RUN:
- List all changes that would be made
- Show diff for changed documents
- Don't actually sync

# Report Format

```json
{
  "skill": "docs-sync",
  "status": "PASS|WARN|FAIL",
  "direction": "push|pull",
  "summary": {
    "total_docs": 25,
    "created": 3,
    "updated": 5,
    "unchanged": 17,
    "conflicts": 0,
    "errors": 0
  },
  "changes": [
    {
      "doc": "docs/adr/001-use-microservices.md",
      "action": "created",
      "confluence_page": "ADR-001: Use Microservices",
      "confluence_id": "12345"
    },
    {
      "doc": "user-service/ARCHITECTURE.md",
      "action": "updated",
      "confluence_page": "User Service Architecture",
      "changes": "Added authentication section"
    }
  ],
  "conflicts": [],
  "errors": []
}
```

# Conflict Resolution

When local and Confluence both changed:
1. Report as conflict
2. Show diff between versions
3. User must manually resolve
4. Options: --prefer-local or --prefer-confluence

# Note on Learnings

**This skill does NOT record learnings.**

Documentation sync is an operational task, not an architectural change.
Only `commit-manager` records learnings after code changes are committed.

# Related Skills

- `validation` - Validate service documentation exists
- `commit-manager` - Commit doc updates to repos
