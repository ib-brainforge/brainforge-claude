# Package Configuration

Configuration reference for NPM and NuGet package management.
Referenced by: package-release skill, npm/nuget package managers.

---

## NPM Package Registry

The organization publishes frontend packages under the @brainforgeau scope to GitHub Packages.

### Registry Details

- Scope: @brainforgeau
- Package Manager: pnpm
- Registry: GitHub Packages (npm.pkg.github.com/@brainforgeau)
- Organization: brainforgeau

---

## Core Frontend Packages

Shared packages located in mf-packages/packages directory.

### @brainforgeau/security

Authentication and authorization utilities for microfrontends. Provides authorized axios client that automatically attaches Keycloak JWT and Context Token to requests. Contains authentication context provider and auth state management using Jotai atoms.

Peer dependencies: react, react-dom, jotai, react-oidc-context, @brainforgeau/identity-management-client

### @brainforgeau/components

UI component library built on HeroUI. Provides reusable components including forms, tables, modals, navigation, inputs, date pickers, charts, and autocomplete. Uses Tailwind CSS for styling with tailwind-merge and tailwind-variants.

Export paths include: icons, form, accordion, table, alert, navbar, button, subscriptions, base, charts, select, input, autocomplete, date-picker, time-input, breadcrumbs, sidenav, modal, utils

Peer dependencies: react, react-dom, @heroui/react, @heroicons/react, @tanstack/react-table, framer-motion, jotai, @microsoft/signalr, react-error-boundary

### @brainforgeau/theme

Tailwind CSS theme package providing consistent styling across microfrontends. Contains theme CSS configuration for HeroUI integration.

Peer dependencies: react, react-dom, @heroui/react, tailwindcss

### @brainforgeau/observability

Frontend observability package for centralized logging, tracing, and metrics. Built on OpenTelemetry for distributed tracing and web-vitals for performance metrics.

Key dependencies: @opentelemetry/api, @opentelemetry/sdk-trace-web, @opentelemetry/instrumentation-fetch, @opentelemetry/exporter-trace-otlp-http, web-vitals

Peer dependencies: react, react-dom

### @brainforgeau/federation-types

Internal package for Module Federation type definitions. Used for TypeScript types generation in microfrontend architecture. Not published to registry.

### @brainforgeau/tailwind-config

Internal shared Tailwind CSS configuration. Integrates with HeroUI theme. Not published to registry.

Peer dependencies: tailwindcss

---

## Generated API Clients

Auto-generated TypeScript clients from backend OpenAPI specifications. Published under @brainforgeau scope.

| Package | Source Backend |
|---------|----------------|
| @brainforgeau/identity-management-client | identity-management |
| @brainforgeau/hr-backend-client | hr-backend |
| @brainforgeau/asset-backend-client | asset-backend |
| @brainforgeau/learning-backend-client | lms-backend |
| @brainforgeau/inventory-backend-client | inventory-backend |
| @brainforgeau/onboard-backend-client | onboard-backend |

All microfrontends depend on @brainforgeau/identity-management-client for user and context operations.

---

## NuGet Packages

Backend packages published to GitHub Packages NuGet feed.

### Package Prefix and Target

- Prefix: Services.Core
- Target Framework: net10.0
- Repository: bf-github monorepo (dotnet-core directory)

### Core Packages

**Services.Core.Abstractions**
- Interfaces, base entities, and shared abstractions
- Foundation package referenced by all other packages
- Depends on: OneOf

**Services.Core**
- Core utilities and business logic helpers
- Contains MediatR pipeline behaviors and FluentValidation integration
- Depends on: Services.Core.Abstractions, MediatR, FluentValidation

**Services.Core.EntityFrameworkCore**
- Entity Framework Core extensions for multi-tenant filtering
- DbContext interceptors and query filters
- Depends on: Services.Core.Abstractions, Microsoft.EntityFrameworkCore

**Services.Core.TenantAuth**
- Context token middleware for multi-tenant authentication
- JWT bearer authentication with Keycloak integration
- Depends on: Services.Core.Abstractions, Services.Core, Services.Core.TenantAuth.Abstractions, Services.Core.Auth.Keycloak

**Services.Core.TenantAuth.Abstractions**
- Authentication abstraction interfaces
- Depends on: Services.Core.Abstractions

**Services.Core.TenantAuth.Redis**
- Redis-based token caching implementation
- Depends on: Services.Core.TenantAuth.Abstractions, StackExchange.Redis

**Services.Core.Auth.Keycloak**
- Keycloak JWT integration and validation
- Depends on: Services.Core.Abstractions, Microsoft.AspNetCore.Authentication.JwtBearer

**Services.Core.Observability**
- OpenTelemetry integration for tracing, metrics, and logging
- Includes ASP.NET Core, HTTP, Entity Framework Core, and runtime instrumentation
- Prometheus metrics exporter
- Depends on: Services.Core.Abstractions, OpenTelemetry packages

**Services.Core.Caching**
- Caching implementation with hybrid cache support
- MediatR integration for cache invalidation
- Depends on: Services.Core.Abstractions, Services.Core.Caching.Abstractions, Microsoft.Extensions.Caching.Hybrid

**Services.Core.Caching.Abstractions**
- Caching interfaces and contracts
- Depends on: Services.Core.Abstractions

**Services.Core.Caching.EntityFramework**
- Entity Framework Core caching extensions
- Standalone package with no additional dependencies

**Services.Core.Http**
- HTTP client utilities and extensions
- Depends on: Services.Core.Abstractions

**Services.Core.Eventing.Abstractions**
- Event abstraction interfaces for pub/sub patterns
- Standalone package with no dependencies

**Services.Core.Eventing.Contracts**
- Shared event contracts and definitions
- Depends on: Services.Core.Eventing.Abstractions

**Services.Core.Eventing.Redis**
- Redis-based event transport implementation
- OpenTelemetry tracing integration
- Depends on: Services.Core.Eventing.Abstractions, StackExchange.Redis, OpenTelemetry.Api

---

## Technology Stack Versions (Verified)

### Frontend

| Technology | Version |
|------------|---------|
| Node.js | >=18.18.0 |
| React | 18.3.1 |
| react-dom | 18.3.1 |
| TypeScript | ~5.7.3 |
| Modern.js (@modern-js/runtime) | ^2.68.9 |
| Module Federation (@module-federation/enhanced) | ^0.21.4 |
| HeroUI (@heroui/react) | 2.8.2 |
| Tailwind CSS | 4.1.13 |
| Jotai | 2.13.1 |
| TanStack React Query | ^5.89.0 |
| TanStack React Form | ^1.23.0 |
| TanStack React Table | ^8.21.3 |
| urql | ^5.0.1 |
| framer-motion | 12.23.12 |
| react-oidc-context | 3.3.0 |
| SignalR (@microsoft/signalr) | ^8.0.0 |
| zod | ^3.25.76 |
| Biome | 1.9.4 |
| Playwright | ^1.49.0 |

### Backend

| Technology | Version |
|------------|---------|
| .NET SDK | 10 |
| Entity Framework Core | 10.0.0 |
| MediatR | 11.1.0 |
| FluentValidation | 12.0.0 |
| StackExchange.Redis | 2.8.41 |
| OpenTelemetry | 1.13.x |

---

## Module Federation Sharing Rules

### Required Singletons

These packages MUST be shared as singletons to ensure correct behavior across microfrontends.

**react and react-dom**
- Singleton: true
- Strict Version: true
- Eager: true
- Required Version: 18.3.1

**@brainforgeau/security**
- Singleton: true
- Eager: true
- Critical for authentication state sharing across module boundaries

### Recommended Singletons

**jotai**
- Singleton: true
- Ensures consistent atom state across modules

**@heroui/react**
- Singleton: true
- Prevents duplicate UI framework instances

**@heroicons/react**
- Singleton: true
- Reduces bundle duplication

**framer-motion**
- Singleton: true
- Required for consistent animation context

### Not Shared

**@brainforgeau/components**
- Each microfrontend bundles its own copy
- Reason: Webpack/Rspack SVG transformation incompatibilities prevent sharing

---

## Version Prefix Policy

| Prefix | Meaning | Auto-Update |
|--------|---------|-------------|
| ^ | Minor updates allowed | Yes |
| ~ | Patch updates only | Yes |
| (none) | Exact version pinned | No |
| * | Any version (peer deps) | Yes |

---

## Package Dependencies Flow

### Frontend Dependency Chain

All microfrontends depend on:
1. @brainforgeau/security (authentication)
2. @brainforgeau/components (UI)
3. @brainforgeau/theme (styling)
4. @brainforgeau/observability (monitoring)
5. @brainforgeau/identity-management-client (user context)

Domain-specific microfrontends add their respective backend client:
- hr-mf: @brainforgeau/hr-backend-client
- asset-mf: @brainforgeau/asset-backend-client
- lms-mf: @brainforgeau/learning-backend-client
- inventory-mf: @brainforgeau/inventory-backend-client
- onboard-mf: @brainforgeau/onboard-backend-client

### Backend Dependency Chain

Most packages build on Services.Core.Abstractions as the foundation:

Services.Core.TenantAuth references:
- Services.Core.Abstractions
- Services.Core.TenantAuth.Abstractions
- Services.Core
- Services.Core.Auth.Keycloak

Services.Core.Eventing.Contracts references:
- Services.Core.Eventing.Abstractions

Services.Core.Eventing.Redis references:
- Services.Core.Eventing.Abstractions

---

## Repository Configuration

- Organization: brainforgeau
- Monorepo: bf-github
- Frontend packages source: mf-packages/packages/
- Backend packages source: dotnet-core/

---

## Update Policy

| Change Type | Version Bump | Auto-Update |
|-------------|--------------|-------------|
| Bug fix | Patch (0.0.x) | Yes |
| New feature | Minor (0.x.0) | Yes (with ^) |
| Breaking change | Major (x.0.0) | No |

---

## Dependency Update Workflow

1. Core package changes committed to dotnet-core or mf-packages
2. CI/CD pipeline builds and publishes new version
3. package-release skill detects new version
4. Scans dependent services/apps for outdated references
5. Updates package references in package.json or .csproj files
6. Creates PRs with updated versions
7. CI runs tests on PRs
