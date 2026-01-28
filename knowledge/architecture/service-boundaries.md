# Service Boundaries

<!--
This file is referenced by: master-architect, validation-orchestrator, plan-validator
Last verified: January 2025
Source: Validated against Confluence docs and repository exploration
-->

## Service Ownership

### Core Platform Services

| Service | Owns | Can Access |
|---------|------|------------|
| identity-management | Users, Tenants, TenantInvitations, TenantMemberships, Organizations, OrganizationMemberships, Divisions, DivisionMemberships, Apps, AppRoles, AppPermissions, AppRolePermissions, AppResourceGroups, AppRoleResourceScopes, AllowedEndpoints, ApiKeys, ApiKeyUsageLogs, Roles, UserAppAssignments, UserPermissionOverrides, UserResourceScopes | Keycloak (admin API for user sync) |
| api-gateway | Routing rules, rate limits, API key validation | All backend services (routing only) |
| notification-backend | Notifications, NotificationCategories, NotificationSubscriptions | identity-management (user lookup) |
| common-backend | Contacts, ContactTypes | Shared entities for cross-service use |

### Application Services

| Service | Owns | Can Access |
|---------|------|------------|
| asset-backend | AssetCatalog context (Assets, AssetTypes, AssetSubTypes, AssetGroups, Manufacturers, ManufacturerModels, AssetDisposals), Maintenance context, DocumentManagement context, FuelManagement context, Telemetry context, TenantSettings context | identity-management (context validation) |
| hr-backend | Organization context (Departments, Positions, EmployeeAssignments, WorkSites), Payroll context (Employees, EmployeePayrollData, Contractors, Timesheets), Scheduling context (Shifts, ScheduledShifts, EmployeeAvailability, Zones) | identity-management (context validation) |
| inventory-backend | ProductCatalog context (Products, ProductCategories, ProductVariants), WarehouseManagement context (Warehouses, StorageLocations, WarehouseZones), SupplyChain context (PurchaseOrders, Suppliers, GoodsReceipts), InventoryCore (StockTransactions) | identity-management (context validation) |
| lms-backend | Courses context (Courses, CourseVersions, Modules, Steps, CourseCategories), Enrollments context (Enrollments, StepProgress, LearnerNotes), Quizzes context (Quizzes, QuizQuestions, QuizAttempts), Approvals context (ApprovalRequests) | identity-management (context validation) |
| onboard-backend | Onboarding workflows (Application-layer focused, minimal domain entities) | identity-management (context validation), hr-backend (employee data) |

### Service ID Registry

Registered service identifiers for cross-service communication (canonical registry from Confluence):

| Service | Service ID |
|---------|-----------|
| identity-management | 00000000-0000-0000-0000-000000000001 |
| hr-backend | 00000000-0000-0000-0000-000000000002 |
| lms-backend | 00000000-0000-0000-0000-000000000003 |
| inventory-backend | 00000000-0000-0000-0000-000000000004 |
| onboard-backend | 00000000-0000-0000-0000-000000000005 |
| asset-backend | 00000000-0000-0000-0000-000000000010 |

**Important:** Coordinate with the team before assigning a new Service ID to avoid conflicts.

### Shared Packages

#### Backend Shared Packages (dotnet-core repository)

| Package | Provides | Used By |
|---------|----------|---------|
| Services.Core | Main core library with common utilities | All backend services |
| Services.Core.Abstractions | Interface contracts (IAppContext, ITenantEntity, ITrackedEntity) | All backend services |
| Services.Core.Auth.Keycloak | Keycloak JWT authentication, multi-realm support | All backend services |
| Services.Core.TenantAuth | TenantAuthMiddleware, context token validation | All backend services |
| Services.Core.EntityFrameworkCore | BaseDbContext, global query filters, AuditStampingInterceptor | All backend services |
| Services.Core.Caching | Distributed caching with Redis | All backend services |
| Services.Core.Eventing.Redis | Redis Streams event publishing/consumption | All backend services |
| Services.Core.Eventing.Contracts | Integration event definitions (ApiKeyUsageLoggedEvent, NotificationEvent, NotificationBroadcast) | All backend services |
| Services.Core.Observability | Logging, distributed tracing, metrics | All backend services |
| Services.Core.Http | HTTP utilities, service account token handling | All backend services |

#### Frontend Shared Packages (mf-packages repository)

| Package | Provides | Used By |
|---------|----------|---------|
| @brainforgeau/security | Auth context provider, authorized axios, context token management, OIDC integration | All frontend MFs (singleton via Module Federation) |
| @brainforgeau/components | UI component library (buttons, forms, tables, modals, icons, navigation) | All frontend MFs |
| @brainforgeau/theme | Tailwind CSS theme configuration | All frontend MFs |
| @brainforgeau/observability | Frontend logging, tracing, metrics | All frontend MFs |

## Communication Rules

### Allowed Patterns

| From | To | Method | Purpose |
|------|-----|--------|---------|
| Any MF | Backend Services | REST (via ingress) | All API requests with Keycloak JWT + X-Context-Token |
| Backend | identity-management | REST | Context token validation, permission checks |
| Backend | Backend | REST (via ServiceAccountTokenHandler) | Cross-service queries with OAuth2 client credentials |
| Backend | Redis Streams | Pub/Sub | Integration events (at-least-once delivery) |
| Backend | PostgreSQL | EF Core | Own database only |
| Frontend | SignalR Hub | WebSocket | Real-time notifications via notification-backend |

### Cross-Service HTTP Communication

Services use ServiceAccountTokenHandler for service-to-service authentication:
- OAuth2 client credentials flow with ClientId and ClientSecret
- Token caching with configurable expiry buffer
- Used by: asset-backend, hr-backend, lms-backend, onboard-backend

### Forbidden Patterns

| Pattern | Reason |
|---------|--------|
| Frontend direct to backend (bypassing ingress) | Bypasses API gateway security |
| Backend direct database access to another service | Violates data ownership |
| Circular synchronous dependencies | Deadlock risk |
| Direct Keycloak access from application services | Use identity-management as proxy |
| Shared mutable state between services | Race conditions, coupling |

## Database Access Rules

### Database Ownership

Each backend service owns its own PostgreSQL database exclusively:

| Service | DbContext Class | Database |
|---------|----------------|----------|
| identity-management | IdentityManagementDbContext | identity |
| asset-backend | AssetManagementDbContext | assetdb |
| hr-backend | ApplicationDbContext | hr |
| inventory-backend | InventoryDbContext | inventorydb |
| lms-backend | LearningManagementDbContext | lms |
| notification-backend | NotificationDbContext | notification |

### Database Isolation Rules

- Each service reads and writes only its own database schemas
- Services NEVER access another service's database directly
- Cross-service data retrieval via REST APIs with context token propagation
- Each DbContext inherits from BaseDbContext which provides tenant filtering

### Schema Organization

Services organize their DbSets by bounded context. Example for asset-backend:
- AssetCatalog (assets, types, manufacturers)
- Maintenance (work orders, service templates)
- Telemetry (metrics, snapshots)
- DocumentManagement (files, attachments)
- Integration (webhooks, audit logs)
- Reporting (aggregated metrics)
- TenantSettings (per-tenant configuration)

## Multi-Tenancy Boundaries

### Tenant Hierarchy

The platform uses a three-level hierarchy for multi-tenant isolation:

| Level | Description | Isolation |
|-------|-------------|-----------|
| Tenant | Top-level customer account | Always enforced |
| Organization | Department or branch within tenant | Optional, hierarchical |
| Division | Team or unit within organization | Optional, hierarchical |

### TenantEntity Base Class

All tenant-scoped entities inherit from TenantEntity, which provides:
- TenantId (non-nullable Guid) - top-level isolation boundary
- OrganisationId (nullable Guid) - mid-level hierarchical scoping
- DivisionId (nullable Guid) - leaf-level hierarchical scoping
- UserId (non-nullable Guid) - business ownership
- SecurityPolicyId (nullable Guid) - row-level security
- Visibility (enum) - controls visibility within hierarchy

### Tenant Isolation Enforcement

| Layer | Enforcement Mechanism |
|-------|----------------------|
| Frontend | AuthContextProvider issues X-Context-Token after tenant selection |
| API Ingress | Context token header validation |
| Backend Middleware | TenantAuthMiddleware validates X-Context-Token, populates IAppContext |
| EF Core | Global query filters via TenantFilter (Simple, Hierarchical, or HierarchicalWithVisibility) |
| Domain | TenantEntity base class enforces tenant context |
| Storage | Tenant-prefixed paths: tenants/{tenantId}/... |

### IAppContext Interface

Aggregates four context interfaces for request-scoped tenant and user information:
- ITenantContext: TenantId, OrganisationId, DivisionId
- IUserContext: UserId, UserName, Email, IsAuthenticated, Roles
- IRequestContext: RequestId, SourceIp, CorrelationId, SessionId
- ISecurityContext: AllowedOrganisationIds, AllowedDivisionIds, AccessLevel, SecurityPolicies, AppPermissions

### Context Token Flow

1. User authenticates via Keycloak (receives JWT with user identity)
2. Frontend calls identity-management /v1/contexts/available to get accessible contexts
3. User selects tenant/organization/division (or auto-select if single)
4. Frontend calls identity-management /v1/contexts/issue to receive Context Token
5. Context token propagated in X-Context-Token header on all requests
6. TenantAuthMiddleware validates token and extracts claims into IAppContext
7. EF Core global filters ensure data isolation based on tenant hierarchy

### Global Query Filter Types

| Filter Type | Behavior |
|------------|----------|
| SimpleFilter | Matches TenantId exactly (allows empty for shared entities) |
| HierarchicalFilter | Applies TenantId always, OrganisationId/DivisionId when context has them |
| HierarchicalWithVisibility | Same as hierarchical but supports Visibility enum for tenant-wide or org-wide access |

## Event-Driven Boundaries

### Message Broker

Redis Streams is the exclusive message broker for integration events:
- Stream naming pattern: {streamPrefix}:{EventType}
- Delivery semantics: At-least-once with EventId-based deduplication
- Services register with AddRedisEventing() and AddRedisEventConsumer()

### Integration Events Defined

| Event | Purpose |
|-------|---------|
| ApiKeyUsageLoggedEvent | Audit logging of API key usage, published by api-gateway |
| NotificationEvent | Direct user targeting for notifications (Sender, Target, Category, Title, Body) |
| NotificationBroadcast | Subscription-based notification routing with category matching |

### Events Published

| Service | Events | Purpose |
|---------|--------|---------|
| api-gateway | ApiKeyUsageLoggedEvent | Audit logging of API key usage |
| asset-backend | NotificationEvent | Maintenance alerts and notifications |
| lms-backend | NotificationEvent | Approval notifications |

### Events Consumed

| Service | Listens To | Purpose |
|---------|------------|---------|
| identity-management | ApiKeyUsageLoggedEvent | Persist usage logs, update real-time metrics |
| notification-backend | NotificationEvent, NotificationBroadcast | Persist notifications, send via SignalR |

### Domain Events vs Integration Events

- Domain Events: Internal to bounded context (e.g., AssetCreatedEvent), not published externally
- Integration Events: Cross-service events implementing IIntegrationEvent, published to Redis Streams

## API Versioning Rules

- All APIs versioned with path prefix: /v1/...
- Breaking changes require new version: /v2/...
- Support previous version during migration period
- Generated clients via NSwag/OpenAPI for type-safe consumption

## Schema Change Rules

### Database Migrations

1. Additive changes (new columns, tables): Safe to deploy anytime
2. Breaking changes: Require migration plan and coordination
3. Multi-tenant impact: All tenants affected simultaneously

### API Contract Changes

1. New endpoints/fields: Non-breaking, deploy freely
2. Removed/renamed fields: Breaking, requires client updates
3. Shared package updates: Coordinate across all consuming services

## Identity Management Boundaries

### What identity-management Owns

- User identity (linked to Keycloak by sub claim)
- Tenant hierarchy (Tenant, Organization, Division entities)
- Memberships (TenantMembership, OrganizationMembership, DivisionMembership)
- Apps and permissions (App, AppRole, AppPermission, AppRolePermission)
- API keys and usage logging (ApiKey, ApiKeyUsageLog)
- Context token issuance and validation
- User resource scopes and permission overrides

### What identity-management Does NOT Own

- User credentials (Keycloak owns authentication)
- Application-specific business data (each service owns)
- Business domain logic (each service owns)

## Validation Checks

Used by plan-validator to verify implementation plans:

| Check | Rule | Severity |
|-------|------|----------|
| db_ownership | Service only accesses its own database | error |
| context_propagation | Cross-service calls include X-Context-Token | error |
| direct_db_access | No cross-service direct DB access | error |
| keycloak_proxy | Apps use identity-management, not direct Keycloak | error |
| tenant_isolation | All queries filtered by tenant context via TenantEntity | error |
| event_boundaries | Async operations use Redis Streams, not sync calls | warning |
| api_versioning | Breaking API changes require new version | warning |

## References

- Service contracts: Generated OpenAPI specs in each service's Api project
- Event schemas: Services.Core.Eventing.Contracts namespace
- Context token spec: identity-management /v1/contexts endpoints
- Confluence documentation: docs/confluence/ directory
