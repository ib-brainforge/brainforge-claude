---
name: /implement-infra
description: Implement infrastructure changes using the infrastructure-implementor agent
allowed_tools: [Read, Task]
---

# Purpose

Implement infrastructure changes (Kubernetes, GitOps, Flux) autonomously for the local-kube cluster.

**CRITICAL**: Do NOT implement infrastructure yourself. Spawn `infrastructure-implementor`.

## Usage

```
/implement-infra "Add CiliumNetworkPolicy for new-service namespace"
/implement-infra "Create HelmRelease for Redis caching"
/implement-infra "Fix bootstrap ordering for monitoring dependencies"
/implement-infra "Add new component with Flux Kustomization"
```

## What To Do

**IMMEDIATELY spawn the implementor. Do NOT do any work yourself.**

```
[main] Detected infrastructure implementation request
[main] Spawning infrastructure-implementor...

Task: spawn infrastructure-implementor
Prompt: |
  Implement infrastructure changes.
  Feature: [USER'S DESCRIPTION]
  $INFRA_ROOT = /Users/ivanbernatovic/Projects/bf-github/infra
  $REPOS_ROOT = /Users/ivanbernatovic/Projects/bf-github

  Complete all work autonomously:
  1. Read knowledge/infrastructure/infrastructure-patterns.md FIRST
  2. Analyze existing patterns in namespaces/ and clusters/local-kube/infrastructure.yaml
  3. Create/modify resources following flat namespaces/[component]/ structure
  4. Ensure CRD dependencies in infrastructure.yaml
  5. Split monitoring resources to *-monitoring kustomizations
  6. Validate manifests with kustomize build
  7. Report changes with REVIEW: comments
  8. If structural changes need fresh bootstrap, tell user to recreate cluster

  DO NOT STOP TO ASK QUESTIONS.
  Make reasonable assumptions, document with REVIEW: comments.
```

## If User Answers a Question

When user provides feedback/decision during the workflow, **RE-SPAWN the implementor**:

```
[main] User provided decision, re-spawning infrastructure-implementor...

Task: spawn infrastructure-implementor
Prompt: |
  CONTINUE infrastructure implementation with user decision.
  Original request: [ORIGINAL DESCRIPTION]
  User decision: [WHAT USER CHOSE]
  Previous work: [SUMMARY OF WHAT WAS DONE]
  $INFRA_ROOT = /Users/ivanbernatovic/Projects/bf-github/infra
  $REPOS_ROOT = /Users/ivanbernatovic/Projects/bf-github

  Resume and complete remaining work.
```

**NEVER continue the work yourself after user feedback!**

## Flow Diagram

```
/implement-infra "Add Redis"
       │
       ▼
┌──────────────────────────┐
│ infrastructure-implementor│ ◄── You spawn ONLY this
└───────────┬──────────────┘
            │
            ├──► Load knowledge/infrastructure/infrastructure-patterns.md
            │
            ├──► Read clusters/local-kube/infrastructure.yaml (dependency graph)
            │
            ├──► Find existing patterns in namespaces/
            │
            ├──► Create/modify manifests
            │     ├── namespaces/[component]/
            │     │   ├── namespace.yaml
            │     │   ├── helm-repository.yaml
            │     │   ├── helm-release.yaml (serviceMonitor.enabled: false)
            │     │   └── kustomization.yaml
            │     ├── namespaces/[component]-monitoring/  (if monitoring needed)
            │     │   ├── kustomization.yaml
            │     │   └── servicemonitor.yaml
            │     └── clusters/local-kube/infrastructure.yaml (Flux Kustomizations)
            │
            ├──► Validate with kustomize build
            │
            ├──► If structural: tell user "vagrant destroy && vagrant up"
            │
            └──► Return summary with REVIEW comments
```

## What Gets Created

Typical output for a new Helm-based service:

```
namespaces/[service]/
├── namespace.yaml              # With PSS labels
├── helm-repository.yaml        # Flux HelmRepository
├── helm-release.yaml           # Flux HelmRelease (serviceMonitor disabled)
└── kustomization.yaml          # Lists resources

namespaces/[service]-monitoring/  (if monitoring needed)
├── kustomization.yaml
├── prometheus-rules.yaml
└── servicemonitor.yaml

clusters/local-kube/infrastructure.yaml  (modified)
  + [service] Flux Kustomization with dependsOn
  + [service]-monitoring Flux Kustomization (depends on monitoring + service)
```

## Key Patterns the Agent Follows

- **Flat structure**: `namespaces/[component]/`, NOT base/overlays
- **Single infrastructure.yaml**: ALL Flux Kustomizations with dependency graph
- **CRD dependencies**: Must declare dependsOn for CRD providers
- **Monitoring split**: PrometheusRule/ServiceMonitor in separate `*-monitoring` kustomization
- **CiliumNetworkPolicy**: For webhook components (not standard K8s NetworkPolicy)
- **No workarounds**: Never force/cleanupOnFail/uninstall strategy on HelmReleases
- **Git only**: SSH to cluster is read-only validation. All changes through Git.

## Related Commands

- `/implement-feature "description"` - Full feature (may include infra)
- `/validate` - Validate all architecture including infrastructure
