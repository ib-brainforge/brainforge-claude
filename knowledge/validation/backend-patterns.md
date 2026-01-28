# Backend Validation Patterns

<!--
PROJECT-SPECIFIC: Backend validation patterns for BrainForge platform.
This is referenced by: backend-pattern-validator
Last verified: 2026-01-27
Source: Verified against asset-backend, hr-backend, inventory-backend, identity-management,
        lms-backend, onboard-backend, notification-backend, common-backend, dotnet-core repositories
        and Confluence documentation in docs/confluence/
-->

## Stack Detection

All BrainForge backend services use .NET 10.0:

| Stack | Detection File | File Extension |
|-------|----------------|----------------|
| .NET 10.0 | `*.csproj` or `*.sln` | `.cs` |

## API Style Detection

| Style | Grep Pattern | File Pattern |
|-------|--------------|--------------|
| REST | `[HttpGet]\|[HttpPost]\|[HttpPut]\|[HttpDelete]` | `**/*Controller.cs` |
| SignalR | `Microsoft.AspNetCore.SignalR\|Hub` | `**/*.cs` |

Note: GraphQL (HotChocolate) is NOT currently used in any backend service.

---

## Backend Services Overview

All backends follow Clean Architecture with Domain-Driven Design. Each service has:
- Api layer (HTTP endpoints, controllers)
- Application layer (CQRS handlers with MediatR)
- Domain layer (entities, value objects, domain events)
- Infrastructure layer (EF Core, external integrations)

### Service Naming Conventions

| Repository | Project Prefix | Description |
|------------|----------------|-------------|
| asset-backend | AssetManagement | Vehicle and equipment management |
| hr-backend | Brainforge | Employee and organizational management |
| inventory-backend | Inventory | Inventory and warehouse management |
| identity-management | IdentityManagement | Users, tenants, contexts, authentication |
| lms-backend | LearningManagement | Learning management system |
| onboard-backend | OnboardManagement | Employee onboarding workflows |
| notification-backend | Notification | Push notifications with SignalR |
| common-backend | Common | Shared common utilities |

---

## Clean Architecture Structure

All backends follow this layered structure:

| Layer | Purpose |
|-------|---------|
| {Prefix}.Api | ASP.NET Core REST API with Controllers, Middleware, Configuration |
| {Prefix}.Application | CQRS Commands/Queries organized by Aggregate |
| {Prefix}.Domain | Aggregates, Value Objects organized by Bounded Context |
| {Prefix}.Infrastructure | EF Core, External Services, Persistence |

### Domain-Driven Design Organization

Domain layers organize business logic into Bounded Contexts (modules):

| Folder | Purpose |
|--------|---------|
| {BoundedContext}/ | Entities and logic for specific domain area |
| SharedKernel/ | Cross-cutting domain concerns |
| ValueObjects/ | Immutable value types |
| Constants/ | Domain constants |
| Enums/ | Domain enumerations |

---

## CQRS Patterns (MediatR)

### Command and Query Definitions

Commands and queries are defined as records implementing IRequest with ApiResult wrapper:

| Check | Description |
|-------|-------------|
| Command definition | Record implementing IRequest<ApiResult<T>> |
| Query definition | Record implementing IRequest<ApiResult<T>> |
| Cacheable query | Query also implementing ICachedApiResultQuery |
| Command handler | Class implementing IRequestHandler<TCommand, ApiResult<T>> |
| Query handler | Class implementing IRequestHandler<TQuery, ApiResult<T>> |
| MediatR dispatch | Handler receives request via mediator.Send() |

### Command/Query Record Pattern

| Element | Pattern |
|---------|---------|
| Record keyword | Commands/queries are records (immutable) |
| Properties | Use init-only setters with get and init |
| Return type | Always IRequest<ApiResult<T>> |
| Cache interface | ICachedApiResultQuery for cacheable queries |
| Cache properties | CacheKey, CacheTags, CacheExpiration |

### Handler Pattern

| Element | Pattern |
|---------|---------|
| Constructor | Primary constructor injection with DbContext |
| Interface | IRequestHandler<TRequest, ApiResult<T>> |
| Method | async Task<ApiResult<T>> Handle(request, cancellationToken) |
| Returns | ApiResults.Success(), ApiResults.Conflict(), etc. |

---

## API Controller Patterns

| Check | Description |
|-------|-------------|
| Controller base | Inherit from BaseController(logger) |
| Route attribute | Route("v1/{resource}") versioned routes |
| ApiController | ApiController attribute required |
| HTTP methods | HttpGet, HttpPost, HttpPut, HttpDelete, HttpPatch |
| Response type | Task<IActionResult> async return |
| Result conversion | ToActionResult(result) helper method |

### Controller Conventions

| Element | Pattern |
|---------|---------|
| Constructor | Primary constructor with IMediator mediator and ILogger<T> logger |
| Base class | BaseController(logger) |
| Route format | Versioned: v1/{resource-name} |
| Tag attribute | OpenApiTag("Resource Name") for Swagger grouping |
| Permission attribute | RequireXxxPermission(Permissions.Resource.Action) |

### BaseController Helpers

| Method | Purpose |
|--------|---------|
| ToActionResult(result) | Converts ApiResult<T> to IActionResult |
| ToActionResult(result, map) | Converts with custom success mapping |
| AsActionResult(result, onSuccess) | Custom IActionResult on success |

---

## Result Pattern (ApiResult)

ApiResult is a discriminated union using OneOf library for type-safe error handling.

### Error Types

| Type | HTTP Status | Purpose |
|------|-------------|---------|
| Success<T> | 200 OK | Successful operation with data |
| NotFoundError | 404 Not Found | Resource not found |
| BadRequestError | 400 Bad Request | Invalid request |
| ValidationError | 400 Bad Request | Validation failures (list) |
| ValidationErrorWithDetails | 400 Bad Request | Field-specific validation errors |
| ConflictError | 409 Conflict | Resource already exists or conflict |
| UnauthorizedError | 401 Unauthorized | Authentication required |
| ForbiddenError | 403 Forbidden | Permission denied |
| InternalServerError | 500 Internal Server Error | System error |

### Factory Methods

| Method | Purpose |
|--------|---------|
| ApiResults.Success(data) | Wrap successful result |
| ApiResults.NotFound(message) | Resource not found error |
| ApiResults.BadRequest(message) | Bad request error |
| ApiResults.Validation(errors) | List of validation errors |
| ApiResults.ValidationWithDetails(dict) | Field-specific errors |
| ApiResults.Conflict(message) | Conflict error |
| ApiResults.Unauthorized(message) | Authentication error |
| ApiResults.Forbidden(message) | Permission denied |
| ApiResults.Error(message) | Internal server error |

---

## Entity Framework Core Patterns

| Check | Description |
|-------|-------------|
| DbContext base | Inherit from BaseDbContext |
| DbSet | DbSet<EntityType> for entity collections |
| Eager loading | Use Include() and ThenInclude() for related data |
| AsNoTracking | Use for read-only queries |
| Migrations | Stored in Migrations/ folder |

### BaseDbContext Features

| Feature | Description |
|---------|-------------|
| Constructor | Accepts DbContextOptions and IAppContext |
| Model cache | TenantModelCacheKeyFactory for per-context model caching |
| Domain events | Dispatches domain events on SaveChangesAsync |
| Design-time | Provides EmptyAppContext fallback for migrations |

### DbContext Configuration

| Step | Description |
|------|-------------|
| ConfigureTrackedEntities | Configure owned types (EntityUser, RequestData) |
| ApplyConfigurationsFromAssembly | Load all IEntityTypeConfiguration implementations |
| ApplyGlobalFilters | Apply tenant and soft-delete query filters |

---

## Multi-Tenancy Patterns

### Entity Hierarchy

All tenant-scoped entities inherit from TenantEntity which provides:

| Property | Type | Description |
|----------|------|-------------|
| TenantId | Guid | Primary isolation boundary (required) |
| OrganisationId | Guid? | Mid-level hierarchy (optional) |
| DivisionId | Guid? | Leaf-level hierarchy (optional) |
| UserId | Guid | Business owner of the entity |
| SecurityPolicyId | Guid? | Row-level security policy |
| Visibility | Visibility | Controls visibility at org/division level |

### Inherited from TrackedEntity

| Property | Type | Description |
|----------|------|-------------|
| Id | Guid | Primary key |
| CreatedAt | DateTimeOffset | Creation timestamp |
| ModifiedAt | DateTimeOffset | Last modification timestamp |
| CreatedBy | EntityUser | User who created (UserId, Name, IpAddress) |
| ModifiedBy | EntityUser | User who last modified |
| CreatedRequest | RequestData | Creation request tracking |
| ModifiedRequest | RequestData | Last modification request tracking |

### Tenant Hierarchy

| Level | Description | Example |
|-------|-------------|---------|
| Tenant | Customer account. All data belongs to a tenant. | "Acme Corp" |
| Organisation | Business unit within a tenant | "Sydney Office" |
| Division | Department within an organisation | "Transport Division" |

### Automatic Field Population

AuditStampingInterceptor automatically sets fields on SaveChanges:

| State | Fields Set |
|-------|------------|
| Added | TenantId, UserId, OrganisationId, DivisionId, CreatedAt, CreatedBy, CreatedRequest |
| Modified | ModifiedAt, ModifiedBy, ModifiedRequest |
| Deleted | Converts to soft delete (DeletedOn timestamp) |

---

## Context Token and IAppContext

### IAppContext Interface

IAppContext aggregates four sub-interfaces providing complete request context:

| Interface | Properties |
|-----------|------------|
| ITenantContext | TenantId, OrganisationId, DivisionId |
| IUserContext | UserId, UserName, Email, IsAuthenticated, Roles |
| IRequestContext | RequestId, SourceIp, CorrelationId, SessionId |
| ISecurityContext | AllowedDivisionIds, SecurityPolicies, AppPermissions, AccessLevel, AllowedOrganisationIds |

### Context Token

| Property | Value |
|----------|-------|
| Header | X-Context-Token |
| Issued By | Identity Management Service |
| Lifetime | 24 hours (configurable) |
| Contains | tenantId, organisationId, divisionId, roles, permissions |
| Refresh trigger | 419 Authentication Timeout response |

---

## Authentication Patterns (Two-Step)

### Step 1: OIDC Authentication (Keycloak)

| Token | Header | Purpose |
|-------|--------|---------|
| Keycloak JWT | Authorization: Bearer {token} | Proves user identity |
| Access Token | | 5-30 minutes lifetime |
| Refresh Token | | Used for silent renewal |

### Step 2: Context Token (Identity Management)

| Token | Header | Purpose |
|-------|--------|---------|
| Context Token | X-Context-Token | Specifies tenant/org/division scope |

### HTTP Status Codes for Auth

| Status | Meaning | Action |
|--------|---------|--------|
| 401 Unauthorized | Invalid/expired access token | Refresh token or re-authenticate |
| 403 Forbidden | User lacks required permission | Show error (no token refresh) |
| 419 Authentication Timeout | Context token expired/invalid | Refresh context token and retry |

---

## Middleware Pipeline Order (Critical)

The correct middleware order in Program.cs:

| Order | Middleware | Purpose |
|-------|------------|---------|
| 1 | UseHttpContext() | Extract RequestId, SourceIp, CorrelationId, SessionId |
| 2 | UseAuthentication() | Keycloak JWT validation |
| 3 | UseTenantAuth() (conditional) | Context token validation (skips public endpoints) |
| 4 | UseSerilogContextEnrichment() | Enrich LogContext with request context |
| 5 | UseOpenTelemetryPrometheusScrapingEndpoint() | Prometheus metrics (before authorization) |
| 6 | UseAuthorization() | Enforce Authorize attributes |
| 7 | MapControllers() | Route to controllers |

### TenantAuth Bypass Patterns

| Endpoint | Description |
|----------|-------------|
| .well-known/* | Discovery endpoints |
| /swagger/* | OpenAPI documentation |
| /metrics | Prometheus metrics |
| /health, /livez | Health checks |

---

## Validation Patterns (FluentValidation)

| Check | Description |
|-------|-------------|
| Validator class | Inherit from AbstractValidator<TCommand> |
| Rule definition | Use RuleFor() fluent API |
| Auto-registration | AddValidatorsFromAssembly in DI |
| Pipeline | ValidationBehavior in MediatR pipeline |

### Common Validation Rules

| Rule | Usage |
|------|-------|
| NotEmpty() | Required fields |
| MaximumLength(n) | String length limits |
| NotEqual() | Inequality check |
| Must(predicate) | Custom validation |
| When(condition) | Conditional validation |

---

## Logging Patterns (Serilog)

| Check | Description |
|-------|-------------|
| Logger injection | Use ILogger<T> from DI |
| Serilog setup | UseSerilog() in Program.cs |
| Loki sink | WriteTo.GrafanaLoki for log aggregation |
| Context enrichment | Enrich.FromLogContext() |
| Structured logging | Log JSON with correlation IDs |

### Required Log Fields

| Field | Description |
|-------|-------------|
| service | Service name (e.g., "asset-backend") |
| tenantId | Current tenant ID |
| userId | Current user ID |
| operation | Operation name |
| traceId | Distributed trace ID |
| correlationId | Request correlation ID |

---

## Observability Patterns (OpenTelemetry)

| Check | Description |
|-------|-------------|
| OTEL registration | AddOpenTelemetry() in services |
| Prometheus metrics | UseOpenTelemetryPrometheusScrapingEndpoint() |
| OTLP export | AddOtlpExporter for trace export |
| Auto-instrumentation | AddAspNetCoreInstrumentation, AddEntityFrameworkCoreInstrumentation |

### Observability Pillars

| Pillar | Implementation |
|--------|---------------|
| Logging | Serilog with Grafana Loki sink |
| Metrics | OpenTelemetry with Prometheus exporter |
| Tracing | OpenTelemetry with correlation ID propagation |
| Dashboards | Managed in infra repository |

---

## Key Dependencies (NuGet)

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| Microsoft.EntityFrameworkCore | 10.0.0 | ORM framework |
| Npgsql.EntityFrameworkCore.PostgreSQL | 10.0.0 | PostgreSQL provider |
| MediatR | 11.1.0 | CQRS pattern |
| FluentValidation | 12.0.0 | Input validation |
| OneOf | 3.0.271 | Discriminated unions |
| Swashbuckle.AspNetCore | 10.0.1 | OpenAPI documentation |

### Observability

| Package | Version | Purpose |
|---------|---------|---------|
| Serilog.AspNetCore | 8.0.3 | Structured logging |
| Serilog.Sinks.Grafana.Loki | 8.3.0 | Log aggregation |
| OpenTelemetry.Exporter.Prometheus.AspNetCore | 1.13.x | Metrics endpoint |

### Health Checks

| Package | Version | Purpose |
|---------|---------|---------|
| AspNetCore.HealthChecks.NpgSql | 9.0.0 | PostgreSQL health |
| AspNetCore.HealthChecks.Redis | 9.0.0 | Redis health |

---

## Shared Core Packages (Services.Core.*)

All published to GitHub NuGet registry with version pattern 0.2.x-develop.{commit}:

| Package | Purpose |
|---------|---------|
| Services.Core | Core DI, validation behaviors |
| Services.Core.Abstractions | Base entities (TenantEntity), ApiResult, interfaces |
| Services.Core.Auth.Keycloak | Keycloak JWT authentication |
| Services.Core.TenantAuth | Multi-tenant context token middleware |
| Services.Core.TenantAuth.Abstractions | TenantAuth interfaces |
| Services.Core.TenantAuth.Redis | Redis-backed tenant auth |
| Services.Core.EntityFrameworkCore | BaseDbContext, interceptors, filters |
| Services.Core.Caching | Distributed caching (Redis) |
| Services.Core.Caching.Abstractions | Caching interfaces |
| Services.Core.Caching.EntityFramework | EF Core caching integration |
| Services.Core.Http | HTTP context middleware, exception handling |
| Services.Core.Observability | OpenTelemetry integration |
| Services.Core.Eventing.Abstractions | Domain event interfaces |
| Services.Core.Eventing.Contracts | Event contracts |
| Services.Core.Eventing.Redis | Redis-based event bus |
| Notification.Client | Notification service client |

---

## Anti-Patterns to Detect

### Architecture Anti-Patterns

| Anti-Pattern | Location | Severity | Suggestion |
|--------------|----------|----------|------------|
| Direct DbContext in controller | Controllers/ | error | Use MediatR + Repository pattern |
| DTO in Domain | Domain/ | error | Keep DTOs in Application layer |
| Business logic in Controller | Controllers > 50 lines | warning | Move to Command/Query handlers |
| Missing validator | Command without Validator file | warning | Add FluentValidation validator |

### CQRS Anti-Patterns

| Anti-Pattern | Description | Severity | Suggestion |
|--------------|-------------|----------|------------|
| Throwing exceptions | throw new Exception in handlers | warning | Use ApiResult error types |
| Service Locator | GetService<> or GetRequiredService<> in handlers | error | Use constructor injection |
| Missing cancellation token | Handle method without CancellationToken | warning | Add CancellationToken parameter |

### Entity Framework Anti-Patterns

| Anti-Pattern | Description | Severity | Suggestion |
|--------------|-------------|----------|------------|
| N+1 query risk | foreach with await Get or ToList before foreach | warning | Use Include() or batched queries |
| Sync over async | .Result, .Wait(), .GetAwaiter().GetResult() | error | Use async/await |
| Missing TenantEntity | Entity not inheriting TenantEntity | error | Inherit from TenantEntity |

### Security Anti-Patterns

| Anti-Pattern | Description | Severity |
|--------------|-------------|----------|
| Hardcoded secrets | password=, apikey=, secret= in code | error |
| SQL injection | FromSqlRaw with string interpolation | error |
| Missing auth attribute | Controller without Authorize or AllowAnonymous | error |
| Disabled HTTPS | RequireHttpsMetadata = false in production | error |

### Logging Anti-Patterns

| Anti-Pattern | Description | Severity | Suggestion |
|--------------|-------------|----------|------------|
| Console.WriteLine | Direct console output | warning | Use ILogger |
| Empty catch | catch block with no logging | warning | Log or handle exception |
| Sensitive data logging | Logging password, secret, token | error | Mask sensitive data |

---

## Database Conventions

| Convention | Description |
|------------|-------------|
| Database | PostgreSQL |
| Per-service database | Each service has its own database |
| Migrations | EF Core migrations in Infrastructure layer |
| Naming | Snake_case via EFCore.NamingConventions |
| Connection strings | Configured per environment |

---

## Database Migration Workflow

### Key Principle: CI/CD Handles Migration Execution

Migrations are **automatically applied** by the running application on startup via `MigrationAndSeedDatabase()` in `Program.cs`. Developers do NOT run `dotnet ef database update` manually.

### Developer Workflow

| Step | Action | Command |
|------|--------|---------|
| 1. Create migration | Generate migration files | `dotnet ef migrations add <MigrationName>` |
| 2. Review migration | Check the generated .cs files | Manual review |
| 3. Commit | Push migration files to Git | `git commit` |
| 4. Deploy | CI/CD deploys to environment | Automatic |
| 5. Apply | Application startup runs migrations | Automatic via `MigrationAndSeedDatabase()` |

### How It Works

All backend services call `MigrationAndSeedDatabase()` at startup in `Program.cs`:

```csharp
// In Program.cs
await app.MigrationAndSeedDatabase();
```

This extension method:
1. Gets the DbContext from DI
2. Calls `db.Database.MigrateAsync()` to apply pending migrations
3. Runs any seed data operations
4. Skips execution in FunctionalTests and Swagger environments

### What NOT to Do

| Action | Why It's Wrong |
|--------|----------------|
| `dotnet ef database update` | Bypasses application startup, may miss seed data |
| Manual SQL scripts | Not tracked in migrations, inconsistent state |
| Modifying deployed database directly | Will be out of sync with code |

### Migration File Location

Migrations are stored in the Infrastructure layer:

```
{Service}.Infrastructure/
  └── Migrations/
      ├── 20260128_InitialCreate.cs
      ├── 20260128_InitialCreate.Designer.cs
      └── {DbContext}ModelSnapshot.cs
```
