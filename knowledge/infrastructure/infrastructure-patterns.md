# Infrastructure Patterns

<!--
This file is referenced by: infrastructure-implementor, infrastructure-validator, feature-planner
Last verified: January 2025

NOTE: This file contains GENERIC patterns. Project-specific details (repo paths,
service names, environment names) should be added for your project.
-->

## Overview

Infrastructure follows GitOps principles with Flux CD managing deployments to Kubernetes.
All changes go through Git - no direct `kubectl apply` in production.

## Repository Structure

```
infrastructure/
├── base/                           # Base Kubernetes manifests
│   ├── [service-name]/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── kustomization.yaml
│   └── ...
├── overlays/                       # Environment-specific overrides
│   ├── development/
│   │   ├── [service-name]/
│   │   │   ├── kustomization.yaml
│   │   │   └── patch-*.yaml
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── ...
│   └── production/
│       └── ...
├── clusters/                       # Flux GitOps configuration
│   ├── development/
│   │   ├── flux-system/
│   │   └── apps.yaml              # Kustomization pointing to overlays
│   ├── staging/
│   │   └── ...
│   └── production/
│       └── ...
├── charts/                         # Helm charts (if used)
│   └── [chart-name]/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
└── terraform/                      # IaC for cloud resources (if used)
    ├── modules/
    └── environments/
```

## Kustomize Patterns

### Base Resource Template

```yaml
# base/[service]/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-name
  labels:
    app: service-name
    version: v1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-name
  template:
    metadata:
      labels:
        app: service-name
        version: v1
    spec:
      containers:
        - name: service-name
          image: registry/service-name:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Base Kustomization

```yaml
# base/[service]/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  app.kubernetes.io/name: service-name
  app.kubernetes.io/part-of: platform
```

### Overlay Kustomization

```yaml
# overlays/production/[service]/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production

resources:
  - ../../../base/[service]

patches:
  - path: patch-deployment.yaml

configMapGenerator:
  - name: service-config
    behavior: merge
    literals:
      - ENVIRONMENT=production
```

### Overlay Patch

```yaml
# overlays/production/[service]/patch-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-name
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: service-name
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
```

## Flux CD Patterns

### Kustomization Resource

```yaml
# clusters/production/apps/service-name.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: service-name
  namespace: flux-system
spec:
  interval: 10m
  path: ./overlays/production/service-name
  prune: true
  sourceRef:
    kind: GitRepository
    name: infrastructure
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: service-name
      namespace: production
```

### HelmRelease Resource

```yaml
# clusters/production/apps/service-name.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: service-name
  namespace: flux-system
spec:
  interval: 10m
  chart:
    spec:
      chart: ./charts/service-name
      sourceRef:
        kind: GitRepository
        name: infrastructure
  values:
    replicaCount: 3
    image:
      repository: registry/service-name
      tag: v1.0.0
```

## Secret Management (SOPS)

### Encrypted Secret Template

```yaml
# overlays/production/[service]/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: service-secrets
type: Opaque
stringData:
  DATABASE_URL: ENC[AES256_GCM,data:...,tag:...,type:str]
  API_KEY: ENC[AES256_GCM,data:...,tag:...,type:str]
```

### SOPS Configuration

```yaml
# .sops.yaml (at repo root)
creation_rules:
  - path_regex: overlays/production/.*\.yaml$
    age: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  - path_regex: overlays/staging/.*\.yaml$
    age: age1yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

### Creating Encrypted Secrets

```bash
# Encrypt a secret file
sops -e -i overlays/production/service/secret.yaml

# Decrypt for editing
sops overlays/production/service/secret.yaml
```

## Common Resource Patterns

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-name
spec:
  selector:
    app: service-name
  ports:
    - name: http
      port: 80
      targetPort: 8080
  type: ClusterIP
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: service-config
data:
  ENVIRONMENT: production
  LOG_LEVEL: info
  FEATURE_FLAGS: '{"newFeature": true}'
```

### Ingress (via Gateway API)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: service-route
spec:
  parentRefs:
    - name: main-gateway
  hostnames:
    - "api.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api/service
      backendRefs:
        - name: service-name
          port: 80
```

### Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: service-network-policy
spec:
  podSelector:
    matchLabels:
      app: service-name
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-gateway
      ports:
        - port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - port: 5432
```

## Validation Commands

```bash
# Validate YAML syntax
kubectl apply --dry-run=client -f file.yaml

# Build Kustomize overlay
kustomize build overlays/production/service-name

# Validate Helm chart
helm lint charts/service-name
helm template charts/service-name --values values.yaml

# Check Flux reconciliation
flux reconcile kustomization service-name

# Validate Terraform
cd terraform/environments/production && terraform validate
```

## Anti-Patterns (AVOID)

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Hardcoded secrets in manifests | Use SOPS-encrypted secrets |
| No resource limits | Always set requests and limits |
| `latest` image tag in production | Use specific version tags |
| Direct kubectl apply | Commit to Git, let Flux reconcile |
| Skipping health probes | Always configure liveness/readiness |
| Single replica in production | Use at least 2 replicas for HA |
| No network policies | Define explicit ingress/egress rules |

## Labels Standard

All resources MUST have these labels:

```yaml
labels:
  app.kubernetes.io/name: service-name
  app.kubernetes.io/instance: service-name-production
  app.kubernetes.io/version: "1.0.0"
  app.kubernetes.io/component: backend  # or frontend, database, etc.
  app.kubernetes.io/part-of: platform-name
  app.kubernetes.io/managed-by: flux
```

## Environment-Specific Defaults

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Replicas | 1 | 2 | 3+ |
| Memory Request | 128Mi | 256Mi | 512Mi |
| Memory Limit | 256Mi | 512Mi | 1Gi |
| CPU Request | 50m | 100m | 250m |
| CPU Limit | 100m | 200m | 500m |
| Log Level | debug | info | info |

---

## Project-Specific Configuration

<!--
Add your project-specific details below:
- Infrastructure repository path
- Environment names
- Service naming conventions
- Registry URLs
- SOPS age keys
-->

### Repository Paths

```
$INFRA_REPO = [TODO: Add path to infrastructure repository]
$REGISTRY = [TODO: Add container registry URL]
```

### Environments

```
development → overlays/development/
staging     → overlays/staging/
production  → overlays/production/
```

### Service Naming

```
[service-name]-backend  → Backend services
[service-name]-mf       → Microfrontend applications
[service-name]-worker   → Background workers
```
