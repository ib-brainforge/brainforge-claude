# Technology Stack

<!--
This file is referenced by: design-pattern-advisor, validators, feature-planner
Last verified: January 2025
-->

## Frontend

The frontend uses a microfrontend architecture. Each application (App, HR, Asset, Identity, Inventory, DriveCOM, LMS, Common) is developed, built, and deployed independently as a separate Kubernetes deployment. Routing is handled via URL path prefixes through the API Gateway (e.g., /hr routes to hr-mf, /asset routes to asset-mf). Module Federation enables runtime sharing of components and packages between applications.

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI framework |
| TypeScript | ~5.7.3 | Type safety |
| Modern.js | 2.68.x | Meta-framework providing build tooling, routing, and SSR capabilities |
| Rspack | (via Modern.js) | Bundler (faster alternative to Webpack) |
| Module Federation | @module-federation/enhanced 0.21.x | Microfrontend composition enabling runtime sharing of components |
| Jotai | 2.13.1 | Atomic state management |
| TanStack React Query | 5.89.x | Server state management and data fetching |
| TanStack React Table | 8.21.x | Headless table utilities |
| TanStack React Form | 1.23.x | Form handling with validation |
| Zod | 3.x | Runtime schema validation |
| @brainforgeau/components | (internal) | Primary UI component library (ALWAYS use this over HeroUI) |
| HeroUI | 2.8.2 | Base UI components (wrapped by @brainforgeau/components) |
| Tailwind CSS | 4.1.x | Utility-first CSS framework |
| Framer Motion | 12.23.x | Animation library |
| react-oidc-context | 3.3.0 | OIDC/OAuth authentication client |
| SignalR | @microsoft/signalr 8.0.x | Real-time WebSocket communication |
| urql | 5.x | GraphQL client (used in HR module) |
| Apollo Client | 4.x | GraphQL client (used in HR module) |

### Frontend Shared Packages (@brainforgeau/*)

Published to internal NPM registry. Used across all microfrontend applications.

| Package | Purpose |
|---------|---------|
| @brainforgeau/security | Authentication context, permission guards, OIDC integration, context token management |
| @brainforgeau/components | **Primary UI library** - Extended components following JIRA design language (buttons, forms, tables, modals, icons) |
| @brainforgeau/theme | Tailwind CSS theme configuration with HeroUI integration |
| @brainforgeau/observability | Frontend OpenTelemetry instrumentation for tracing and web vitals |
| @brainforgeau/federation-types | TypeScript type generation for Module Federation remotes |
| @brainforgeau/tailwind-config | Shared Tailwind configuration extending HeroUI theme |

**Component Library Priority:** ALWAYS use @brainforgeau/components over raw HeroUI. The components follow JIRA design language with consistent styling. Components use "Base" prefix naming (BaseButton, BaseInput, BaseModal, etc.).

### Generated API Clients (@brainforgeau/*-client)

Auto-generated TypeScript clients from backend OpenAPI specifications.

| Package | Backend Service |
|---------|-----------------|
| @brainforgeau/hr-backend-client | HR Backend API |
| @brainforgeau/asset-backend-client | Asset Management API |
| @brainforgeau/identity-management-client | Identity Management API |
| @brainforgeau/learning-backend-client | Learning Management API |

---

## Backend

All backend services follow Clean Architecture with CQRS pattern. Services are containerized and deployed to Kubernetes.

| Technology | Version | Purpose |
|------------|---------|---------|
| .NET | 10.0 | Runtime |
| ASP.NET Core | 10.0 | Web framework |
| Entity Framework Core | 10.0 | ORM with code-first migrations |
| Npgsql.EntityFrameworkCore.PostgreSQL | 10.0 | PostgreSQL provider for EF Core |
| MediatR | 11.1.0 | In-process messaging for CQRS pattern |
| FluentValidation | 12.0.0 | Declarative request validation |
| Serilog | 8.0.3 | Structured logging with Loki sink |
| OpenTelemetry | 1.13.x | Distributed tracing and metrics |
| StackExchange.Redis | 2.8.x | Redis client for caching and pub/sub |
| Keycloak.Net.Core | 1.0.38 | Keycloak admin API client |
| OneOf | 3.0.271 | Discriminated unions for Result pattern |
| Swashbuckle | 10.0.1 | OpenAPI/Swagger documentation |
| NSwag | 14.2.0 | TypeScript client generation from OpenAPI |
| MongoDB.EntityFrameworkCore | 9.x | MongoDB provider (notification service) |
| Microsoft.Extensions.Caching.Hybrid | 10.0.0 | Two-tier hybrid caching (L1 memory + L2 Redis) |

### Backend Shared Packages (Services.Core.*)

Published to internal NuGet feed. Provide common functionality across all services.

| Package | Purpose |
|---------|---------|
| Services.Core.Abstractions | Base interfaces, entity types, result patterns, common contracts |
| Services.Core | Request context, validation pipeline, utility extensions |
| Services.Core.EntityFrameworkCore | EF Core base DbContext, tenant query filters, audit fields |
| Services.Core.Auth.Keycloak | JWT Bearer authentication middleware for Keycloak tokens |
| Services.Core.TenantAuth | Context token validation, multi-tenant authorization |
| Services.Core.TenantAuth.Abstractions | Tenant auth interfaces and contracts |
| Services.Core.TenantAuth.Redis | Redis-backed context token caching |
| Services.Core.Caching | Hybrid caching abstraction (L1 memory + L2 distributed) |
| Services.Core.Caching.Abstractions | Caching interfaces |
| Services.Core.Caching.EntityFramework | EF Core query result caching |
| Services.Core.Eventing.Redis | Domain events via Redis pub/sub |
| Services.Core.Eventing.Abstractions | Event interfaces |
| Services.Core.Eventing.Contracts | Shared event type definitions |
| Services.Core.Http | HTTP middleware, context extraction, correlation ID propagation |
| Services.Core.Observability | OpenTelemetry configuration, trace enrichment |

---

## Infrastructure

GitOps-managed Kubernetes infrastructure using Flux CD.

| Technology | Version | Purpose |
|------------|---------|---------|
| Kubernetes | 1.27+ | Container orchestration |
| Flux CD | 2.x | GitOps continuous delivery |
| Envoy Gateway | 1.2.x | Kubernetes Gateway API implementation |
| Kustomize | (bundled with Flux) | YAML configuration management |
| Helm | 3.x | Kubernetes package management |
| Docker | 24.x | Container runtime |
| SOPS + Age | (current) | Secret encryption for GitOps |
| Cilium | (optional) | Advanced CNI with L7 policies and WireGuard encryption |

### Observability Stack

Deployed via kube-prometheus-stack Helm chart with additional Grafana components.

| Technology | Purpose |
|------------|---------|
| Prometheus | Metrics collection and alerting rules |
| Grafana | Dashboards and visualization with Keycloak SSO |
| Loki | Log aggregation with multi-tenant support |
| Tempo | Distributed trace storage with service map |
| Blackbox Exporter | HTTP/HTTPS endpoint probing |
| Pushgateway | E2E test metrics ingestion |

### Security Stack

| Technology | Purpose |
|------------|---------|
| Kyverno | Kubernetes policy enforcement |
| Trivy Operator | Continuous container vulnerability scanning |
| CrowdSec | Collaborative threat intelligence and blocking |
| SafeLine | Web application firewall |
| cert-manager | Automated TLS certificate provisioning |
| Reloader | Auto-restart pods on secret/configmap changes |

---

## Databases

| Database | Purpose | Notes |
|----------|---------|-------|
| PostgreSQL 15+ | Primary RDBMS for all services | Each service has dedicated database |
| Redis | Distributed caching, pub/sub for domain events, context token storage | Used by Services.Core.Caching and Services.Core.Eventing |
| RabbitMQ | Message queue for async operations | Future use for event-driven workflows |
| MongoDB | Document store for notifications | Used by notification-backend |

---

## External Services

| Service | Purpose |
|---------|---------|
| Keycloak | Identity Provider (OIDC) with multi-tenant realm support |
| Azure Blob Storage | Backup storage for NFS volumes |
| NFS Server | Shared file storage for user uploads and documents |

---

## Development Tools

| Tool | Purpose |
|------|---------|
| pnpm 8+ | Frontend monorepo package manager |
| Node.js 20+ | JavaScript runtime |
| .NET SDK 10.0 | Backend development |
| Biome | Frontend linting and formatting (replacing ESLint in some projects) |
| Prettier | Code formatting with Tailwind plugin |
| Playwright | End-to-end testing |
| xUnit | Backend unit and integration testing |
| Allure | Test reporting |

---

## Version Compatibility

### Required Versions

| Component | Minimum Version |
|-----------|-----------------|
| Node.js | 18.18.0+ (20.x LTS recommended) |
| .NET SDK | 10.0.x |
| pnpm | 8.x |
| Docker | 24.x |
| Kubernetes | 1.27+ |

### Frontend Configuration

- ES Module type enabled in package.json
- TypeScript strict mode
- Path aliases configured in tsconfig

### Backend Configuration

- Nullable reference types enabled
- File-scoped namespaces
- Primary constructors (C# 12+)
- Records for DTOs and Commands/Queries

---

## File Naming Conventions

### Frontend

- **Components**: PascalCase (UserCard.tsx, AssetList.tsx)
- **Hooks**: camelCase with use prefix (useAssets.ts, usePermissions.ts)
- **Atoms**: camelCase with Atom suffix (assetsAtom.ts, filtersAtom.ts)
- **Utilities**: camelCase (formatDate.ts, parseError.ts)
- **Routes**: lowercase with dashes (asset-types/page.tsx)

### Backend

- **Classes**: PascalCase (CreateAssetCommand.cs)
- **Interfaces**: PascalCase with I prefix (IAssetRepository.cs)
- **Folders**: PascalCase, feature-based structure
- **Namespaces**: Match folder structure

---

## Code Style

### Frontend

- Biome or Prettier with Tailwind plugin
- Import sorting enabled
- Simple-git-hooks for pre-commit checks

### Backend

- .editorconfig for consistent formatting
- Roslyn analyzers for code quality
- Documentation generation enabled
- NoWarn configured for documentation coverage

---

## References

- Frontend patterns: mf-packages/README.md
- Backend patterns: dotnet-core/README.md
- Infrastructure setup: infra/docs/
- Confluence technical docs: docs/confluence/EAHT/netcorp360/technical-overview/
