# /git-sync

Sync current feature branch with latest develop to prevent merge conflicts.

## Usage

```
/git-sync
```

## What It Does

1. Fetches latest `origin/develop`
2. Merges develop into your current feature branch
3. Reports any conflicts (you'll need to resolve manually)

## When to Use

- Before finishing a long-running feature
- When you know develop has changed significantly
- Before pushing to avoid PR conflicts
- After seeing "branch is behind develop" warnings

## Implementation

```
Task: spawn git-workflow-manager
Prompt: |
  Sync current feature branch with develop.
  $ACTION = sync-develop
  $REPOS = [all repos in workspace]
```

## Example Output

```
[git-workflow-manager] Syncing with latest develop...
[git-workflow-manager] Fetched origin/develop
[git-workflow-manager] Branch was 3 commits behind develop
[git-workflow-manager] Merged origin/develop ✓
[git-workflow-manager] Branch is now up-to-date with develop

Sync complete. No conflicts.
```

## If Conflicts Occur

```
[git-workflow-manager] MERGE CONFLICT detected
[git-workflow-manager] Conflicting files:
  - src/Components/Quiz.tsx
  - src/hooks/useQuiz.ts

Please resolve conflicts manually:
1. Open the conflicting files
2. Resolve the conflicts (look for <<<<<<< markers)
3. Stage the resolved files: git add <file>
4. Complete the merge: git commit
```
