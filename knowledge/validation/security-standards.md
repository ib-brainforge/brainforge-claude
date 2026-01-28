# Security Standards

<!--
PROJECT-SPECIFIC: Security requirements for BrainForge platform.
This is referenced by: plan-validator
Last verified: 2026-01-27
Source: Verified against docs/confluence/EAHT/netcorp360/technical-overview/core-platform/authentication-and-authorization, docs/api_key_auth, identity-management, dotnet-core, hr-backend repositories
-->

## Two-Token Authentication Architecture

BrainForge uses a two-step authentication system that separates identity verification from data access authorization.

**Step 1: OIDC Authentication** - Verifies WHO the user is via Keycloak, issuing Access Token, ID Token, and Refresh Token.

**Step 2: Context Token** - Determines WHAT data the user can access by establishing tenant, organization, and division scope.

| Token | Header | Issued By | Purpose |
|-------|--------|-----------|---------|
| Access Token (JWT) | `Authorization: Bearer {token}` | Keycloak | Proves user identity |
| Context Token | `X-Context-Token: {token}` | Identity Management API | Specifies tenant/org/division scope |

**Both tokens are required for all authenticated API requests.**

### Token Lifecycle

| Token | Lifetime | Proactive Refresh | Refresh Trigger |
|-------|----------|-------------------|-----------------|
| Access Token (JWT) | 5-30 minutes (configurable) | 2 minutes before expiry | 401 Unauthorized |
| Refresh Token | Hours to days | - | Access token expiry |
| Context Token | 8 hours (default, configurable) | 60 seconds before expiry | 419 Authentication Timeout |

### Authentication State Flow

Authentication progresses through these states:
1. `initializing` - OIDC library loading
2. `validating` - Token validation in progress
3. `loading-context` - Fetching contexts and issuing context token
4. `ready` - Fully authenticated (both tokens present)

Error states: `error` (authentication failed), `unauthenticated` (needs sign-in)

---

## OIDC Authentication (Keycloak)

### Passwordless Email OTP

| Property | Value |
|----------|-------|
| Provider | Keycloak |
| Authentication Method | Passwordless email OTP |
| OTP Characters | 0-9, A-Z (alphanumeric) |
| OTP Length | 6 characters |
| OTP Format | `XXX-XXX` (dashed for readability) |
| OTP Validity | 10 minutes |
| OTP Comparison | Case-insensitive, whitespace/dash tolerant |
| Alternative | Magic link option available |

### Automatic User Provisioning

When a user authenticates for the first time:
- Account is automatically created in Keycloak
- Name is extracted from email
- Email is marked as verified
- Default "user" role is assigned

No pre-registration is required - users can log in with just their email address.

### OIDC Endpoints

| Endpoint | URL Pattern |
|----------|-------------|
| Authority | `https://auth.brainforge.com.au/realms/{realm}` |
| Token | `{authority}/protocol/openid-connect/token` |
| Authorization | `{authority}/protocol/openid-connect/auth` |
| Logout | `{authority}/protocol/openid-connect/logout` |

---

## Context Token

### Context Token Claims

| Claim | Description |
|-------|-------------|
| `tenant_id` | The tenant UUID |
| `organisation_id` | The organization UUID (optional) |
| `division_id` | The division UUID (optional) |
| `user_id` | The user's UUID |
| `session_id` | Session tracking ID |
| `roles` | User's roles in this context (array) |
| `app_permissions` | Permissions for the current app (JSON) |
| `exp` | Token expiration time |

### Context Token Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/contexts/available` | Returns list of contexts user can access |
| `POST /v1/contexts/issue` | Issues context token for selected context |
| `GET /v1/contexts/jwks` | Public keys for token validation |

---

## Authentication Requirements

### Backend Middleware Order

The middleware pipeline order is critical. In backend services (verified in hr-backend/Program.cs):

1. **UseHttpContext()** - Extract RequestId, SourceIp, CorrelationId, SessionId
2. **UseAuthentication()** - Keycloak JWT validation, populate HttpContext.User
3. **UseTenantAuth()** - X-Context-Token validation, populate IAppContext
4. **UseSerilogContextEnrichment()** - Enrich logs with context
5. **UseAuthorization()** - Enforce authorization attributes

TenantAuthMiddleware includes regex-based path exclusion patterns for endpoints that don't require context tokens.

### Authorization Attributes

| Attribute | Purpose | Location |
|-----------|---------|----------|
| `[Authorize]` | Basic authentication required | ASP.NET Core |
| `[AllowAnonymous]` | No authentication required | ASP.NET Core |
| `[RequireContextToken]` | Context token required | Services.Core.TenantAuth.Abstractions |
| `[AllowAnonymousContext]` | Context token not required | Services.Core.TenantAuth.Abstractions |
| `[RequirePermission]` | Specific permission required | Services.Core (base class) |
| `[RequireIdentityPermission]` | Identity-specific permission | IdentityManagement.Api |

### Endpoints Excluded from Tenant Auth

These endpoints are excluded from context token validation via regex patterns:
- `.well-known/*` - OpenID Connect discovery
- `swagger/*` - API documentation
- `metrics` - Prometheus metrics
- `health`, `livez` - Health checks
- `contexts/available`, `contexts/issue` - Context token flow
- `tenants/resolve` - Tenant resolution for custom domains

---

## Multi-Tenancy Security

### Tenant Hierarchy

The platform uses a three-level hierarchy for data isolation:

| Level | Description | Example |
|-------|-------------|---------|
| **Tenant** | A customer account (all data belongs to a tenant) | "Acme Corp" |
| **Organization** | A business unit within a tenant | "Sydney Office" |
| **Division** | A department within an organization | "Transport Division" |

### TenantEntity Base Class

All tenant-scoped entities must inherit from `TenantEntity` (defined in Services.Core.Abstractions).

The base class provides these properties:
- `TenantId` - Required, which tenant owns this record
- `OrganisationId` - Optional, which organization
- `DivisionId` - Optional, which division
- `UserId` - Optional, which user owns this record
- `SecurityPolicyId` - Optional, for row-level security
- `Visibility` - Entity visibility level

HR-specific entities extend this with additional scoping: `LocationScopeId`, `TeamScopeId`.

### Automatic Tenant Filtering

- **Global Query Filters**: DbContext (BaseDbContext) applies automatic tenant filtering on all queries
- **Audit Stamping**: AuditStampingInterceptor automatically sets tenant fields on insert from IAppContext
- **No Manual Filtering**: Developers don't need to add WHERE clauses for tenant filtering

### Context-Based Access

The `IAppContext` interface provides current context for data filtering:
- Implements `ITenantContext` (TenantId, OrganisationId, DivisionId)
- Implements `IUserContext` (UserId, Email, Roles)
- Implements `IRequestContext` (RequestId, CorrelationId)
- Implements `ISecurityContext` (permissions, resource scopes)

Populated by TenantAuthMiddleware from the Context Token.

### Tenant Isolation Tiers

| Tier | Keycloak | Database | Domain |
|------|----------|----------|--------|
| Standard | Shared realm, per-tenant client | Shared (TenantId filter) | Subdomain/shared |
| Enhanced | Dedicated realm | Shared | Custom domain |
| Enterprise | Dedicated realm | Dedicated | Custom domain |

---

## API Key Authentication

For programmatic access without interactive OAuth2 flows (external integrations, partner systems).

### API Key Properties

| Property | Description |
|----------|-------------|
| Header | `X-Api-Key: ak_xxxxxxxxxxxx` |
| Prefix | `ak_` |
| Storage | Hashed, shown only once at creation |
| Scope | Bound to specific tenant |

### API Key Features

| Feature | Description |
|---------|-------------|
| Endpoint allowlisting | Specific path patterns and HTTP methods |
| Rate limiting | Per-minute and per-day limits |
| Tenant scope | Key bound to specific tenant |
| Optional expiration | Configurable expiry date |
| Context token generation | Gateway generates context token from API key |

### API Gateway Flow

1. Client sends request with API key in header
2. Gateway validates API key
3. Gateway looks up tenant associated with key
4. Gateway generates Context Token for that tenant
5. Gateway forwards request to backend with Authorization + X-Context-Token headers
6. Backend processes request with tenant context (no backend changes required)

### Rate Limit Headers

- `X-RateLimit-Limit` - Maximum requests allowed
- `X-RateLimit-Remaining` - Requests remaining in window
- `X-RateLimit-Reset` - Unix timestamp when limit resets
- `Retry-After` - Seconds to wait before retrying (on 429)

---

## Authorization Patterns

### Permission System

Centralized permission management in identity-management with resource/action/scope model.

| Component | Description |
|-----------|-------------|
| Resource | Domain entity (scheduling, timesheets, employees, assets) |
| Action | Operation (read, write, approve, manage) |
| Scope | Data visibility level |

Permission format: `{resource}.{action}` (e.g., `scheduling.read`, `timesheets.approve`)

### Scope Types

| Scope | User Can Access |
|-------|-----------------|
| `own` | Only resources created by/assigned to the user |
| `team` | Resources within assigned team(s) |
| `location` | Resources within assigned location(s) |
| `division` | Resources within assigned division(s) |
| `organisation` | All resources within the organisation |
| `tenant` | All resources across all organisations |

### Resource Scopes in Token

Context token includes `resourceScopes` mapping each resource group to its scope type and specific IDs:

| Field | Description |
|-------|-------------|
| `resourceScopes[resource].scope` | Scope type for this resource |
| `resourceScopes[resource].ids` | Specific scope identifiers (location IDs, team IDs, etc.) |

### Frontend Permission Hooks

The `usePermissions` hook from `@bf-github/security` package provides:
- `can(permission)` - Check single permission
- `canAny(...permissions)` - Check if any permission granted
- `canAll(...permissions)` - Check if all permissions granted
- `getResourceScope(resource)` - Get scope for a resource
- `hasMinimumScope(resource, minimumScope)` - Check scope level
- `canAccessId(resource, id)` - Check access to specific ID

---

## Input Validation

### FluentValidation Pattern

All Commands must have corresponding validators using FluentValidation AbstractValidator pattern.

| Validation Type | Description |
|-----------------|-------------|
| NotEmpty() | Required field |
| MaximumLength(n) | String length limit |
| When() | Conditional validation |
| Must() | Custom validation logic |

Validators are registered and executed automatically via MediatR pipeline.

---

## HTTP Status Codes

| Status | Name | Meaning | Frontend Action |
|--------|------|---------|-----------------|
| 401 | Unauthorized | Access token invalid/expired, user unauthenticated | Refresh access token or redirect to login |
| 403 | Forbidden | Permission denied (user lacks required permission) | Show error banner, **NO token refresh** |
| 419 | Authentication Timeout | Context token invalid/expired | Refresh context token with exponential backoff and retry |
| 429 | Too Many Requests | Rate limit exceeded | Exponential backoff |

### Context Token Specific Errors (419)

| Error Type | Description |
|------------|-------------|
| Token Required | Context token header missing but required |
| Token Expired | Context token has passed expiration time |
| Invalid Signature | Token signature doesn't match expected key |
| Invalid Token | Token is malformed or cannot be parsed |
| Key Not Found | Signing key referenced by token not recognized |

**Important**: 419 is used instead of 403 for context token issues to prevent infinite loops. Frontend only refreshes tokens on 419, not on 403 (permission denied).

---

## Audit Logging

### Required Log Fields (Serilog Enrichment)

All logs must include:
- `RequestId` - Unique per request
- `CorrelationId` - Cross-service tracking
- `SessionId` - User session tracking
- `UserId` - User identity
- `TenantId` - Tenant context
- `SourceIp` - Client IP address

### Structured Log Format

Logs are JSON formatted with service name, tenant context, operation, trace ID, severity, and elapsed time.

---

## Frontend Security

### Token Storage

| Token Type | Storage | Reason |
|------------|---------|--------|
| Access Token | Memory/sessionStorage | Short-lived, never localStorage |
| Refresh Token | httpOnly cookie or memory | Secure handling |
| Context Token | sessionStorage | Session-scoped, never localStorage |

### Authorized HTTP Client

Use `useAuthorizedAxios` hook from `@bf-github/security` for all API calls:
- Automatically attaches both tokens to requests
- Handles 401 with automatic token refresh
- Handles 419 with context token refresh and retry
- Proactive token refresh before expiry

### Microfrontend Token Sharing

- Shell application handles complete authentication flow
- Microfrontends read tokens from shared Jotai store
- Token changes broadcast via custom `CONTEXT_TOKEN_CHANGED` event

---

## Security Anti-Patterns

### Authentication Anti-Patterns

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| Controller without auth attribute | error | All endpoints must declare `[Authorize]` or `[AllowAnonymous]` |
| Hardcoded secrets in code | error | Use configuration/secrets management |
| RequireHttpsMetadata = false in production | error | Always require HTTPS metadata |
| Skipping token validation | error | Always validate tokens |

### Authorization Anti-Patterns

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| Query without TenantId filter | error | All queries must be tenant-scoped (use TenantEntity) |
| Direct DbContext in Controller | error | Use MediatR + Repository pattern |
| Hardcoded role checks | warning | Use permission-based checks instead |

### Data Anti-Patterns

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| String interpolation in FromSqlRaw | error | Use parameterized queries |
| Logging passwords, tokens, API keys | error | Mask sensitive data |
| Returning full user objects | warning | Use DTOs with limited fields |

### Frontend Anti-Patterns

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| Token in localStorage | error | Use sessionStorage only |
| Hardcoded API keys | error | Use environment variables |
| dangerouslySetInnerHTML without sanitization | warning | Always sanitize HTML |
| eval() usage | error | Never use eval |

---

## Security Checklist

### Backend Service

- [ ] All controllers have `[Authorize]` or `[AllowAnonymous]`
- [ ] All entities inherit from `TenantEntity`
- [ ] All commands have FluentValidation validators
- [ ] No hardcoded secrets in code
- [ ] Sensitive data masked in logs
- [ ] HTTPS required in production
- [ ] Health/metrics endpoints excluded from auth
- [ ] Middleware order is correct (Authentication before TenantAuth before Authorization)

### Frontend Application

- [ ] Uses `useAuthorizedAxios` for API calls
- [ ] Tokens stored in sessionStorage (not localStorage)
- [ ] No hardcoded API URLs or keys
- [ ] Permission checks before sensitive actions
- [ ] Handles 401 with token refresh
- [ ] Handles 419 with context token refresh (not 403)
- [ ] Error boundaries for auth failures
