# CI/CD Package Publishing

This document describes how packages are built, versioned, and published through CI/CD pipelines.
Referenced by: package-release skill, feature-implementor, commit-manager agents

---

## Overview

The system uses GitHub Actions for CI/CD with packages published to GitHub Packages (both NPM and NuGet registries). Package builds are triggered by pushes to `main` and `develop` branches, with prerelease versions generated for non-main branches.

---

## Package Repositories

### NPM Packages (mf-packages)

**Repository:** `mf-packages`  
**Registry:** GitHub Packages NPM (`npm.pkg.github.com/@brainforgeau`)  
**Scope:** `@brainforgeau`

| Package | Workflow File | Trigger Paths |
|---------|--------------|---------------|
| @brainforgeau/components | build-components.yml | packages/components/** |
| @brainforgeau/security | build-security.yml | packages/security/** |
| @brainforgeau/theme | build-theme.yml | packages/theme/** |
| @brainforgeau/observability | build-observability.yml | packages/observability/** |

**Combined workflow:** `build-and-deploy.yml` - Detects changes across all packages and builds Docker image for MFS serving.

### NuGet Packages (dotnet-core)

**Repository:** `dotnet-core`  
**Registry:** GitHub Packages NuGet (`nuget.pkg.github.com/brainforgeau`)  
**Target Framework:** .NET 10.0

| Package | Workflow File |
|---------|--------------|
| Services.Core | services-core.yml |
| Services.Core.Abstractions | services-core-abstractions.yml |
| Services.Core.Auth.Keycloak | services-core-auth-keycloak.yml |
| Services.Core.Caching | services-core-caching.yml |
| Services.Core.Caching.Abstractions | services-core-caching-abstractions.yml |
| Services.Core.Caching.EntityFramework | services-core-caching-ef.yml |
| Services.Core.EntityFrameworkCore | services-core-entityframeworkcore.yml |
| Services.Core.Eventing.Abstractions | services-core-eventing-abstractions.yml |
| Services.Core.Eventing.Contracts | services-core-eventing-contracts.yml |
| Services.Core.Eventing.Redis | services-core-eventing-redis.yml |
| Services.Core.Http | services-core-http.yml |
| Services.Core.Observability | services-core-observability.yml |
| Services.Core.TenantAuth | services-core-tenantauth.yml |
| Services.Core.TenantAuth.Abstractions | services-core-tenantauth-abstractions.yml |
| Services.Core.TenantAuth.Redis | services-core-tenantauth-redis.yml |

---

## Version Strategy

All packages use a consistent versioning scheme based on branch:

### Main Branch (Production Release)
```
[MAJOR].[MINOR].[BUILD_NUMBER]
Example: 0.1.42
```

### Other Branches (Prerelease)
```
[MAJOR].[MINOR+1].[BUILD_NUMBER]-[BRANCH_SLUG].[SHORT_SHA]
Example: 0.2.42-develop.abc1234
Example: 0.2.43-feature-BF-123.def5678
```

**Key Points:**
- `MAJOR` and `MINOR` are defined in workflow env vars or repository variables
- `BUILD_NUMBER` is `github.run_number` (auto-incrementing per workflow)
- Prerelease versions use `MINOR+1` to ensure they sort higher than current release
- Branch slug: slashes replaced with dashes, special chars removed
- Short SHA: first 7 characters of commit hash

### Version Variables

**NPM Packages (mf-packages):**
- `VERSION_MAJOR: '0'`
- `VERSION_MINOR: '1'`

**NuGet Packages (dotnet-core):**
- `${{ vars.PACKAGE_VERSION_MAJOR || '0' }}`
- `${{ vars.PACKAGE_VERSION_MINOR || '1' }}`

---

## Build Triggers

### NPM Package Workflows

```yaml
on:
  push:
    branches: [ main, develop ]
    paths:
      - 'packages/[package-name]/**'
      - '.github/workflows/build-[package-name].yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'packages/[package-name]/**'
  workflow_dispatch:
```

**Important:** NPM packages are **NOT published** during pull requests. They are only built and uploaded as artifacts.

```yaml
- name: Publish package
  if: github.event_name != 'pull_request'  # <-- Only on push
  run: npm publish
```

### NuGet Package Workflows

```yaml
on:
  push:
    branches: [ main, develop ]
    paths:
      - '[PackagePath]/**'
      - 'Directory.Build.props'
      - '.github/workflows/[workflow-file].yml'
  pull_request:
    branches: [ main ]
    paths:
      - '[PackagePath]/**'
  workflow_dispatch:
```

**Important:** NuGet packages are **NOT published** during pull requests:

```yaml
- name: Publish package to GitHub Packages
  if: github.event_name == 'push'  # <-- Only on push
  run: dotnet nuget push ...
```

---

## API Client Generation

Backend services generate TypeScript NPM clients from their OpenAPI specifications.

### Services with Client Generation

| Backend | Client Package | Workflow |
|---------|---------------|----------|
| identity-management | @brainforgeau/identity-management-client | generate-client.yml |
| asset-backend | @brainforgeau/asset-backend-client | generate-client.yml |
| hr-backend | @brainforgeau/hr-backend-client | generate-client.yml |
| inventory-backend | @brainforgeau/inventory-backend-client | generate-client.yml |
| lms-backend | @brainforgeau/learning-backend-client | generate-client.yml |
| notification-backend | @brainforgeau/notification-backend-client | generate-client.yml |
| onboard-backend | @brainforgeau/onboard-backend-client | generate-client.yml |

### Client Generation Workflow

```yaml
on:
  push:
    branches: [ main, develop ]
    paths:
      - 'openapi/**'
      - '.github/workflows/generate-client.yml'
      - '[ServiceName].Api/**'
      - '[ServiceName].Application/**'
      - '[ServiceName].Domain/**'
      - '[ServiceName].Infrastructure/**'
  workflow_dispatch:
```

### Generation Process

1. **Build API with Swagger configuration** - Generates OpenAPI spec
2. **Check for API changes** - Compares new spec with previous commit
3. **Skip if no changes** - Avoids unnecessary rebuilds
4. **Generate TypeScript client** - Uses OpenAPI Generator CLI (Java-based)
5. **Build and publish** - Compiles TypeScript and publishes to GitHub Packages

**Generator:** `openapi-generator-cli v7.16.0`  
**Template:** `typescript-axios`  
**Options:** `withInterfaces=true, withSeparateModelsAndApi=true`

### API Change Detection

The workflow intelligently detects API changes:

```bash
# Compare paths and schemas between old and new spec
jq -S '{paths: .paths, components: .components}' old-spec.json > old-api.json
jq -S '{paths: .paths, components: .components}' new-spec.json > new-api.json
diff old-api.json new-api.json
```

If no API changes detected, client generation is skipped (unless `workflow_dispatch`).

---

## Current Limitations

### No PR-Based Package Versions

**Current State:**
- Packages are only published from `main` and `develop` branches
- Pull requests only build artifacts (not published to registry)
- Cannot reference a specific PR's package version

**Impact on Development:**
- Cross-repo changes require merging to develop first
- Cannot test package changes in consuming apps until merged
- Feature development across repos is sequential, not parallel

### Workaround for Cross-Repo Testing

1. Build package locally
2. Use `pnpm link` or local file references
3. Test locally before merging
4. After merge to develop, update consuming apps

---

## Proposed Enhancement: PR-Based Package Versions

### Concept

Generate and publish packages from pull requests with PR-specific versions:

```
[MAJOR].[MINOR].[BUILD_NUMBER]-pr.[PR_NUMBER].[SHORT_SHA]
Example: 0.2.50-pr.123.abc1234
```

### Benefits

1. **Parallel development** - Test changes across repos before merging
2. **Claude agent integration** - Agents can reference PR versions during implementation
3. **Better CI** - Consuming apps can test against PR versions in their own PRs
4. **Faster iteration** - No need to merge to develop just to test integration

### Implementation Considerations

1. **Add pull_request trigger for publishing:**
```yaml
on:
  pull_request:
    branches: [ develop, main ]
    paths:
      - 'packages/**'
```

2. **Modify version generation:**
```bash
if [[ "${{ github.event_name }}" == "pull_request" ]]; then
  PR_NUMBER="${{ github.event.pull_request.number }}"
  VERSION="${MAJOR}.${MINOR}.${{ github.run_number }}-pr.${PR_NUMBER}.${SHORT_SHA}"
fi
```

3. **Publish prerelease packages:**
```bash
npm publish --tag pr-${PR_NUMBER}
```

4. **Cleanup old PR packages** - Add workflow to delete packages when PR is closed

### NPM Tag Strategy

| Branch/Event | Version Tag | Example |
|--------------|-------------|---------|
| main | latest | 0.1.42 |
| develop | develop | 0.2.42-develop.abc1234 |
| PR #123 | pr-123 | 0.2.43-pr.123.def5678 |

---

## Docker Image Building

### Microfrontend Deployments

Each microfrontend has a `docker-build.yml` workflow:

| Repository | Workflow | Registry |
|------------|----------|----------|
| app | docker-build-app.yml | ghcr.io/brainforgeau/app |
| hr-mf | docker-build.yml | ghcr.io/brainforgeau/hr-mf |
| asset-mf | docker-build.yml | ghcr.io/brainforgeau/asset-mf |
| identity-mf | docker-build.yml | ghcr.io/brainforgeau/identity-mf |
| inventory-mf | docker-build.yml | ghcr.io/brainforgeau/inventory-mf |
| lms-mf | docker-build.yml | ghcr.io/brainforgeau/lms-mf |
| navbar-mf | build-and-deploy.yml | ghcr.io/brainforgeau/navbar-mf |
| common-mf | docker-build.yml | ghcr.io/brainforgeau/common-mf |
| drivecom-mf | docker-build.yml | ghcr.io/brainforgeau/drivecom-mf |
| onboard-mf | docker-build.yml | ghcr.io/brainforgeau/onboard-mf |
| mf-packages | build-and-deploy.yml | ghcr.io/brainforgeau/mf-packages |

### Backend Deployments

Each backend has a `docker-build.yml` workflow:

| Repository | Registry |
|------------|----------|
| hr-backend | ghcr.io/brainforgeau/hr-backend |
| asset-backend | ghcr.io/brainforgeau/asset-backend |
| identity-management | ghcr.io/brainforgeau/identity-management |
| inventory-backend | ghcr.io/brainforgeau/inventory-backend |
| lms-backend | ghcr.io/brainforgeau/lms-backend |
| notification-backend | ghcr.io/brainforgeau/notification-backend |
| onboard-backend | ghcr.io/brainforgeau/onboard-backend |

### Image Versioning

Docker images use the same version scheme as packages:
- Main: `0.1.42`, `latest`
- Develop: `0.2.42-develop.abc1234`, `develop`
- PR (if implemented): `0.2.43-pr.123.def5678`

---

## GitOps Deployment

### Flux CD Integration

After Docker images are built, workflows update the infra repository:

```yaml
- name: Update Flux deployment
  if: github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main'
  run: |
    git clone https://...@github.com/.../infra.git
    cd infra
    sed -i "s|image: ...|image: $NEW_TAG|g" namespaces/brainforge/deployments/[service].yaml
    git commit -m "Update [service] image to $VERSION"
    git push
```

Flux then reconciles the cluster to match the updated manifests.

---

## Dependency Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CORE PACKAGES                                │
│  ┌─────────────────┐         ┌─────────────────┐                   │
│  │   dotnet-core   │         │   mf-packages   │                   │
│  │  (NuGet pkgs)   │         │   (NPM pkgs)    │                   │
│  └────────┬────────┘         └────────┬────────┘                   │
│           │ push to develop/main       │ push to develop/main      │
│           ▼                            ▼                            │
│  ┌─────────────────┐         ┌─────────────────┐                   │
│  │  GitHub Packages │         │ GitHub Packages │                   │
│  │     (NuGet)      │         │      (NPM)      │                   │
│  └────────┬────────┘         └────────┬────────┘                   │
└───────────┼──────────────────────────┼─────────────────────────────┘
            │                          │
            ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND SERVICES                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ hr-backend   │  │asset-backend │  │identity-mgmt │  ...         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │ push to develop/main (API changes)                        │
│         ▼                                                           │
│  ┌─────────────────────────────────────────────────┐               │
│  │         generate-client.yml workflows           │               │
│  │    Generates TypeScript clients from OpenAPI    │               │
│  └──────────────────────┬──────────────────────────┘               │
│                         │                                           │
│                         ▼                                           │
│  ┌─────────────────────────────────────────────────┐               │
│  │     @brainforgeau/*-backend-client (NPM)        │               │
│  └──────────────────────┬──────────────────────────┘               │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND APPS                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    hr-mf     │  │   asset-mf   │  │ identity-mf  │  ...         │
│  │ (consumes:   │  │ (consumes:   │  │ (consumes:   │              │
│  │  - security  │  │  - security  │  │  - security  │              │
│  │  - components│  │  - components│  │  - components│              │
│  │  - hr-client)│  │  -asset-cli) │  │  - id-client)│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Cross-Repo Change Workflow

### Current Process

1. **Core package change** (e.g., new component in mf-packages)
   - Create PR to mf-packages
   - Merge to develop
   - CI publishes `0.2.X-develop.abc1234`

2. **Update consuming app** (e.g., hr-mf)
   - Update package.json with new version
   - Create PR to hr-mf
   - Test with develop version
   - Merge when satisfied

### Proposed Process (with PR packages)

1. **Core package change**
   - Create PR #123 to mf-packages
   - CI publishes `0.2.X-pr.123.abc1234`

2. **Update consuming app** (simultaneously)
   - Create PR to hr-mf referencing `@brainforgeau/components@0.2.X-pr.123.abc1234`
   - Test both changes together
   - Merge mf-packages PR first (publishes stable version)
   - Update hr-mf PR to use stable version
   - Merge hr-mf PR

---

## Agent Integration Notes

### For feature-implementor agent:

When implementing features that span multiple repos:
1. Check if changes to core packages are needed
2. If yes, note that consuming apps will need updating AFTER core package merges
3. Create separate PRs for each repo
4. Document the dependency in PR descriptions

### For package-release agent:

After core package releases:
1. Scan consuming repos for outdated references
2. Create update PRs automatically
3. Track which apps need updates for each package release

---

## References

- NPM workflow examples: `mf-packages/.github/workflows/`
- NuGet workflow examples: `dotnet-core/.github/workflows/`
- Client generation examples: `identity-management/.github/workflows/generate-client.yml`
- Flux deployments: `infra/namespaces/brainforge/deployments/`
- GitHub Packages docs: https://docs.github.com/en/packages
