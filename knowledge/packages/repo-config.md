# Repository Configuration

This file contains repository structure and configuration for the bf-github monorepo.
Referenced by: commit-manager, validation agents

---

## Repository Types

The monorepo contains individual repositories, each with its own .git folder. All repositories are hosted under the GitHub organization.

### Frontend Microfrontends

Microfrontends use Modern.js with Rspack and Module Federation for runtime composition.

| Repository | Description |
|------------|-------------|
| hr-mf | Human Resources microfrontend for employee and payroll management |
| asset-mf | Asset Management microfrontend for tracking company assets and maintenance |
| identity-mf | Identity Management microfrontend for authentication flows, tenant selection, and permission management |
| inventory-mf | Inventory microfrontend for product catalog, warehouses, and stock management |
| drivecom-mf | Driver Communication microfrontend |
| lms-mf | Learning Management System microfrontend for courses, enrollments, and training |
| common-mf | Common shared microfrontend providing cross-cutting components and notifications |
| navbar-mf | Shared navigation bar component exposed as Module Federation remote, uses Webpack instead of Modern.js |
| onboard-mf | Employee onboarding microfrontend for onboarding workflows |

### Frontend Applications

| Repository | Description |
|------------|-------------|
| app | Main shell application that hosts all microfrontends, serves as the Module Federation host |
| onboard-app | Standalone onboarding application |
| public-website | Public marketing website built with Modern.js |
| netcorp-public-website | NetCorp public website using WordPress with Advanced Custom Fields |

### Content Management

| Repository | Description |
|------------|-------------|
| public-website-strapi | Strapi CMS workspace with separate apps for API and frontend |

### Backend Services

All backend services follow Clean Architecture with Domain, Application, Infrastructure, and Api layers.

| Repository | Description | Solution Prefix |
|------------|-------------|-----------------|
| hr-backend | HR service managing employees, departments, positions, payroll, and scheduling | Brainforge |
| asset-backend | Asset Management service for assets, maintenance, fuel, documents, and telemetry | AssetManagement |
| identity-management | Identity and Authorization service managing users, tenants, organizations, divisions, permissions, and API keys | IdentityManagement |
| inventory-backend | Inventory service for products, warehouses, suppliers, and stock transactions | Inventory |
| lms-backend | Learning Management service for courses, enrollments, quizzes, and approvals | LearningManagement |
| notification-backend | Notification service for real-time notifications via SignalR and subscription management | Notification |
| common-backend | Common shared backend service for cross-cutting entities like contacts | Common |
| onboard-backend | Onboarding backend service for managing onboarding workflows | OnboardManagement |

### Core Libraries

| Repository | Description |
|------------|-------------|
| dotnet-core | Shared .NET packages providing infrastructure building blocks for all backend services |
| mf-packages | Shared frontend packages published to npm registry for all microfrontends |

### Infrastructure

| Repository | Description |
|------------|-------------|
| infra | Infrastructure as code with Kubernetes manifests, Flux GitOps configuration, SOPS for secrets, and Terraform |
| api-gateway | API Gateway service for routing, rate limiting, and API key validation |
| aspire | .NET Aspire orchestration with AppHost and ServiceDefaults projects for local development |
| auth | Authentication configuration and Keycloak integration |

### Documentation

| Repository | Description |
|------------|-------------|
| docs | Central documentation repository with Confluence exports and technical documentation |

---

## Microfrontend Ports

Development server ports configured in modern.config.ts or webpack.config.ts files.

| Microfrontend | Port | Build Tool |
|---------------|------|------------|
| app | 8080 | Modern.js + Rspack |
| hr-mf | 8081 | Modern.js + Rspack |
| asset-mf | 8082 | Modern.js + Rspack |
| drivecom-mf | 8083 | Modern.js + Rspack |
| common-mf | 8084 | Modern.js + Rspack |
| inventory-mf | 8084 | Modern.js + Rspack |
| lms-mf | 8085 | Modern.js + Rspack |
| onboard-mf | 8085 | Modern.js + Rspack |
| identity-mf | 8090 | Modern.js + Rspack |
| navbar-mf | 3001 | Webpack |

Note: common-mf and inventory-mf share port 8084; lms-mf and onboard-mf share port 8085. Adjust one port when running both locally.

---

## Commit Conventions

The project follows Conventional Commits format.

### Commit Message Format

Type, optional scope in parentheses, colon, subject line. Optional body and footer sections.

### Commit Types

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| chore | Maintenance tasks |
| refactor | Code restructuring without behavior change |
| docs | Documentation changes |
| test | Test additions or modifications |
| style | Formatting changes |
| perf | Performance improvements |
| ci | CI/CD configuration changes |

### Repository to Scope Mapping

| Repository | Commit Scope |
|------------|--------------|
| hr-mf | hr |
| asset-mf | asset |
| identity-mf | identity |
| inventory-mf | inventory |
| drivecom-mf | drivecom |
| lms-mf | lms |
| common-mf | common |
| navbar-mf | navbar |
| onboard-mf | onboard |
| onboard-app | onboard |
| app | app |
| public-website | website |
| netcorp-public-website | website |
| public-website-strapi | cms |
| hr-backend | hr-api |
| asset-backend | asset-api |
| identity-management | identity-api |
| inventory-backend | inventory-api |
| lms-backend | lms-api |
| notification-backend | notification-api |
| common-backend | common-api |
| onboard-backend | onboard-api |
| dotnet-core | core |
| mf-packages | packages |
| api-gateway | gateway |
| infra | infra |
| aspire | aspire |
| auth | auth |

### Ticket Reference

The project uses EAHT ticket prefix pattern (e.g., EAHT-123). Tickets are optional for most commits but recommended for traceability.

---

## Service Dependencies

### Frontend to Backend via Generated API Clients

Each frontend microfrontend uses generated TypeScript clients (NSwag) to communicate with backend services.

| Frontend | API Client Packages |
|----------|---------------------|
| hr-mf | hr-backend-client, identity-management-client, learning-backend-client |
| asset-mf | asset-backend-client, identity-management-client |
| identity-mf | identity-management-client, hr-backend-client |
| inventory-mf | inventory-backend-client, identity-management-client |
| lms-mf | learning-backend-client, identity-management-client |
| onboard-mf | onboard-backend-client, identity-management-client |
| common-mf | identity-management-client |
| drivecom-mf | identity-management-client |
| navbar-mf | identity-management-client |
| app | identity-management-client |

All API clients are published under the @brainforgeau npm scope.

### Backend to Core Packages

All backend services reference shared packages from the dotnet-core repository.

| Package | Purpose |
|---------|---------|
| Services.Core | Main core library with common utilities |
| Services.Core.Abstractions | Interface contracts including IAppContext, ITenantEntity, ITrackedEntity |
| Services.Core.Auth.Keycloak | Keycloak JWT authentication with multi-realm support |
| Services.Core.TenantAuth | TenantAuthMiddleware for context token validation |
| Services.Core.TenantAuth.Abstractions | Tenant authentication interface contracts |
| Services.Core.TenantAuth.Redis | Redis-based tenant token caching |
| Services.Core.EntityFrameworkCore | BaseDbContext, global query filters, AuditStampingInterceptor |
| Services.Core.Caching | Distributed caching implementation |
| Services.Core.Caching.Abstractions | Caching interface contracts |
| Services.Core.Eventing.Abstractions | Event publishing interface contracts |
| Services.Core.Eventing.Contracts | Integration event definitions |
| Services.Core.Eventing.Redis | Redis Streams event publishing and consumption |
| Services.Core.Observability | Logging, distributed tracing, and metrics |
| Services.Core.Http | HTTP utilities including ServiceAccountTokenHandler |

### Frontend to Shared Packages

All frontend microfrontends depend on packages from the mf-packages repository.

| Package | Purpose |
|---------|---------|
| @brainforgeau/security | Auth context provider, authorized axios, context token management, OIDC integration. Exposed as Module Federation singleton |
| @brainforgeau/components | UI component library including buttons, forms, tables, modals, icons, charts, navigation |
| @brainforgeau/theme | Tailwind CSS theme configuration and CSS custom properties |
| @brainforgeau/observability | Frontend logging, distributed tracing via OpenTelemetry, and web vitals metrics |
| @brainforgeau/federation-types | Module Federation type definitions |
| @brainforgeau/tailwind-config | Shared Tailwind CSS configuration preset |

---

## Service ID Registry

Each backend service has a registered identifier for cross-service communication and permission scoping. The canonical registry is maintained in docs/confluence/netcorp-backbone-architecture.md.

| Service | Service ID |
|---------|-----------|
| identity-management | 00000000-0000-0000-0000-000000000001 |
| hr-backend | 00000000-0000-0000-0000-000000000002 |
| lms-backend | 00000000-0000-0000-0000-000000000003 |
| inventory-backend | 00000000-0000-0000-0000-000000000004 |
| onboard-backend | 00000000-0000-0000-0000-000000000005 |
| asset-backend | 00000000-0000-0000-0000-000000000010 |

**Important:** Coordinate with the team before assigning a new Service ID to avoid conflicts.

---

## Source Control

| Property | Value |
|----------|-------|
| Provider | GitHub |
| Organization | brainforgeau |
| Repository Structure | Multi-repo within shared parent directory |
| Each Repository | Has individual .git folder |

---

## References

- Architecture overview: docs/confluence/netcorp-backbone-architecture.md
- Service boundaries: .claude/knowledge/architecture/service-boundaries.md
- Commit conventions: .claude/knowledge/commit-conventions.md
