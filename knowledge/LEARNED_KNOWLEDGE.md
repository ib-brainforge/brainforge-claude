# Learned Knowledge System

## Overview

Each `.md` knowledge file has a companion `.learned.yaml` file:
- **`.md` files** = Base knowledge (user-defined, manually updated)
- **`.learned.yaml` files** = Learned knowledge (significant changes auto-recorded)

## What Gets Recorded

**ONLY record significant architectural knowledge:**

| Record | Don't Record |
|--------|--------------|
| New feature added to system | Individual file patterns found |
| New service communication discovered | Grep match counts |
| Breaking change made | Minor code style observations |
| New shared contract/event created | File structure discoveries |
| Architectural decision made | Routine validations |
| New integration point | Existing pattern confirmations |

### Good Examples (Record These)
```yaml
- "Added lease_end_date property to Tenancy - affects asset-backend, asset-mf, common-backend"
- "New event TenancyLeaseExpiring added to common-backend for notification triggers"
- "asset-backend now calls notification-backend via event bus for lease reminders"
- "Breaking: TenancyDto changed - all consumers need update"
```

### Bad Examples (Don't Record)
```yaml
- "Found Tenancy entity in asset-backend"  # Obvious, not useful
- "TenancyForm uses React.FC"              # Too granular
- "Grep pattern matched 5 times"           # Noise
- "Convention followed correctly"          # Not a change
```

## YAML Schema

```yaml
# [topic].learned.yaml
version: 1
last_updated: "2024-01-27T10:30:00Z"
updated_by: "commit-manager"

# Significant feature additions
features:
  - id: "feat-20240127-001"
    date: "2024-01-27"
    description: "Added lease_end_date to tenancy feature"
    ticket: "FEAT-123"
    affected_services:
      - name: "asset-backend"
        changes: ["Tenancy entity", "TenancyDto", "migration"]
      - name: "asset-mf"
        changes: ["TenancyForm", "TenancyDetails", "types"]
      - name: "common-backend"
        changes: ["TenancyEvents"]
    breaking: false
    notes: "Optional field, nullable DateTime"
    # --- Observability metadata (auto-added by commit-manager) ---
    recorded_at: "2024-01-27T10:30:00Z"   # When this was recorded
    recorded_by: "commit-manager"          # Always commit-manager
    source_commits:                        # Git commits that triggered this
      - repo: "asset-backend"
        sha: "abc1234"
        message: "feat(tenancy): add lease_end_date"
      - repo: "asset-mf"
        sha: "def5678"
        message: "feat(tenancy): add lease end date picker"

# New service communications discovered
communications:
  - id: "comm-20240127-001"
    date: "2024-01-27"
    from: "asset-backend"
    to: "notification-backend"
    type: "event"
    event: "TenancyLeaseExpiring"
    purpose: "Trigger lease expiry notifications"
    discovered_in: "FEAT-123"

# New shared contracts/events
contracts:
  - id: "contract-20240127-001"
    date: "2024-01-27"
    name: "TenancyLeaseExpiring"
    location: "common-backend/src/Contracts/Events/"
    consumers: ["notification-backend", "asset-mf"]
    publisher: "asset-backend"
    added_in: "FEAT-123"

# Breaking changes log
breaking_changes:
  - id: "break-20240127-001"
    date: "2024-01-27"
    description: "TenancyDto added required LeaseEndDate field"
    affected_services: ["asset-mf", "onboard-mf"]
    migration_notes: "Update all TenancyDto consumers"
    ticket: "FEAT-123"

# Architectural decisions made during implementation
decisions:
  - id: "adr-20240127-001"
    date: "2024-01-27"
    context: "Needed to track lease expiration for tenancies"
    decision: "Add nullable LeaseEndDate to Tenancy entity"
    alternatives_considered:
      - "Separate LeaseTerms table - rejected (overkill for single field)"
      - "Store in metadata JSON - rejected (need query capability)"
    consequences: "Simple approach, can extend later if needed"
    ticket: "FEAT-123"

# Statistics (auto-updated)
stats:
  total_features: 1
  total_communications: 1
  total_contracts: 1
  total_breaking_changes: 1
  last_update: "2024-01-27T10:30:00Z"
```

## Recording Triggers

Record learned knowledge ONLY when:

1. **Feature Implementation Completes**
   - New property/field added to domain
   - New API endpoint created
   - New UI component added

2. **Service Communication Changes**
   - New service-to-service call
   - New event published/consumed
   - New API integration

3. **Shared Contract Changes**
   - New event type in common-backend
   - New shared DTO
   - Contract modification

4. **Breaking Changes**
   - DTO field changes
   - API signature changes
   - Event schema changes

5. **Architectural Decisions**
   - Why a specific approach was chosen
   - Trade-offs considered
   - Future implications

## How Agents Use This

### Reading (All Agents)
```
Read: knowledge/architecture/system-architecture.md        # Base
Read: knowledge/architecture/system-architecture.learned.yaml  # Recent changes

Check recent features to understand:
- What was recently added to affected services?
- Any recent breaking changes to consider?
- Recent communications added?
```

### Writing (ONLY commit-manager)

**Single Writer Pattern**: Only `commit-manager` writes to learned YAML files.
This prevents concurrent write conflicts when multiple agents run in parallel.

```
commit-manager (after commits complete)
    │
    └──► Task: spawn knowledge-updater
         Prompt: |
           $KNOWLEDGE_TYPE = system-architecture
           $LEARNING = {
             "type": "feature",
             "description": "[from commit messages]",
             "ticket": "FEAT-123",
             "affected_services": [...],
             "breaking": false
           }
```

**Why single writer?**
- Parallel validation agents can't conflict
- Learnings based on actual committed changes (not planned changes)
- Clear ownership and responsibility

## Human Override (Manual Editing)

YAML files can be edited directly by humans. This is useful for:
- Adding knowledge that wasn't captured automatically
- Correcting incorrect entries
- Promoting entries to base knowledge
- Removing obsolete entries

### Adding Entries Manually

```yaml
# Add to system-architecture.learned.yaml
features:
  - id: "feat-20240127-manual"      # Use "manual" suffix for human entries
    date: "2024-01-27"
    description: "Describe the feature clearly"
    ticket: "FEAT-123"              # Optional
    affected_services:
      - name: "service-name"
        changes: ["what changed"]
    breaking: false
    notes: "Added manually - [reason]"
    added_by: "human"               # Mark as human-added
```

### Editing Existing Entries

```yaml
# Before
features:
  - id: "feat-20240127-001"
    description: "Added X to service"

# After (add note about edit)
features:
  - id: "feat-20240127-001"
    description: "Added X to service (corrected: also affects service-b)"
    edited_at: "2024-02-15"
    edited_by: "human"
```

### Deleting Entries

Option 1: Remove the entry entirely
Option 2: Mark as deleted (preserves history):
```yaml
features:
  - id: "feat-20240127-001"
    deleted: true
    deleted_at: "2024-02-15"
    deleted_reason: "Feature was reverted"
```

### Validation After Manual Edit

```bash
# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('file.learned.yaml'))"

# Commit with clear message
git add file.learned.yaml
git commit -m "docs(knowledge): [add|edit|remove] [description]"
```

## Deduplication Rules

1. **Same ticket ID** → Update existing entry, don't duplicate
2. **Same feature description** → Merge into existing
3. **Same date + same services** → Likely same change, merge

## Cross-Branch Awareness

**Limitation:** Feature branches are isolated. Branch A doesn't see Branch B's learned knowledge.

**This is by design:**
- Git merge handles it naturally when branches merge to main
- Keeps branches independent (no unexpected changes)
- Conflict resolution is straightforward (keep both entries)

**Best practice:**
- Merge from main frequently to get latest learned knowledge
- Before major features, pull main to check recent changes

## Git Conflict Resolution

YAML files use unique IDs per entry, so conflicts are rare. If they occur:

### Typical Conflict
```yaml
features:
<<<<<<< HEAD
  - id: "feat-20240127-001"
    description: "Added X to service-a"
=======
  - id: "feat-20240127-002"
    description: "Added Y to service-b"
>>>>>>> feature-branch
```

### Resolution: Keep Both
```yaml
features:
  - id: "feat-20240127-001"
    description: "Added X to service-a"
  - id: "feat-20240127-002"
    description: "Added Y to service-b"
```

### Rules
1. **Different IDs** → Keep both entries (append)
2. **Same ID, different content** → Keep the more recent (by date field)
3. **Stats conflict** → Recalculate from entries count
4. **When in doubt** → Keep both, deduplicate later

### After Resolving
```bash
# Verify YAML is valid
python -c "import yaml; yaml.safe_load(open('file.learned.yaml'))"

# Commit resolution
git add file.learned.yaml
git commit -m "chore: resolve learned knowledge merge conflict"
```

## Maintenance & Pruning

### Auto-Archive (6 months)

Entries older than 6 months should be moved to `*.archived.yaml`:

```
knowledge/architecture/
├── system-architecture.learned.yaml      # Active (< 6 months)
├── system-architecture.archived.yaml     # Archived (> 6 months)
```

**Archive process (run monthly):**
```bash
# Check for old entries
grep -l "date: \"$(date -d '6 months ago' +%Y)" knowledge/**/*.learned.yaml
```

### Promote to Base Knowledge

Valuable learnings should be promoted to base MD files:

**Candidates for promotion:**
- Patterns used in 3+ features
- Decisions referenced multiple times
- Communications that became standard

**Promotion workflow:**
1. Identify valuable entry in `.learned.yaml`
2. Add to appropriate `.md` file (rewrite in documentation style)
3. Remove from `.learned.yaml`
4. Commit: `docs: promote [topic] to base knowledge`

### Cleanup Criteria

**Archive if:**
- Entry older than 6 months
- Feature was later refactored/removed
- Communication no longer exists

**Delete if:**
- Duplicate of another entry
- Superseded by newer entry (same ticket)
- Incorrect/invalid entry

**Promote if:**
- Referenced by 3+ subsequent features
- Became a standard pattern
- Important architectural decision

### Archive File Format

```yaml
# system-architecture.archived.yaml
version: 1
archived_at: "2024-07-01"

features:
  - id: "feat-20240127-001"
    date: "2024-01-27"
    archived_reason: "older than 6 months"
    # ... original entry fields
```
