# /write-docs Command

Create technical or business documentation on Confluence.

## Usage

```
/write-docs "topic" [--type technical|business] [--space SPACE_KEY]
```

## Aliases / Trigger Phrases

- "write documentation for..."
- "create confluence page for..."
- "document the ... service"
- "create technical docs for..."
- "write business documentation for..."

## Examples

```
/write-docs "Asset Service" --type technical --space ENG
/write-docs "Onboarding Process" --type business --space HR
/write-docs "API Gateway Architecture"
```

Or naturally:
```
User: "Write technical documentation for the auth-service"
User: "Create a confluence page documenting our deployment process"
User: "Document the tenant management feature for the business team"
```

## What It Does

1. **Explores codebase** to understand the topic
2. **Writes documentation locally** in `docs/confluence/`
3. **Pushes to Confluence** via Atlassian MCP server
4. **Creates child pages** if needed (examples, API reference)

## Workflow

```
/write-docs "Asset Service" --type technical
    │
    ▼
[main] Spawn confluence-writer
    │
    ├──► Explore: asset-backend/, asset-mf/
    │    ├── Controllers, Services, Entities
    │    ├── Components, Hooks, Types
    │    └── README, existing docs
    │
    ├──► Write locally:
    │    └── docs/confluence/ENG/asset-service-technical/
    │        ├── content.md
    │        └── _meta.json
    │
    ├──► Push to Confluence via MCP
    │
    └──► Create child pages (if extensive)
```

## Documentation Types

### Technical (`--type technical`)
- Overview & Architecture
- Components breakdown
- Data Model
- API Reference
- Configuration
- Dependencies
- Security
- Troubleshooting

### Business (`--type business`)
- Executive Summary
- Business Context
- User Stories
- Process Flow
- Roles & Responsibilities
- Business Rules
- Metrics & KPIs
- FAQ

## Local Mirror

All docs are mirrored locally before pushing:

```
docs/confluence/
├── _index.json
└── ENG/
    └── asset-service-technical/
        ├── _meta.json       # Page ID, URL, version
        └── content.md       # Actual content
```

Benefits:
- Track changes in git
- Work offline
- Review before publishing
- Sync bidirectionally

## Prerequisites

**Atlassian MCP Server** must be configured in `.mcp.json`:
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.atlassian.com/v1/sse"]
    }
  }
}
```

## Notes

- Uses **Opus** model for high-quality writing
- Evidence-based - explores actual code
- Creates child pages for extensive topics
- Maintains local mirror for version control
