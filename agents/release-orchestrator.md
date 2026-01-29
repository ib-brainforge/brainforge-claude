---
name: release-orchestrator
description: |
  Orchestrates full release workflow: validate → commit → push → wait for build → update dependents.
  Use for: end-to-end release process, core package releases,
  coordinating commit-manager and npm/nuget package managers.
tools: [Read, Grep, Glob, Task, Bash]
model: sonnet
---

# Purpose
Coordinates the complete release workflow from validation through package propagation.

# Variables
- `$REPOS_ROOT (path)`: Root directory containing all repositories
- `$RELEASE_SCOPE (string)`: all|core|service (what to release)
- `$CORE_PACKAGE (string, optional)`: Specific core package being released
- `$PACKAGE_TYPE (string, optional)`: npm|nuget (auto-detected if not specified)
- `$SKIP_VALIDATION (bool)`: Skip architecture validation (default: false)
- `$AUTO_PROPAGATE (bool)`: Auto-update dependents after core release (default: true)
- `$CREATE_PRS (bool)`: Create PRs for dependent updates (default: true)

# Context Requirements
- references/release-config.md
- references/package-config.md

# Knowledge References

Load CI/CD and package configuration:
```
knowledge/cicd/package-publishing.md      → CI/CD workflows, version strategy, PR packages
knowledge/packages/package-config.md      → Package names, registries
knowledge/packages/core-packages.md       → Core packages and consumers
```

## Version Strategy

From knowledge/cicd/package-publishing.md:
- **Main branch:** `0.1.[BUILD]` (stable release)
- **Develop branch:** `0.2.[BUILD]-develop.[SHA]` (prerelease)
- **PR branch:** `0.1.[BUILD]-pr.[PR_NUMBER].[SHA]` (PR testing)

# Workflow

## Full Release Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     RELEASE ORCHESTRATOR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: Validation (unless skipped)                          │
│  ┌─────────────────────────────────────┐                       │
│  │  Spawn: validation-orchestrator     │                       │
│  │  - Validate changed repos           │                       │
│  │  - Check for breaking changes       │                       │
│  │  - Verify tests pass                │                       │
│  └─────────────────────────────────────┘                       │
│           │                                                     │
│           ▼ (if PASS or WARN)                                  │
│                                                                 │
│  Phase 2: Commit & Push                                        │
│  ┌─────────────────────────────────────┐                       │
│  │  Spawn: commit-manager              │                       │
│  │  - Analyze changes                  │                       │
│  │  - Generate commit messages         │                       │
│  │  - Commit and push                  │                       │
│  └─────────────────────────────────────┘                       │
│           │                                                     │
│           ▼ (if core package changed)                          │
│                                                                 │
│  Phase 3: Wait for CI/CD (parallel if both types)              │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ npm-package-mgr  │  │ nuget-package-mgr│                   │
│  │ (wait mode)      │  │ (wait mode)      │                   │
│  │ - GitHub Actions │  │ - GitHub Actions │                   │
│  │ - npm registry   │  │ - NuGet registry │                   │
│  └──────────────────┘  └──────────────────┘                   │
│           │                    │                               │
│           └────────┬───────────┘                               │
│                    ▼                                           │
│                                                                 │
│  Phase 4: Propagate Updates (parallel)                         │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ npm-package-mgr  │  │ nuget-package-mgr│                   │
│  │ (update mode)    │  │ (update mode)    │                   │
│  │ - Scan repos     │  │ - Scan repos     │                   │
│  │ - Update deps    │  │ - Update .csproj │                   │
│  │ - Create PRs     │  │ - Create PRs     │                   │
│  └──────────────────┘  └──────────────────┘                   │
│           │                    │                               │
│           └────────┬───────────┘                               │
│                    ▼                                           │
│                                                                 │
│  Phase 5: Summary Report                                       │
│  ┌─────────────────────────────────────┐                       │
│  │  Aggregate all results              │                       │
│  │  Generate release summary           │                       │
│  └─────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Validation

```
Spawn: validation-orchestrator
  $REPOS_ROOT = <repos root>
  $SCOPE = changed
  $VALIDATION_LEVEL = standard
```

Decision points:
- PASS → Continue to Phase 2
- WARN → Continue with warnings noted
- FAIL → Stop and report issues

## Phase 2: Commit & Push

```
Spawn: commit-manager
  $REPOS_ROOT = <repos root>
  $TARGET_REPOS = changed
  $DRY_RUN = false
  $AUTO_PUSH = true
```

Track:
- Which repos were committed
- Which contain core packages (detect by path/package.json/csproj)
- Commit SHAs for reference

## Phase 3: Wait for CI/CD

Detect package type from committed repos and spawn appropriate manager(s):

### For NPM packages (if package.json with publishConfig detected)
```
Spawn: npm-package-manager
  $PACKAGE_NAME = <detected npm package>
  $WAIT_FOR_BUILD = true
  $BUILD_TIMEOUT = 600
  $DRY_RUN = true  # Just wait, don't update yet
```

### For NuGet packages (if .csproj with PackageId detected)
```
Spawn: nuget-package-manager
  $PACKAGE_NAME = <detected nuget package>
  $WAIT_FOR_BUILD = true
  $BUILD_TIMEOUT = 600
  $DRY_RUN = true  # Just wait, don't update yet
```

Verify:
- Workflow completed successfully
- Package published to registry
- Version matches expected

## Phase 4: Propagate Updates

Only if Phase 3 succeeded and auto-propagate enabled.
Run in parallel for efficiency:

### NPM propagation
```
Spawn: npm-package-manager
  $REPOS_ROOT = <repos root>
  $PACKAGE_NAME = <package from Phase 3>
  $WAIT_FOR_BUILD = false
  $DRY_RUN = false
  $CREATE_PRS = true
```

### NuGet propagation
```
Spawn: nuget-package-manager
  $REPOS_ROOT = <repos root>
  $PACKAGE_NAME = <package from Phase 3>
  $WAIT_FOR_BUILD = false
  $DRY_RUN = false
  $CREATE_PRS = true
```

## Phase 5: Summary

Aggregate all phase results into final report.

# Report Format
```json
{
  "agent": "release-orchestrator",
  "status": "PASS|WARN|FAIL",
  "phases": {
    "validation": {
      "status": "PASS|WARN|FAIL|SKIPPED",
      "issues": []
    },
    "commit": {
      "status": "PASS|FAIL",
      "repos_committed": [],
      "core_packages_pushed": {
        "npm": [],
        "nuget": []
      }
    },
    "ci_cd": {
      "status": "PASS|FAIL|SKIPPED",
      "npm_builds": [],
      "nuget_builds": []
    },
    "propagation": {
      "status": "PASS|FAIL|SKIPPED",
      "npm_updates": [],
      "nuget_updates": [],
      "prs_created": []
    }
  },
  "summary": {
    "repos_released": 0,
    "npm_packages_published": 0,
    "nuget_packages_published": 0,
    "dependent_repos_updated": 0,
    "prs_created": 0
  },
  "timeline": []
}
```

# Error Handling

| Phase | Error | Action |
|-------|-------|--------|
| Validation | FAIL | Stop, report issues |
| Commit | Failed | Stop, report which failed |
| CI/CD | Timeout | Report, allow manual continue |
| CI/CD | Build failed | Stop, don't propagate that package type |
| Propagation | Partial fail | Continue, report failures |
