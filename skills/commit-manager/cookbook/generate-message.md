# Recipe: Generate Commit Message

## Purpose

Generate conventional commit messages using local LLM with Claude fallback.

## LLM Selection Flow

```
1. Check $USE_LOCAL_LLM setting
   ├── "force" → Always use local, fail if unavailable
   ├── "never" → Always use Claude
   └── "auto" (default) → Try local, fallback to Claude

2. If local enabled:
   └──► Spawn local-llm-worker or lmstudio-llm-worker
        └──► Ping first
             ├── Available → Generate message
             └── Unavailable → Fallback to Claude

3. Validate generated message regardless of source
```

## Local LLM Worker

```
Task: spawn local-llm-worker
Prompt: |
  Generate commit message:
  Repo: $REPO_NAME
  Type: $COMMIT_TYPE
  Diff Summary: $DIFF_SUMMARY
  Files Changed: $FILES

  Follow conventional commits format from knowledge/commit-conventions.md
```

## Response Handling

- If `status: UNAVAILABLE` → Use Claude API
- If `status: FAIL` → Use Claude API
- If `status: PASS` → Use generated message

## Message Validation

All messages must pass:
- Conventional commit format: `type(scope): description`
- First line ≤ 72 characters
- Body wrapped at 80 characters
- References issues if applicable

## Knowledge Dependencies

- `knowledge/commit-conventions.md` - Message format rules
