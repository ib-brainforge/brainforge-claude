# Infrastructure Patterns

<!--
This file is referenced by: infrastructure-implementor, infrastructure-validator, feature-planner
Last verified: February 2026
-->

## Overview

Infrastructure follows GitOps principles with Flux CD managing deployments to Kubernetes.
All changes go through Git — no direct `kubectl apply`. The cluster watches the `security-upgrade-2` branch.

## Repository Structure

```
infra/
├── clusters/                          # Per-environment Flux configuration
│   ├── local-kube/
│   │   ├── infrastructure.yaml        # ALL Flux Kustomizations with dependency graph
│   │   ├── secrets/                   # SOPS-encrypted secrets
│   │   ├── cert-manager-config/       # Environment-specific cert config
│   │   └── cluster-config.yaml        # ConfigMap with env vars (NFS_SERVER, etc.)
│   ├── staging/
│   │   └── infrastructure.yaml
│   └── production/
│       └── infrastructure.yaml
├── namespaces/                        # One directory per component/namespace
│   ├── cilium/
│   │   ├── kustomization.yaml         # Kustomize kustomization (lists resources)
│   │   ├── helm-release.yaml          # Flux HelmRelease
│   │   ├── helm-repository.yaml       # Flux HelmRepository
│   │   ├── namespace.yaml
│   │   └── cilium-network-policies/   # CiliumNetworkPolicy resources
│   ├── linkerd/
│   │   ├── helm-release-cni.yaml
│   │   ├── helm-release-control-plane.yaml
│   │   ├── helm-release-crds.yaml
│   │   ├── certificates.yaml
│   │   └── network-policy-allow-control-plane.yaml
│   ├── monitoring/                    # kube-prometheus-stack
│   ├── cilium-monitoring/             # PrometheusRules/ServiceMonitors for cilium
│   ├── kyverno-monitoring/            # PrometheusRules/ServiceMonitors for kyverno
│   ├── gatekeeper-monitoring/         # ServiceMonitors for gatekeeper
│   ├── trivy-monitoring/              # PrometheusRules/ServiceMonitors for trivy
│   ├── backup-monitoring/             # PrometheusRules for backup
│   ├── netcorp-monitoring/            # ServiceMonitors for netcorp services
│   ├── netcorp/                       # Application workloads
│   ├── postgre/                       # CloudNativePG cluster
│   ├── redis/                         # Redis via Bitnami Helm
│   ├── rabbitmq/                      # RabbitMQ via operator
│   ├── mongodb/                       # MongoDB
│   └── ...
```

### Key Difference from Generic Patterns

This repo does NOT use `base/overlays/` structure. Each component lives in `namespaces/[component]/`
with a flat layout. Environment-specific overrides are done via Flux Kustomization `patches` in
`clusters/[env]/infrastructure.yaml`, NOT via Kustomize overlays.

## Cluster Details

| Setting | Value |
|---------|-------|
| Control plane | 192.168.50.100 |
| Workers | .101, .102, .103 |
| Pod CIDR | 10.244.0.0/16 |
| Service CIDR | 10.96.0.0/12 |
| CNI | Cilium 1.16.5 with WireGuard |
| Service Mesh | Linkerd with linkerd-cni |
| GitOps | Flux CD on branch `security-upgrade-2` |
| SSH | kube@192.168.50.100 (password: kubernetes) |

**IMPORTANT**: SSH is READ-ONLY for validation. Never make changes via SSH. All changes go through the Git repo.

## Flux Kustomization Patterns

### The Infrastructure File

ALL Flux Kustomization resources live in a single file: `clusters/[env]/infrastructure.yaml`.
This file defines the complete dependency graph for bootstrap ordering.

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: component-name
  namespace: flux-system
spec:
  dependsOn:
    - name: dependency-1        # Must be Ready before this starts
    - name: dependency-2
  interval: 5m
  path: ./namespaces/component-name
  prune: false                  # We use false to avoid accidental deletion
  sourceRef:
    kind: GitRepository
    name: flux-system
  wait: true                    # Wait for health checks to pass
  timeout: 10m
```

### Bootstrap Dependency Rules

**CRD dependencies MUST be explicit.** If a kustomization creates CRD instances, it MUST
depend on the kustomization that installs the CRD.

| CRD | Provided By | Consumers Must Depend On |
|-----|-------------|--------------------------|
| CiliumNetworkPolicy | `cilium` | Any kustomization with CiliumNetworkPolicy resources |
| PrometheusRule, ServiceMonitor | `monitoring` | Split into separate `*-monitoring` kustomizations |
| RecurringJob (longhorn.io) | `longhorn-system` | redis, mongodb, rabbitmq (and any using Longhorn backups) |
| Certificate, ClusterIssuer | `cert-manager` | cert-manager-config, linkerd |
| ConstraintTemplate | `gatekeeper-system` | gatekeeper-constraint-templates |
| ClusterPolicy (Kyverno) | `kyverno` | kyverno-config |

**Webhook ordering:** Gatekeeper and Kyverno register admission webhooks. During bootstrap,
if their webhook is registered before their pods are ready, ALL API server operations fail.
Kustomizations that create namespaces or resources subject to these webhooks should NOT
depend on them directly — let the webhooks come up in parallel and Flux will retry.

### Monitoring Resource Split Pattern

PrometheusRule and ServiceMonitor resources MUST NOT be in the same kustomization as the
service they monitor. They must be in a separate `*-monitoring` kustomization that depends
on BOTH `monitoring` (for CRDs) AND the parent service (for the namespace/endpoints).

```yaml
# In clusters/[env]/infrastructure.yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cilium-monitoring
  namespace: flux-system
spec:
  dependsOn:
    - name: monitoring          # Provides PrometheusRule/ServiceMonitor CRDs
    - name: cilium              # Provides the namespace and endpoints
  interval: 5m
  path: ./namespaces/cilium-monitoring
  prune: false
  sourceRef:
    kind: GitRepository
    name: flux-system
  wait: false                   # Monitoring add-ons don't block anything
  timeout: 5m
```

Similarly, helm-generated ServiceMonitors must be DISABLED (`serviceMonitor.enabled: false`)
in the HelmRelease values, and manually defined in the `-monitoring` kustomization instead.

## HelmRelease Patterns

### Standard HelmRelease

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: component-name
  namespace: target-namespace    # Where the release is installed
spec:
  interval: 1h
  chart:
    spec:
      chart: chart-name
      version: "1.x"            # Use semver constraints
      sourceRef:
        kind: HelmRepository
        name: repo-name
        namespace: flux-system
  timeout: 10m                  # Increase for slow installs (default 5m)
  install:
    remediation:
      retries: 3
  upgrade:
    remediation:
      retries: 3
  values:
    # Chart-specific values
```

### Anti-Patterns for HelmReleases

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| `upgrade.force: true` | Deletes and recreates ALL resources on upgrade |
| `cleanupOnFail: true` | Can delete data on transient failures |
| `strategy: uninstall` | Nuclear option — uninstalls everything |
| `remediateLastFailure: true` on install | Can loop uninstall/install forever |
| Dummy annotations to trigger restarts | Workaround for broken config — fix the root cause |

If a HelmRelease gets stuck, the fix is proper dependency ordering or a cluster recreate,
NOT adding remediation hacks.

## Cilium + CiliumNetworkPolicy Patterns

### Critical Rules

- Standard K8s NetworkPolicy `ipBlock` rules do NOT work with Cilium's datapath for ClusterIP service DNAT
- Must use `CiliumNetworkPolicy` with `toEntities: kube-apiserver` for egress to API server
- For webhook ingress from API server, use `fromEntities: [kube-apiserver, host]`
- `endpointSelector: {}` selects ALL pods in namespace — must add DNS + intra-namespace rules
- `cni.exclusive: false` in Cilium HelmRelease required for linkerd-cni chaining

### Standard CiliumNetworkPolicy for Webhook Components

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-k8s-api
  namespace: component-namespace
spec:
  endpointSelector: {}
  egress:
    - toEntities:
        - kube-apiserver
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
            - port: "6443"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s:k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
            - port: "53"
              protocol: TCP
    - toEndpoints:
        - {}
  ingress:
    - fromEntities:
        - kube-apiserver
        - host
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
            - port: "8443"
              protocol: TCP
```

### Linkerd CNI + Cilium

Linkerd-cni must chain into Cilium's CNI conflist. Race condition on bootstrap:
- If both start simultaneously, Cilium overwrites the conflist
- **Fix**: `linkerd` Flux Kustomization MUST depend on `cilium`
- `priorityClassName: system-node-critical` on linkerd-cni DaemonSet

## Kustomize Patterns (in-repo)

### Component kustomization.yaml

```yaml
# namespaces/[component]/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - helm-repository.yaml
  - helm-release.yaml
  # CiliumNetworkPolicies in subdirectory
  # PrometheusRules/ServiceMonitors in separate *-monitoring kustomization
```

### Namespace with PSS Labels

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: component-name
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
```

## Secret Management (SOPS)

Secrets are encrypted with SOPS using Age keys and stored in `clusters/[env]/secrets/`.

```yaml
# clusters/local-kube/secrets/secret-name.yaml (encrypted)
apiVersion: v1
kind: Secret
metadata:
  name: secret-name
  namespace: target-namespace
type: Opaque
stringData:
  key: ENC[AES256_GCM,data:...,tag:...,type:str]
```

Flux decrypts at reconciliation time via the `sops-age` secret:
```yaml
spec:
  decryption:
    provider: sops
    secretRef:
      name: sops-age
```

## Flux Operations

### Trigger Reconciliation
```bash
kubectl annotate gitrepository flux-system -n flux-system \
  reconcile.fluxcd.io/requestedAt=$(date +%s) --overwrite
```

### Suspend/Unsuspend HelmRelease (reset retry counters)
Don't do this via SSH — change `spec.suspend: true/false` in the repo.

### Check Status
```bash
kubectl get kustomizations -n flux-system
kubectl get helmrelease -A
```

## Validation

### YAML Syntax (local)
```bash
kubectl apply --dry-run=client -f file.yaml
```

### Kustomize Build (local)
```bash
kustomize build namespaces/[component]/
```

### Cluster Status (via SSH, read-only)
```bash
sshpass -p 'kubernetes' ssh -o StrictHostKeyChecking=no kube@192.168.50.100 \
  'kubectl get kustomizations -n flux-system'
```

## Current Bootstrap Layer Order

```
Layer 0: cluster-secrets
Layer 1 (parallel): nfs-provisioner, cert-manager, reloader, cilium,
                     gateway-api-crds, kyverno, trivy-system
Layer 1.5: gatekeeper-system(->cilium), longhorn-system(->secrets,cilium),
           velero(->secrets,cilium), database-operators(->nfs),
           kyverno-config(->kyverno), cilium-config(->cilium),
           envoy-gateway(->gateway-api-crds), cert-manager-config(->cert-manager),
           linkerd(->cert-manager,cilium), gatekeeper-constraint-templates(->gatekeeper)
Layer 2:  gatekeeper-config, local-cert-manager-config, envoy-gateway-config,
          linkerd-config, linkerd-viz, monitoring(->nfs,secrets),
          backup(->secrets,nfs), backup-jobs(->nfs,secrets)
Layer 3:  postgre, redis, rabbitmq, mongodb, strapi-postgres
Layer 4:  netcorp-app (->all data services)
Layer 4.5: *-monitoring kustomizations (->monitoring + parent)
```
