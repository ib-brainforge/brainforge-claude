# Design Patterns

<!--
This file is referenced by: design-pattern-advisor, feature-planner
Last verified: January 2025
NOTE: All patterns have been verified against actual repository implementations.
-->

## Frontend Patterns

### UI Component Library (MANDATORY)

**The platform follows JIRA Design Language. ALWAYS use @brainforgeau/components over raw HeroUI.**

@brainforgeau/components provides BrainForge-styled wrappers around HeroUI that maintain visual consistency. Each component uses the "Base" prefix naming convention.

**Most-Used Components (in order of usage frequency):**
1. Icon - Custom icon set (125+ icons)
2. BaseButton - Button with BrainForge variants
3. BaseInput - Form input field
4. PageSpinner - Loading spinner
5. BaseSelect / BaseSelectItem - Dropdown selections
6. BaseCheckbox - Checkbox input
7. BaseTable - TanStack Table wrapper
8. TablePagination - Table pagination
9. BaseStatusSelect - Status badge dropdown
10. BaseModal (with Header, Body, Footer) - Modal dialogs

**HeroUI Direct Usage (allowed only for):**
- addToast (notification utility)
- Alert (inline alerts)
- HeroUIProvider, ToastProvider (providers)

### Required Patterns

| Pattern | When to Use | Implementation |
|---------|-------------|----------------|
| Module Federation | All microfrontends | @module-federation/enhanced with @module-federation/modern-js via Rspack bundler |
| Auth Provider | App entry point | FlexibleAuthProvider from @brainforgeau/security package |
| Permission Guards | Protected routes/actions | usePermissions hook and PermissionGuard component from @brainforgeau/security |
| Query State Management | Server state | atomWithQuery from jotai-tanstack-query combined with Jotai atoms |
| Form Pattern | All forms | TanStack Form (@tanstack/react-form) with Zod validation and @tanstack/zod-form-adapter |
| Error Boundary | Page-level | ErrorBoundary component from @brainforgeau/components (wraps react-error-boundary) |
| Data Tables | Tabular data | BaseTable from @brainforgeau/components with TanStack Table and server-side pagination |

### Component Structure

Frontend microfrontends follow a feature-based folder structure:

- **routes/** - File-based routing via Modern.js with page.tsx and layout.tsx files
- **components/[feature]/** - Feature-specific organization containing:
  - **hooks/** - Custom hooks for data fetching (useFeatureData), filtering (useFeatureFilters), and table configuration (useFeatureTable)
  - **state/** - Jotai atoms for filter state and data state
  - **components/** - UI components including table columns, filters, and create/edit modals
- **api/** - API client configuration and authorized axios instances
- **atoms/** - Global atoms for configuration and authentication state
- **utils/** - Shared utility functions

### State Management Rules

| State Type | Solution | Package |
|------------|----------|---------|
| Server state | TanStack Query with Jotai integration | @tanstack/react-query, jotai-tanstack-query |
| Auth state | Centralized auth atom via singleton | @brainforgeau/security (eager singleton in Module Federation) |
| Global client state | Jotai primitive and derived atoms | jotai |
| Local component state | React hooks | useState, useReducer |
| Form state | TanStack Form | @tanstack/react-form |
| URL state | Route params | Modern.js file-based routing |

### Data Fetching Patterns

The primary data fetching approach uses TanStack Query (React Query) integrated with Jotai atoms via jotai-tanstack-query. The atomWithQuery function creates atoms that manage server state including loading states, error handling, and automatic refetching.

For data fetching without Suspense (recommended pattern to avoid white flash during filter changes), a custom async atom pattern is used with manual loading state management via writable atoms. This keeps previous data visible while new data loads.

API communication uses authorizedAxios from @brainforgeau/security which automatically attaches Keycloak JWT and Context Token headers, handles token refresh, and provides consistent error handling.

### Permission Patterns

**usePermissions Hook** - Returns permission checking functions including hasPermission, hasAnyPermission, hasAllPermissions, hasRole, hasAnyRole, hasAllRoles, hasAppPermission, and getAppRole. Also provides hasElevatedAccess, hasElevatedReadAccess, hasElevatedWriteAccess for scope-based access control.

**PermissionGuard Component** - Wrapper component for conditional rendering of UI elements based on permissions. Used extensively in table action columns, modals, and form sections.

**withAuthorizationRequired HOC** - Higher-order component for permission-gated pages and routes.

**withAuthenticationRequired HOC** - Higher-order component for authentication-gated pages, typically wrapping page exports.

### Module Federation Configuration

All microfrontends share critical dependencies as singletons:
- react and react-dom (eager singletons)
- @brainforgeau/security (CRITICAL: must be eager singleton for auth state sharing)
- jotai (singleton)
- @heroui/react and @heroicons/react (singletons)
- framer-motion (singleton)

The navbar is consumed as a remote module from navbar-mf. Note that @brainforgeau/components is NOT shared due to Webpack/Rspack SVG transformation incompatibilities - each microfrontend bundles its own copy.

---

## Backend Patterns

### Required Patterns

| Pattern | When to Use | Core Component |
|---------|-------------|----------------|
| Clean Architecture | All services | Four-layer structure: Domain, Application, Infrastructure, Api |
| CQRS | All commands/queries | MediatR handlers organized in Commands/ and Queries/ folders |
| Repository | Data access | IRepository interfaces defined in Domain layer, implementations in Infrastructure |
| Result Pattern | All handlers | ApiResult from Services.Core.Abstractions using OneOf discriminated union |
| FluentValidation | Command validation | AbstractValidator implementations, integrated via MediatR ValidationBehavior |
| Domain Events | Side effects within bounded context | IDomainEvent interface, dispatched via EF Core interceptor to MediatR |
| Multi-Tenancy | All data access | TenantEntity base class with automatic query filters |

### Clean Architecture Layers

**Domain Layer** - Contains entities, value objects, domain events, and repository interfaces. Has NO external dependencies. Organized by bounded context with Aggregates/, Events/, Repositories/, and ValueObjects/ subdirectories.

**Application Layer** - Contains use cases, DTOs, and MediatR handlers. Organized by feature with Commands/ and Queries/ subdirectories. Each command/query includes the request record, handler class, and optional validator.

**Infrastructure Layer** - Contains EF Core implementations, external service integrations, and repository implementations. Includes Persistence/ for database concerns, Services/ for external integrations, and AntiCorruption/ for external system adapters.

**Api Layer** - Contains controllers, middleware configuration, and program startup. Controllers delegate to MediatR, using Commands/Queries directly as request bodies (avoiding unnecessary DTO mappings where possible).

### CQRS Pattern

Commands and Queries are implemented as immutable records with init-only properties. Handlers implement IRequestHandler from MediatR and return ApiResult for consistent error handling.

Commands typically represent write operations that modify state, while Queries represent read operations. Both use the same MediatR pipeline which includes validation behavior, caching behavior, and tenant context extraction.

Validators use FluentValidation's AbstractValidator base class and are automatically discovered and executed by the ValidationBehavior pipeline.

### Result Pattern

ApiResult is a discriminated union type built on the OneOf library. It can contain either a Success with data or various error types including ValidationError, NotFoundError, BadRequestError, ConflictError, UnauthorizedError, ForbiddenError, and InternalServerError.

The ApiResults static class provides factory methods (Success, NotFound, Conflict, etc.) for creating results. Controllers convert ApiResult to appropriate HTTP status codes via the ToActionResult extension method.

### Entity Base Classes

**TenantEntity** (Services.Core.Abstractions) - Base class providing multi-tenancy properties (TenantId, OrganisationId, DivisionId, UserId, SecurityPolicyId) and audit tracking (CreatedAt, ModifiedAt, CreatedBy, ModifiedBy). Uses UUID v7 for ID generation.

**Domain-Specific Entity Hierarchies:**
- **DomainEntity** - For aggregate roots without soft delete, extends TenantEntity and provides domain events via AddDomainEvent method
- **SoftDeletableDomainEntity** - Adds soft delete support via DeletedOn property and IDeletedEntity interface
- **ChildEntity** - For child entities within aggregates
- **SoftDeletableChildEntity** - Child entities with soft delete support

Some services (like HR) extend the base TenantEntity with domain-specific properties such as LocationScopeId and TeamScopeId for additional scoping.

### Repository Pattern

Repository interfaces are defined in the Domain layer following the IRepository pattern. Common methods include GetByIdAsync, GetAllAsync, Add, Update, and Remove. Domain-specific query methods (like ExistsByNameAsync, GetByNameAsync) are added per aggregate needs.

Implementations in the Infrastructure layer use EF Core DbContext. Global query filters automatically apply tenant isolation - all queries are filtered by TenantId from the current context.

### Domain Events

Domain events are implemented as sealed records implementing the IDomainEvent marker interface. Events are added to entities via the AddDomainEvent method inherited from the Entity base class.

When SaveChangesAsync is called, an EF Core interceptor dispatches accumulated domain events through MediatR, allowing handlers to react to domain state changes within the same transaction.

Domain events differ from integration events: domain events are for intra-bounded-context communication with immediate consistency, while integration events are for cross-service communication with eventual consistency.

### Integration Events (Cross-Service)

Integration events implement IIntegrationEvent interface (from Services.Core.Eventing.Abstractions) with properties EventId, OccurredOnUtc, and EventType.

Publishing uses IIntegrationEventPublisher interface with RedisStreamPublisher implementation backed by Redis Streams. Consumption uses IntegrationEventHostedService with consumer groups for reliable message processing.

Event handlers implement IIntegrationEventHandler interface. Handler registration uses fluent builder pattern via RedisEventConsumerBuilder.AddHandler method.

---

## Pattern Selection Guide

| Feature Type | Frontend Pattern | Backend Pattern |
|--------------|------------------|-----------------|
| Data listing | TanStack Table with atomWithQuery | Query with Specification pattern |
| Form submission | TanStack Form with Zod validation | Command with FluentValidation |
| Authentication | FlexibleAuthProvider (shell mode for MF, standalone for local dev) | Keycloak JWT validation + TenantAuth middleware |
| Permissions | usePermissions hook, PermissionGuard component | RequirePermissionAttribute, Authorization handlers |
| File upload | Components FileUploader (separate DTO for IFormFile) | IFileService with signed URLs |
| Real-time updates | SignalR subscription (signalr-react integration) | SignalR Hub |
| Caching (frontend) | TanStack Query staleTime configuration | Services.Core.Caching (ICachedQuery with MediatR behavior) |

## Multi-Tenancy Patterns

### Frontend

Context selection uses useHierarchicalContext hook from @brainforgeau/security. Users authenticate via Keycloak, then select their context (tenant/organization/division) from available options.

All API calls automatically include the context token via authorizedAxios which attaches both the Keycloak JWT (Authorization header) and Context Token (X-Context-Token header).

### Backend

TenantAuthMiddleware from Services.Core.TenantAuth extracts and validates the context from the X-Context-Token header. The extracted context is available via IAppContext injection.

IAppContext provides access to Tenant property containing TenantId, OrganisationId, DivisionId, and related identifiers. EF Core global query filters automatically apply tenant isolation to all database queries.

## Caching Patterns

### Backend (Two-Tier via Services.Core.Caching)

Queries implement ICachedQuery interface specifying CacheKey, CacheTags, CacheExpiration, and optional LocalCacheExpiration. The CachingBehavior MediatR pipeline handles cache lookup and population automatically.

Cache invalidation is tag-based using ICacheInvalidator interface. Commands that modify data invalidate relevant cache tags, triggering refresh on next query. CacheKeyBuilder and CacheTagBuilder utilities help construct consistent keys and tags.

For ApiResult-returning queries, ApiResultCachingBehavior provides specialized caching that only caches successful results.

### Frontend

TanStack Query provides client-side caching with configurable staleTime. Data remains fresh for the staleTime duration before background refetch occurs. Query invalidation can be triggered manually via queryClient.invalidateQueries.

## References

- Backbone architecture overview: confluence/netcorp-backbone-architecture.md
- Page pattern implementation guide: docs/dev-files/PAGE_PATTERN_GUIDE.md
- Controller refactoring (DTO removal): docs/dev-files/REFACTORING_GUIDE.md
- Technical overview: confluence/EAHT/netcorp360/technical-overview/content.md
- Backend services structure: confluence/EAHT/netcorp360/technical-overview/backend-services/content.md
- Frontend services structure: confluence/EAHT/netcorp360/technical-overview/frontend-services/content.md
