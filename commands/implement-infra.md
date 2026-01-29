---
name: /implement-infra
description: Implement infrastructure changes using the infrastructure-implementor agent
allowed_tools: [Read, Task]
---

# Purpose

Implement infrastructure changes (Kubernetes, GitOps, IaC) autonomously.

**CRITICAL**: Do NOT implement infrastructure yourself. Spawn `infrastructure-implementor`.

## Usage

```
/implement-infra "Add Redis deployment for caching"
/implement-infra "Create Kubernetes resources for new notification-service"
/implement-infra "Add HelmRelease for monitoring stack"
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
  $INFRA_ROOT = [path to infrastructure repository]
  $REPOS_ROOT = [current working directory]

  Complete all work autonomously:
  1. Analyze existing patterns
  2. Create/modify resources
  3. Validate manifests
  4. Report changes

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
  $INFRA_ROOT = [path to infrastructure repository]
  $REPOS_ROOT = [current working directory]

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
            ├──► Load knowledge/infrastructure/
            │
            ├──► Find existing patterns
            │
            ├──► Create/modify manifests
            │     ├── base/redis/
            │     ├── overlays/[env]/redis/
            │     └── clusters/[env]/redis.yaml
            │
            ├──► Validate with kustomize build
            │
            └──► Return summary with REVIEW comments
```

## What Gets Created

Typical output for a new service:

```
base/[service]/
├── deployment.yaml
├── service.yaml
├── configmap.yaml
└── kustomization.yaml

overlays/production/[service]/
├── kustomization.yaml
└── patch-deployment.yaml

clusters/production/apps/[service].yaml (Flux Kustomization)
```

## Related Commands

- `/implement-feature "description"` - Full feature (may include infra)
- `/validate` - Validate all architecture including infrastructure
