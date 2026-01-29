# Knowledge Base

This folder contains **domain-specific knowledge** for your project. When using this setup in a new project, you only need to update files in this folder.

## Structure

```
knowledge/
├── validation/                      # Patterns for validators
│   ├── backend-patterns.md          # Backend grep patterns + anti-patterns
│   ├── frontend-patterns.md         # Frontend grep patterns + anti-patterns
│   ├── security-standards.md        # Security requirements
│   └── validation-config.md         # Validation levels, scopes
├── architecture/                    # System architecture
│   ├── system-architecture.md       # System overview, ADRs
│   ├── service-boundaries.md        # Service interaction rules
│   ├── design-patterns.md           # Required patterns (guidance)
│   └── tech-stack.md                # Frameworks, versions
├── packages/                        # Package management
│   ├── core-packages.md             # Shared package APIs
│   ├── package-config.md            # NPM/NuGet settings
│   └── repo-config.md               # Repo-specific settings
├── infrastructure/                  # Infrastructure patterns
│   └── infrastructure-patterns.md   # Kubernetes, GitOps, IaC patterns
├── cicd/                            # CI/CD pipelines
│   └── package-publishing.md        # Package build, version, publish workflows
└── commit-conventions.md            # Commit message format
```

## File Purposes

### validation/
Focused grep patterns for validator agents. Each validator loads only what it needs.

| File | Used By | Contains |
|------|---------|----------|
| `backend-patterns.md` | backend-pattern-validator | Stack detection, API/DB/security patterns |
| `frontend-patterns.md` | frontend-pattern-validator | **UI Design Language (JIRA design)**, framework detection, component patterns |
| `security-standards.md` | plan-validator | Auth, data protection, audit requirements |
| `validation-config.md` | validation-orchestrator | Levels, scopes, exclusions |

**IMPORTANT:** `frontend-patterns.md` contains the mandatory UI component usage rules. All UI changes MUST follow the JIRA design language and use @brainforgeau/components over raw HeroUI.

### architecture/
System design and high-level patterns (no grep patterns here).

| File | Used By | Contains |
|------|---------|----------|
| `system-architecture.md` | master-architect | Service map, data flows, ADRs |
| `service-boundaries.md` | plan-validator, master-architect | Service responsibilities |
| `design-patterns.md` | design-pattern-advisor | Pattern guidance, examples |
| `tech-stack.md` | all validators | Framework versions |

### packages/
Package management configuration.

| File | Used By | Contains |
|------|---------|----------|
| `core-packages.md` | validators, design-pattern-advisor | Shared package APIs |
| `package-config.md` | npm/nuget-package-manager | Registry URLs, package names |
| `repo-config.md` | commit-manager | Branch rules, commit prefixes |

### cicd/
CI/CD pipeline documentation.

| File | Used By | Contains |
|------|---------|----------|
| `package-publishing.md` | package-release, feature-implementor | Build triggers, versioning, API client generation |

## How Agents Load Knowledge

Each agent loads **only the file(s) it needs**:

```
backend-pattern-validator   →  validation/backend-patterns.md
frontend-pattern-validator  →  validation/frontend-patterns.md
infrastructure-implementor  →  infrastructure/infrastructure-patterns.md
infrastructure-validator    →  infrastructure/infrastructure-patterns.md
                               architecture/tech-stack.md
plan-validator              →  validation/security-standards.md
                               architecture/service-boundaries.md
validation-orchestrator     →  validation/validation-config.md
master-architect            →  architecture/system-architecture.md
commit-manager              →  commit-conventions.md
                               packages/repo-config.md
package-release             →  cicd/package-publishing.md
                               packages/package-config.md
feature-implementor         →  cicd/package-publishing.md (for cross-repo awareness)
```

## Using in a New Project

1. Copy the entire `claude-code-setup/` folder
2. Update files in `knowledge/` for your project
3. Agents/skills work automatically with new knowledge

## Why This Structure?

**Focused files** = less context loaded = faster, more accurate agents

Each validator loads ~100 lines instead of 500+ lines of mixed content.
