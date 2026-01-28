# Validation Configuration

<!--
PROJECT-SPECIFIC: Configuration for architecture validation.
This is referenced by: validation-orchestrator
Last verified: 2026-01-27
Source: Verified against all repositories in bf-github and docs/confluence/
-->

## Validation Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| quick | Structure only | Pre-commit hook |
| standard | + patterns, security | PR validation |
| thorough | + cross-service, ADR | Release validation |

## Scope Configuration

| Scope | What's Validated |
|-------|------------------|
| all | All discovered services |
| changed | Services with git changes |
| service | Single named service |

## Validators by Level

### Quick

- Project structure validation (Clean Architecture layers)
- Dependency check (NuGet/npm versions)
- File naming conventions

### Standard (includes Quick)

- CQRS pattern compliance (Commands/Queries structure)
- Security basics (auth middleware, attribute usage)
- Core package usage (Services.Core.*, @brainforgeau/* packages)
- Multi-tenancy enforcement (TenantEntity inheritance)

### Thorough (includes Standard)

- Cross-service dependencies
- ADR compliance
- Full security audit (secrets, injection risks)
- Authentication flow compliance (two-token pattern)

## Severity Configuration

| Severity | Blocks PR | Blocks Release |
|----------|-----------|----------------|
| error | Yes | Yes |
| warning | No | Yes |
| info | No | No |

---

## Backend Services to Validate

All backend services follow Clean Architecture with .NET 10.0.

| Service | Repository | Project Prefix |
|---------|------------|----------------|
| Asset Backend | asset-backend | AssetManagement |
| HR Backend | hr-backend | Brainforge |
| Inventory Backend | inventory-backend | Inventory |
| Identity Management | identity-management | IdentityManagement |
| LMS Backend | lms-backend | LearningManagement |
| Onboard Backend | onboard-backend | OnboardManagement |
| Notification Backend | notification-backend | Notification |
| Common Backend | common-backend | Common |

Note: Compliance and Payroll backends are planned but not yet created.

---

## Frontend Services to Validate

All microfrontends use React 18 with Modern.js and Module Federation.

| Service | Repository | Port | Status |
|---------|------------|------|--------|
| HR MF | hr-mf | 8081 | Active |
| Asset MF | asset-mf | 8082 | Active |
| Identity MF | identity-mf | 8090 | Active |
| Inventory MF | inventory-mf | - | Active |
| LMS MF | lms-mf | - | Active |
| Navbar MF | navbar-mf | 3001 | Active (Provider) |
| DriveCom MF | drivecom-mf | - | Active |
| Onboard MF | onboard-mf | - | Active |
| Common MF | common-mf | - | Active |

Note: Navbar MF uses Webpack directly instead of Modern.js due to specific build requirements.

---

## Shared Packages to Validate

### Backend (NuGet - dotnet-core)

| Package | Purpose |
|---------|---------|
| Services.Core.Abstractions | Base entities, interfaces, ApiResult |
| Services.Core | MediatR pipeline, FluentValidation integration |
| Services.Core.EntityFrameworkCore | BaseDbContext, interceptors, filters |
| Services.Core.TenantAuth | Context token middleware |
| Services.Core.TenantAuth.Abstractions | TenantAuth interfaces |
| Services.Core.TenantAuth.Redis | Redis-backed token caching |
| Services.Core.Auth.Keycloak | Keycloak JWT authentication |
| Services.Core.Observability | OpenTelemetry integration |
| Services.Core.Caching | Distributed caching (Redis) |
| Services.Core.Http | HTTP context middleware |
| Services.Core.Eventing.Redis | Redis event bus |

### Frontend (NPM - mf-packages)

| Package | Purpose |
|---------|---------|
| @brainforgeau/security | Authentication context, authorized axios |
| @brainforgeau/components | Extended HeroUI component library |
| @brainforgeau/theme | Tailwind CSS theme configuration |
| @brainforgeau/observability | Frontend logging, tracing, metrics |
| @brainforgeau/federation-types | Module Federation type definitions (internal) |

---

## Service ID Registry

Service IDs for inter-service communication. Coordinate before assigning new IDs.

| Service | Service ID |
|---------|------------|
| identity-management | 00000000-0000-0000-0000-000000000001 |
| hr-backend | 00000000-0000-0000-0000-000000000002 |
| lms-backend | 00000000-0000-0000-0000-000000000003 |
| inventory-backend | 00000000-0000-0000-0000-000000000004 |
| onboard-backend | 00000000-0000-0000-0000-000000000005 |
| asset-backend | 00000000-0000-0000-0000-000000000010 |

Source: docs/confluence/netcorp-backbone-architecture.md

---

## HTTP Status Code Validation

Authentication-related HTTP status codes that validation checks for correct handling.

| Status | Name | Meaning | Expected Action |
|--------|------|---------|-----------------|
| 401 | Unauthorized | Access token invalid/expired | Refresh access token |
| 403 | Forbidden | Permission denied | Show error, NO token refresh |
| 419 | Authentication Timeout | Context token invalid/expired | Refresh context token and retry |
| 429 | Too Many Requests | Rate limited | Exponential backoff |

Note: 419 is used instead of 403 for context token issues to prevent infinite refresh loops.

---

## Excluded Paths

Paths skipped during validation.

### General Exclusions

- node_modules/
- bin/
- obj/
- .git/
- dist/
- build/
- Migrations/

### File Pattern Exclusions

- *.generated.cs
- *.d.ts

### TenantAuth Bypass Endpoints

These endpoints bypass context token validation.

- .well-known/* - OpenID Connect discovery
- swagger/* - API documentation
- metrics - Prometheus metrics
- health, livez - Health checks
- contexts/available, contexts/issue - Context token flow
- tenants/resolve - Tenant resolution for custom domains

---

## Custom Validation Rules

### Backend Rules

**Architecture Rules**

| Rule | Check | Path | Severity |
|------|-------|------|----------|
| TenantEntity inheritance | All domain entities inherit from TenantEntity | Domain/**/*.cs | error |
| MediatR usage | Controllers dispatch via mediator.Send() | Controllers/**/*.cs | error |
| FluentValidation | Commands have corresponding validators | Commands/**/*Command.cs | warning |
| Clean Architecture | Correct layer dependencies | All projects | error |

**CQRS Rules**

| Rule | Check | Severity |
|------|-------|----------|
| Command/Query records | Use IRequest<ApiResult<T>> pattern | error |
| Handler return type | Return ApiResult, not throwing exceptions | warning |
| Constructor injection | No service locator pattern | error |

**Security Rules**

| Rule | Check | Severity |
|------|-------|----------|
| Auth attribute | All controllers declare Authorize or AllowAnonymous | error |
| No hardcoded secrets | No password=, apikey=, secret= in code | error |
| Parameterized queries | No FromSqlRaw with string interpolation | error |
| HTTPS enforcement | RequireHttpsMetadata = true in production | error |

### Frontend Rules

**UI Component Rules (CRITICAL - JIRA Design Language)**

| Rule | Check | Path | Severity |
|------|-------|------|----------|
| Use BaseButton | No direct @heroui/react Button imports | src/**/*.tsx | error |
| Use BaseInput | No direct @heroui/react Input imports | src/**/*.tsx | error |
| Use BaseSelect | No direct @heroui/react Select imports | src/**/*.tsx | error |
| Use BaseModal | No direct @heroui/react Modal imports | src/**/*.tsx | error |
| Use BaseCheckbox | No direct @heroui/react Checkbox imports | src/**/*.tsx | error |
| Use BaseTable | No custom table implementations | src/**/*.tsx | warning |
| @brainforgeau/components | Primary UI library for all components | src/**/*.tsx | error |

**Allowed Direct HeroUI Usage:**
- addToast (notification utility)
- Alert (inline alerts)
- HeroUIProvider, ToastProvider (providers)
- Popover (when BaseSelect does not fit)

**API Rules**

| Rule | Check | Path | Severity |
|------|-------|------|----------|
| Authorized axios | Use authorizedAxios from @brainforgeau/security | src/**/*.ts | error |
| No direct fetch | No raw fetch() or axios() calls | src/**/*.ts | error |
| No hardcoded URLs | API URLs from environment variables | src/**/*.ts | warning |

**State Rules**

| Rule | Check | Severity |
|------|-------|----------|
| Jotai for client state | Use Jotai atoms for cross-component state | warning |
| TanStack Query for server state | No useState for server data | warning |
| Context token sync | Handle CONTEXT_TOKEN_CHANGED_EVENT | error |

**Security Rules**

| Rule | Check | Severity |
|------|-------|----------|
| No localStorage for tokens | Use sessionStorage only | error |
| No hardcoded API keys | Use environment variables | error |
| No eval() usage | Never use eval | error |
| Sanitize HTML | Use proper sanitization with dangerouslySetInnerHTML | warning |

---

## Middleware Order Validation

Backend services must configure middleware in this exact order.

| Order | Middleware | Purpose |
|-------|------------|---------|
| 1 | UseHttpContext() | Extract RequestId, SourceIp, CorrelationId |
| 2 | UseAuthentication() | Keycloak JWT validation |
| 3 | UseTenantAuth() | Context token validation |
| 4 | UseSerilogContextEnrichment() | Log enrichment |
| 5 | UseOpenTelemetryPrometheusScrapingEndpoint() | Metrics |
| 6 | UseAuthorization() | Authorization enforcement |
| 7 | MapControllers() | Route to controllers |

---

## Module Federation Validation

Microfrontends must share these packages as singletons.

| Package | Singleton | Eager | Strict Version |
|---------|-----------|-------|----------------|
| react | Yes | Yes | Yes (18.3.1) |
| react-dom | Yes | Yes | Yes (18.3.1) |
| @brainforgeau/security | Yes | Yes | No |
| jotai | Yes | No | No |
| @heroui/react | Yes | No | No |
| framer-motion | Yes | No | No |

Note: @brainforgeau/components is NOT shared due to Webpack/Rspack SVG transformation incompatibilities.

---

## Cross-Reference

Detailed validation patterns are documented in:
- [backend-patterns.md](backend-patterns.md) - .NET validation rules
- [frontend-patterns.md](frontend-patterns.md) - React validation rules
- [security-standards.md](security-standards.md) - Authentication and authorization validation
