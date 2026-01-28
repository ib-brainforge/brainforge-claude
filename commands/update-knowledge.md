# /update-knowledge Command

Investigate and correct misconceptions in knowledge files.

## Usage

```
/update-knowledge "description of what's wrong"
```

## Aliases / Trigger Phrases

This command can also be invoked by saying:
- "the knowledge is wrong about..."
- "that's not how we do it, we actually..."
- "correct the knowledge..."
- "fix the knowledge about..."
- "update knowledge about..."
- "the docs say X but we use Y"

## Examples

```
/update-knowledge "we use AuditableEntity not BaseEntity"
/update-knowledge "auth-service communicates via events not HTTP"
/update-knowledge "we're on .NET 8 not .NET 6"
/update-knowledge "the API patterns use MediatR not direct service calls"
```

Or naturally:
```
User: "That's wrong, we don't use IRepository, we use IGenericRepository"
→ Triggers knowledge investigation

User: "The knowledge says we use Redux but we actually use Zustand"
→ Triggers knowledge investigation
```

## What It Does

1. **Investigates** the actual codebase to find the truth
2. **Compares** findings against current knowledge files
3. **Updates** knowledge MD files with accurate information
4. **Documents** what was wrong and what was corrected
5. **Logs** corrections to `.claude/knowledge-corrections.log`

## Workflow

```
User identifies misconception
    │
    ▼
[main] Spawn knowledge-investigator
    │
    ├──► Parse the misconception
    ├──► Load relevant knowledge files
    ├──► Grep/Glob/Read actual codebase
    ├──► Compare knowledge vs reality
    ├──► Edit knowledge files if wrong
    └──► Report corrections made
```

## Output

The agent reports:
- What the knowledge said
- What was actually found in codebase
- Evidence (file paths, counts)
- Corrections made (if any)

## Notes

- Only updates BASE knowledge (*.md files), not learned (*.yaml)
- Evidence-based corrections only
- Adds comments about when/why corrected
- Logs all corrections for audit trail
