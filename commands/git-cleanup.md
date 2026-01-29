# /git-cleanup

Clean up after a merged PR. Switches to develop, pulls latest, and deletes the old feature branch.

## Usage

```
/git-cleanup
```

## What It Does

1. Switches to `develop` branch
2. Pulls latest changes (including your merged PR)
3. Deletes the local feature/fix branch you were on
4. Prunes stale remote tracking branches

## When to Use

Run this command after your PR has been merged on GitHub. This ensures your local repo is clean and ready for the next feature.

## Implementation

```
Task: spawn git-workflow-manager
Prompt: |
  Clean up after merged PR.
  $ACTION = cleanup
  $REPOS = [all repos in workspace]
```

## Example Output

```
[git-workflow-manager] Cleaning up after merged PR...
[git-workflow-manager] Switched to develop in lms-backend
[git-workflow-manager] Pulled latest develop ✓
[git-workflow-manager] Deleted local branch: feature/BF-123-add-quiz
[git-workflow-manager] Pruned stale remote branches ✓

Cleanup complete. Ready for next feature.
```
