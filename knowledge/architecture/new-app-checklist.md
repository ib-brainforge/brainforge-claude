# New App Introduction Checklist

<!--
This file documents the complete process for introducing a new application
to the BrainForge/NetCorp360 platform. Follow every step to ensure the app
is fully integrated across all system components.

Last verified: February 2025 (tracking app introduction)
Referenced by: feature-implementor, master-architect, infrastructure-implementor
-->

## Overview

Adding a new app to the platform requires changes across multiple repositories.
This checklist covers all integration points using the tracking app as the
reference implementation.

## Step-by-Step Checklist

### 1. Backend Service

**Repository:** `{app}-backend`

- [ ] Create Clean Architecture project structure (Domain/Infrastructure/Application/Api)
- [ ] Configure `appsettings.json` with production values:
  - `Service.Id` - Unique GUID (coordinate to avoid conflicts)
  - `Service.Name` - Service name
  - `Authentication.Keycloak.Audience` - Must match Keycloak client ID
  - `NotificationService.BaseUrl` - Use `http://notification-backend.brainforge.svc.cluster.local`
  - `ServiceAccount` - Token URL, ClientId, ClientSecret for M2M auth
  - `ConnectionStrings.Redis` - Use `Redis` key (not `Cache`) for consistency
  - `Observability` - OpenTelemetry, Prometheus, Loki
- [ ] Create `appsettings.Development.json` with local overrides:
  - OTLP endpoint: `http://localhost:4317`
  - Notification service: `http://localhost:5300`
  - ServiceAccount TokenUrl: `http://localhost:8080/realms/test/...`
- [ ] Create production-ready Dockerfile (multi-stage Alpine build)
- [ ] Configure CI/CD pipeline for container image builds
- [ ] Generate TypeScript client package (`@brainforgeau/{app}-client`)

### 2. Frontend Microfrontend

**Repository:** `{app}-mf`

- [ ] Create Modern.js project with Module Federation
- [ ] Configure shared dependencies (react, jotai, heroui, security)
- [ ] Use generated `@brainforgeau/{app}-client` for API calls (never raw fetch)
- [ ] Configure CI/CD pipeline for container image builds

### 3. App Shell - Root Page

**Repository:** `app`
**File:** `src/routes/page.tsx`

- [ ] Import the app icon from `@brainforgeau/components/icons`
- [ ] Add app entry to the `apps` array with:
  - `id` - App identifier (must match identity-management app name and license key)
  - `name` - Display name
  - `path` - URL path (e.g., `/tracking`)
  - `icon` - Icon component
  - `description` - Short description
  - `color` - Tailwind background color class
  - `requiredRolePrefix` - Must match the `prefix` in identity-management config

The root page automatically filters by both role-based access AND tenant license
via `hasLicensedApp(app.id)`.

### 4. Navbar App Switcher

**Repository:** `navbar-mf`
**File:** `src/state/apps.tsx`

- [ ] Import the app icon from `@brainforgeau/components/icons`
- [ ] Add app entry to the `apps` array (same structure as root page, plus `colorHex`)
- [ ] Ensure `id` matches the identity-management app name exactly

The navbar also filters by role access, license, and whitelabel configuration.

### 5. Identity Management - Permissions & Licensing

**Repository:** `identity-management`
**File:** `IdentityManagement.Api/Config/AppPermissions/{app}.json`

- [ ] Create JSON permission config file with:
  - `name` - Lowercase app identifier (MUST match `id` in navbar and root page)
  - `displayName` - Human-readable name
  - `prefix` - Keycloak role prefix (MUST match `requiredRolePrefix` in navbar/root page)
  - `displayOrder` - Sort order in admin UI
  - `scopeTypes` - Data access boundaries (own, location, division, organisation, tenant)
  - `resourceGroups` - Groups of related permissions
  - `roles` - Predefined roles (viewer, operator, manager, admin) with permission bundles

The `AppPermissionSyncHostedService` automatically syncs JSON to database on startup.
No code changes needed.

**Licensing:** Tenants must have the app ID added to their `LicensedApps` list in
`TenantSettings` via the `UpdateTenantLicenseCommand` API or direct DB update.

### 6. Infrastructure (Kubernetes)

**Repository:** `infra`

- [ ] Create Deployment YAML with:
  - Labels: `app: {service}`, `repository: bf-github`
  - Environment variables for all config (connection strings, auth, observability)
  - Secret references for sensitive values (context token signing key, service account secret)
  - Resource requests/limits
  - Image pull secrets
- [ ] Create Service YAML (ClusterIP for internal, LoadBalancer for TCP listeners)
- [ ] Create Secret YAML (sealed/encrypted)
- [ ] Configure ingress routes (add path rules to ingress.yaml)
- [ ] Create ServiceMonitor for Prometheus scraping
- [ ] Add to Kustomization resources list
- [ ] (Optional) HorizontalPodAutoscaler for auto-scaling
- [ ] (Optional) PodDisruptionBudget for high availability
- [ ] (Optional) Grafana dashboard JSON for observability

### 7. Keycloak Configuration

- [ ] Create client for the backend service (e.g., `tracking-backend`)
- [ ] Configure client credentials for service account (M2M auth)
- [ ] Ensure audience mapper is configured

### 8. Database

- [ ] Create PostgreSQL database for the service
- [ ] Run EF Core migrations on first deployment
- [ ] Configure connection string in K8s deployment env vars

## Critical Consistency Rules

These identifiers MUST match across all systems:

| Identifier | Where Used |
|-----------|-----------|
| App ID (e.g., `tracking`) | `apps` array in navbar-mf, root page in app, `name` in identity-management JSON, `LicensedApps` in tenant settings |
| Role prefix (e.g., `tracking`) | `requiredRolePrefix` in navbar/root page, `prefix` in identity-management JSON, Keycloak role names |
| Backend audience (e.g., `tracking-backend`) | Keycloak client ID, `Authentication.Keycloak.Audience` in appsettings |
| Service account client ID | Keycloak client, `ServiceAccount.ClientId` in appsettings, K8s secret |

## Verification Steps

After completing all steps:

1. Deploy identity-management - verify `AppPermissionSyncHostedService` creates the app in DB
2. License a tenant for the new app via API or DB
3. Assign a user to the app with a role
4. Verify the app appears in the navbar app switcher
5. Verify the app appears on the root dashboard page
6. Verify the microfrontend loads at its URL path
7. Verify the backend API is accessible via ingress
8. Verify Prometheus metrics are being scraped
9. Verify logs appear in Loki/Grafana
