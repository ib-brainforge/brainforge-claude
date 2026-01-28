---
name: package-release
description: |
  Package version management and release orchestration.
  Monitors CI/CD, propagates versions across repositories.
  All package names and registries loaded from knowledge files.
triggers:
  - /update-packages
  - /release
  - update packages
  - propagate versions
  - check package versions
---

# Purpose

Monitor core package CI/CD pipelines, detect new versions, and propagate updates
across all dependent repositories. All package-specific configuration is loaded
from knowledge files.

# Usage

```
/update-packages                     # Check and update all packages
/update-packages --ecosystem npm     # Frontend packages only
/update-packages --ecosystem nuget   # Backend packages only
/update-packages --check-only        # Check for updates, don't apply
/update-packages --package [name]    # Specific package
/release                             # Full release workflow
```

# Variables

- `$REPOS_ROOT (path)`: Path to repositories (default: .)
- `$ECOSYSTEM (string)`: npm|nuget|all (default: all)
- `$CHECK_ONLY (bool)`: Don't apply updates (default: false)
- `$PACKAGE (string, optional)`: Specific package to update
- `$AUTO_COMMIT (bool)`: Commit changes automatically (default: false)
- `$AUTO_PR (bool)`: Create PRs for updates (default: false)

# Knowledge References

Load ALL package configuration from:

```
knowledge/packages/package-config.md      → Package names, registries, feeds, workflows
knowledge/packages/core-packages.md       → Core package list and their APIs
```

**IMPORTANT**: Do not hardcode any package names, registry URLs, or specific
packages in this skill. All such information must come from knowledge files.

**Note**: This skill does NOT record learnings. Only `commit-manager` writes to learned YAML files.

# Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PACKAGE RELEASE WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. LOAD KNOWLEDGE                                                           │
│     └──► Read package-config.md for package names and registries             │
│                                                                              │
│  2. CHECK CI/CD STATUS                                                       │
│     └──► Bash: gh workflow list / gh run list                                │
│                                                                              │
│  3. DETECT NEW VERSIONS                                                      │
│     └──► Check npm registry / NuGet feed for latest versions                 │
│                                                                              │
│  4. FIND DEPENDENTS                                                          │
│     └──► Grep for package references in repos                                │
│                                                                              │
│  5. UPDATE DEPENDENTS                                                        │
│     └──► Update package.json / *.csproj files                                │
│                                                                              │
│  6. COMMIT & PR (if enabled)                                                 │
│     └──► Use commit-manager skill                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

# Instructions

## 1. Load Knowledge First

```
Read: knowledge/packages/package-config.md
Read: knowledge/packages/core-packages.md
```

Extract from knowledge:
- Frontend package names and npm registry
- Backend package names and NuGet feed
- CI workflow names
- Organization/scope info

## 2. Check CI/CD Status

### For GitHub Actions
```
Bash: gh workflow list --repo [package-repo]
Bash: gh run list --workflow "[workflow-name]" --repo [package-repo] --limit 1
```

Check if latest builds passed for core packages.

### Parse Results
- Extract workflow status (success/failure)
- Get latest version from successful builds

## 3. Detect New Versions

### Frontend (npm)
```
Bash: npm view [package-name] version
Bash: npm view [package-name] versions --json
```

### Backend (NuGet)
```
Bash: dotnet nuget list source
Bash: curl -s "[nuget-feed]/[package-name]/index.json" | jq '.versions[-1]'
```

Or using nuget CLI:
```
Bash: nuget list [package-name] -Source [feed-url]
```

## 4. Find Dependent Repositories

### Frontend Dependents
```
Grep: "[package-name]" in $REPOS_ROOT/**/package.json
```

For each match:
```
Read: [repo]/package.json
```

Parse to check if package is in dependencies or devDependencies.

### Backend Dependents
```
Grep: "[package-name]" in $REPOS_ROOT/**/*.csproj
```

For each match:
```
Read: [repo]/[project].csproj
```

Parse PackageReference elements for version.

## 5. Compare Versions

For each dependent:
- Get current version from package.json or .csproj
- Compare with latest available version
- Determine if update is needed (patch, minor, major)

## 6. Update Dependencies

### Frontend (package.json)

Read current:
```
Read: [repo]/package.json
```

Update version and write:
```
Edit: [repo]/package.json
  - Change "[package]": "[old-version]" to "[package]": "[new-version]"
```

Then:
```
Bash: cd [repo] && npm install
```

### Backend (.csproj)

Read current:
```
Read: [repo]/[project].csproj
```

Update PackageReference:
```
Edit: [repo]/[project].csproj
  - Change Version="[old]" to Version="[new]"
```

Then:
```
Bash: cd [repo] && dotnet restore
```

## 7. Check Only Mode

If $CHECK_ONLY:
- List all available updates
- Show current vs latest versions
- Don't make any changes

## 8. Auto Commit (if enabled)

If $AUTO_COMMIT:
```
Use skill: commit-manager
  --scope all
  --feature-tag "deps-update"
```

## 9. Auto PR (if enabled)

If $AUTO_PR:
```
Bash: git checkout -b deps/update-[package]-[version]
Bash: gh pr create --title "chore(deps): update [package] to [version]" \
  --base develop \
  --body "Automated package update from package-release skill"
```
<!-- Corrected 2026-01-28: Added --base develop per GitFlow rules (PRs must target develop, not main) -->

# Report Format

```json
{
  "skill": "package-release",
  "status": "PASS|WARN|FAIL",
  "ci_status": {
    "frontend": {
      "package": "@org/core",
      "workflow": "publish-npm",
      "status": "success",
      "latest_version": "2.1.0"
    },
    "backend": {
      "package": "Org.Core",
      "workflow": "publish-nuget",
      "status": "success",
      "latest_version": "3.0.1"
    }
  },
  "updates": {
    "frontend": {
      "available": 5,
      "applied": 5,
      "repos_updated": [
        {
          "repo": "user-frontend",
          "package": "@org/core",
          "from": "2.0.0",
          "to": "2.1.0"
        }
      ]
    },
    "backend": {
      "available": 3,
      "applied": 3,
      "repos_updated": [
        {
          "repo": "user-service",
          "package": "Org.Core",
          "from": "3.0.0",
          "to": "3.0.1"
        }
      ]
    }
  },
  "commits": [],
  "prs": [],
  "warnings": []
}
```

# Version Update Rules

| Update Type | Example | Action |
|-------------|---------|--------|
| Patch | 1.0.0 → 1.0.1 | Auto-update |
| Minor | 1.0.0 → 1.1.0 | Auto-update (with flag) |
| Major | 1.0.0 → 2.0.0 | Requires --allow-major |

# Note on Learnings

**This skill does NOT record learnings.**

Package updates are operational tasks. Significant dependency changes
(like major upgrades or new packages) should be recorded by `commit-manager`
when the changes are committed.

# Related Skills

- `validation` - Validate builds pass with new versions
- `commit-manager` - Commit version updates
- `feature-planning` - Plan major version upgrades
