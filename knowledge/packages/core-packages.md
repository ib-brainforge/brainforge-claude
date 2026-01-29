# Core Packages

This file documents the shared packages used across the NetCorp360 platform.
Referenced by: design-pattern-advisor, core-validator, package managers

---

## Frontend Packages (mf-packages)

Located in repository: `mf-packages/packages/`

### @brainforgeau/security

Authentication and authorization utilities for all microfrontends.

**CRITICAL: Must be configured as eager singleton in Module Federation to ensure authentication state is shared correctly across module boundaries.**

**Purpose:**
- OIDC authentication integration via react-oidc-context
- Context token management for multi-tenancy
- Authorized HTTP client with automatic token injection
- Shared authentication state management via Jotai atoms
- Permission checking and access control

**Key Exports:**

Auth module:
- FlexibleAuthProvider, ShellAuthProvider, AuthContextProvider - Authentication context providers for different scenarios
- useAuth - Hook for accessing authentication state and methods
- useContextToken - Hook for context token management (emits CONTEXT_TOKEN_CHANGED_EVENT)
- useHierarchicalContext - Hook for tenant/organization/division hierarchy
- useImpersonation - Hook for user impersonation functionality
- useMicrofrontendAuth - Hook specifically for Module Federation auth integration
- withAuthenticationRequired - HOC wrapper for routes requiring authentication
- withAuthorizationRequired - HOC wrapper for routes requiring specific authorization
- authorizedAxios - Pre-configured axios instance with automatic token injection (emits GLOBAL_ERROR_EVENT, NAVBAR_NOTIFICATION_EVENT)
- crossAppAxios - Axios instance for cross-microfrontend communication
- useRedirectGuard - Hook for redirect protection

Permissions module:
- usePermissions - Comprehensive permissions hook returning: roles, permissions, appPermissions, hasRole, hasAnyRole, hasAllRoles, hasPermission, hasAnyPermission, hasAllPermissions, hasAppPermission, hasAnyAppPermission, hasAllAppPermissions, hasAppRole, filterNavItems, getAppPermissions, hasElevatedAccess, hasElevatedReadAccess, hasElevatedWriteAccess, hasScopesAccess
- GuardedItem - Interface for items with permission guards

Components module:
- AccessDenied - Component displayed when access is denied
- PermissionGuard - Component for conditional rendering based on permissions
- useCanAccess - Hook for checking access rights
- hasElevatedAccess, hasElevatedReadAccess, hasElevatedWriteAccess, hasScopesAccess - Utility functions

Configuration module:
- RuntimeConfig - Runtime configuration utilities

Logger module:
- createSecurityLogger - Factory for security-specific logging

**Peer Dependencies:** react 18.3.1, react-dom 18.3.1, jotai 2.13.1, react-oidc-context 3.3.0, @brainforgeau/identity-management-client

**Dependencies:** axios

---

### @brainforgeau/components

Core UI components library for all microfrontends.

**NOT shared via Module Federation** - Each microfrontend bundles its own copy due to webpack SVG transformation incompatibilities with Rspack.

**Purpose:**
- Consistent UI components across all applications
- Integration with HeroUI design system
- Chart visualizations
- Table components with TanStack Table
- Real-time subscription components via SignalR

**Export Paths (granular imports):**
- /icons - SVG icon components (140+ custom icons)
- /form - Form-related utilities
- /accordion - Accordion component (BaseAccordion)
- /table - Table components with TanStack Table integration
- /alert - Alert components (ValidationAlert, GlobalErrorAlert, GlobalErrorContext)
- /navbar - Navbar integration (NavbarActionContext, NavbarNotificationContext)
- /button - Button components (BaseButton)
- /subscriptions - SignalR subscription management
- /base - Base components (Box, PageSpinner, Icon, Pager, ErrorBoundary, BaseErrorMessage)
- /charts - Chart components (BarChart, DonutChart, TabbedBarChart)
- /select - Select/dropdown components (BaseSelect)
- /input - Input components (BaseInput)
- /autocomplete - Autocomplete component (BaseAutocomplete)
- /date-picker - Date picker components (BaseDatePicker, BaseWeekPicker)
- /time-input - Time input component (BaseTimeInput)
- /breadcrumbs - Breadcrumb navigation (BaseBreadcrumbs)
- /sidenav - Side navigation (SideNav, SideNavDesktop, SideNavMobile, SideNavContent)
- /modal - Modal components (BaseModal, BaseModalBody, BaseModalContent, BaseModalFooter, BaseModalHeader)
- /utils - Utility functions

Additional components:
- Avatar - User avatar display
- Menu - Menu components
- MetadataPanel - Metadata display panel
- TagSelect, FilterSelect, ChipSelect, StatusSelect - Specialized selection components
- Textarea, Toggle, NumberInput, Radio, Checkbox - Form inputs

Subscriptions module hooks and components:
- useSubscriptions, useEntitySubscription, useCategorySubscription - Hooks for SignalR subscriptions
- SubscriptionToggle, CategorySubscriptionToggle - Toggle components for subscription management
- subscriptionsAtom, categoriesAtom, subscriptionsLoadingAtom, subscriptionsErrorAtom - Jotai atoms for subscription state

**Peer Dependencies:** react 18.3.1, react-dom 18.3.1, jotai 2.13.1, @heroui/react 2.8.2, @heroicons/react ^2.1.1, @tanstack/react-table ^8.21.3, framer-motion ^12.23.12, @microsoft/signalr ^8.0.0, react-error-boundary ^6.0.0

**Dependencies:** @internationalized/date, @react-types/shared, chart.js, chartjs-plugin-datalabels, dayjs, react-chartjs-2, tailwind-merge, tailwind-variants

**Special Configuration:** CSS side effects enabled; requires SVGR webpack plugin for SVG transformations

---

### @brainforgeau/theme

Tailwind CSS theme configuration for consistent styling across all microfrontends.

**Purpose:**
- Centralized Tailwind CSS configuration
- Theme CSS variables and custom properties
- HeroUI theme integration with light and dark modes
- Custom color scheme (brand colors)
- Custom animations and typography

**Key Exports:**
- Main entry imports theme.css
- ./theme.css subpath export for direct CSS import

**Features:**
- Dark mode support (class-based)
- Custom color palette with primary, secondary, and accent colors
- HeroUI theme integration with light and dark variants
- Custom animations (fade-in, slide-in)
- Custom font family configuration (Inter)

**Peer Dependencies:** react 18.3.1, react-dom 18.3.1, @heroui/react 2.8.2, tailwindcss 4.1.13

**Special Configuration:** CSS side effects enabled; exports both ESM and CJS formats

---

### @brainforgeau/observability

Frontend observability package providing logging, tracing, and metrics for all microfrontends.

**Purpose:**
- OpenTelemetry integration for browser-based distributed tracing
- Fetch and XMLHttpRequest instrumentation
- Web vitals collection
- Correlation ID propagation across service calls
- Session management for user tracking
- React integration via context and hooks

**Key Exports:**

Types:
- LogLevel, LogEntry, LokiConfig, TracingConfig, MetricsConfig, ObservabilityConfig - Configuration types
- Logger, Tracer, Span, Metrics, ObservabilityInstance - Core interface types
- TracingHeaders, Tracker, PageViewEvent, UserActionEvent, UserActionType - Tracking types
- ErrorHandlerConfig, HttpInterceptorConfig, SimpleInterceptorConfig, TrackingConfig - Handler configuration types

Logger:
- createLogger - Factory function for creating loggers
- LokiLogger - Loki-compatible logger implementation

Tracer:
- initializeTracing - Initialize OpenTelemetry tracing
- shutdownTracing - Clean shutdown of tracing
- createNoopTracer - No-operation tracer for testing

Metrics:
- createMetrics - Factory for metrics collection

Error Handling:
- setupGlobalErrorHandlers - Global error handler setup
- createErrorBoundaryHandler - React error boundary integration

React Integration:
- ObservabilityProvider - React context provider component
- useObservability, useLogger, useTracer, useMetrics, useTracker - Context hooks
- useErrorBoundaryHandler, useTracingHeaders - Additional hooks
- ObservabilityProviderProps - Provider props type

Session Management:
- getSessionId, clearSessionId, rotateSessionId - Session ID management functions

HTTP Integration:
- getTracingHeaders - Get headers for distributed tracing
- createAxiosInterceptor, createAxiosResponseInterceptor - Axios middleware factories
- createTracedFetch - Fetch wrapper with tracing
- createSessionIdInterceptor - Session ID injection interceptor
- generateRequestId - Request ID generation

Tracking:
- createTracker - Analytics tracker factory

**Peer Dependencies:** react 18.3.1, react-dom 18.3.1

**Dependencies:** @opentelemetry/api, @opentelemetry/context-zone, @opentelemetry/exporter-trace-otlp-http, @opentelemetry/instrumentation, @opentelemetry/instrumentation-fetch, @opentelemetry/instrumentation-xml-http-request, @opentelemetry/resources, @opentelemetry/sdk-trace-web, @opentelemetry/semantic-conventions, web-vitals

---

### Internal Packages (not published to npm)

| Package | Purpose |
|---------|---------|
| @brainforgeau/federation-types | TypeScript type definitions for Module Federation remotes (hrMf, assetMf, drivecomMf with App, routes, components, hooks, services exports) |
| @brainforgeau/tailwind-config | Shared Tailwind configuration with HeroUI theme plugin |

---

### Generated API Clients

These packages are auto-generated from backend OpenAPI specifications via CI/CD workflows.

**Generation Process:**
1. Backend changes trigger `generate-client.yml` workflow on push to `main`/`develop`
2. Workflow builds API with Swagger configuration to generate OpenAPI spec
3. OpenAPI Generator CLI (v7.16.0) generates TypeScript client using `typescript-axios` template
4. Client is published to GitHub Packages NPM registry

**Trigger Paths:** Changes to `openapi/**`, API/Application/Domain/Infrastructure layers

**Version Strategy:** Same as mf-packages (see `knowledge/cicd/package-publishing.md`)

| Package | Source Service | Purpose |
|---------|----------------|---------|
| @brainforgeau/identity-management-client | identity-management | Identity and authentication API client |
| @brainforgeau/hr-backend-client | hr-backend | HR management API client |
| @brainforgeau/asset-backend-client | asset-backend | Asset management API client |
| @brainforgeau/learning-backend-client | lms-backend | Learning management API client |
| @brainforgeau/inventory-backend-client | inventory-backend | Inventory management API client |
| @brainforgeau/onboard-backend-client | onboard-backend | Onboarding API client |
| @brainforgeau/notification-backend-client | notification-backend | Notification API client |

**Smart Rebuild:** Workflows compare OpenAPI specs between commits and skip client generation if no API changes detected (unless manually triggered via `workflow_dispatch`).

---

## Backend Packages (dotnet-core)

Located in repository: `dotnet-core/`
Target Framework: .NET 10.0 (all packages)

### Services.Core.Abstractions

Core interfaces, base entities, and result types for multi-tenant SaaS applications.

**Purpose:**
- Define base entity types for all domain models
- Define context interfaces for tenant/user/request data
- Provide discriminated union result types for API responses
- Define constants for claims, roles, and scope types

**Key Types:**

Base Entities:
- Entity - Abstract base class for all entities
- TrackedEntity - Abstract base with audit fields (inherits Entity, implements ITrackedEntity)
- TenantEntity - Abstract base for tenant-scoped entities (inherits TrackedEntity, implements ITenantEntity, IVisibilityEntity)

Entity Interfaces:
- ITenantEntity - Interface for tenant-scoped entities
- ITrackedEntity - Interface for entities with audit tracking
- IDeletedEntity - Interface for soft-deletable entities
- IVersioned - Interface for versioned entities
- IIdEntity<T> - Generic interface for entities with typed ID
- IConcurrency<T> - Interface for entities with concurrency control
- IVisibilityEntity - Interface for entities with visibility levels

Context Interfaces:
- IAppContext - Combined interface for ITenantContext, IUserContext, IRequestContext, ISecurityContext
- ITenantContext - Interface providing tenant information
- IUserContext - Interface providing user information
- IRequestContext - Interface providing request metadata
- ISecurityContext - Interface providing security/permissions context
- IAppContextSetter - Interface for setting app context values
- IContextScopeRunner - Interface for running code within specific context

Domain Events:
- IDomainEvent - Marker interface for domain events
- IDomainEvents - Interface for entity domain event collection
- EntityChangedEvent - Record for entity change notifications

Records and Classes:
- EntityUser - Record representing a user in entity context
- RequestData - Record containing request metadata
- Tenant - Class representing tenant information
- SecurityPolicy - Record for security policy configuration
- ResourceScope - Record with ScopeType and Identifiers for resource-based authorization
- AppPermissions - Record for application permission structure
- FileStorageOptions, FileValidationOptions - Configuration classes for file handling

API Result Types (using OneOf):
- Success<T> - Successful result wrapper
- NotFoundError, BadRequestError, ValidationError, ValidationErrorWithDetails - Client error types
- ConflictError, UnauthorizedError, ForbiddenError - Authorization error types
- InternalServerError - Server error type
- ApiResults - Static factory class for creating result types

Extensions and Constants:
- ClaimsPrincipalExtensions - Extension methods for claims principal
- Constants - Static class with nested HttpContextTypes, ClaimTypes, Roles, ScopeTypes

Enums:
- Visibility - Entity visibility levels
- AccessLevel - Access level enumeration

**Dependencies:** OneOf 3.0.271

---

### Services.Core

Core implementations including validation, clock, context management, and MediatR behaviors.

**Purpose:**
- Provide system clock abstraction
- Implement ambient app context for request-scoped data
- Provide context scope runner for executing code with specific context
- Implement MediatR pipeline behaviors for validation

**Key Types:**
- SystemClock - IClock implementation using system time
- AmbientAppContext - IAppContextSetter implementation using AsyncLocal
- ContextScopeRunner - IContextScopeRunner implementation for scoped context execution
- ValidationBehavior<TRequest, TResponse> - MediatR behavior for FluentValidation
- WriteScopeValidationBehavior<TRequest, TResponse> - MediatR behavior for write scope validation
- DependencyInjection - Static class with service registration extensions

**Dependencies:** MediatR 11.1.0, FluentValidation 12.0.0, Microsoft.Extensions.DependencyInjection.Abstractions 9.0.10, Microsoft.Extensions.Logging.Abstractions 9.0.0

**Project References:** Services.Core.Abstractions

---

### Services.Core.EntityFrameworkCore

Entity Framework Core extensions for multi-tenancy with automatic tenant filtering.

**Purpose:**
- Provide base DbContext with multi-tenant support
- Implement global query filters for tenant isolation
- Provide save changes interceptors for audit stamping
- Implement resource scope filtering for authorization

**Key Types:**

DbContext:
- BaseDbContext - Abstract base class with tenant filtering and audit support

Interceptors:
- AuditStampingInterceptor - SaveChangesInterceptor that auto-populates audit fields (CreatedBy, ModifiedBy, TenantId, etc.)
- TenantWriteAuthorizationInterceptor - SaveChangesInterceptor validating tenant write permissions

Model Caching:
- TenantModelCacheKeyFactory - IModelCacheKeyFactory for per-tenant model caching

Query Filters:
- QueryFilterNames - Static class with filter name constants
- QueryFilterExpressions - Static class with filter expression builders
- SoftDeleteFilter - Static class for soft delete filtering
- VisibilityFilter - Static class for visibility-based filtering
- TenantFilter - Static class for tenant-based filtering
- AppPermissionFilter - Static class for permission-based filtering

Scoped Entity Interfaces:
- IScopedEntity - Base interface for scoped entities
- ITeamScopedEntity - Interface for team-scoped entities
- ILocationScopedEntity - Interface for location-scoped entities
- IDivisionScopedEntity - Interface for division-scoped entities
- IOrganisationScopedEntity - Interface for organisation-scoped entities

Filter Providers:
- IAppPermissionFilterProvider - Interface for permission filter providers
- IResourceScopeFilterProvider - Interface for resource scope filter providers
- IResourceGroupMappingProvider - Interface for resource group mapping

Extensions:
- ContextExtensions - Extension methods for EF context
- ResourceScopeExtensions - Extension methods for resource scope queries
- AppPermissionFilterExtensions - Extension methods for permission filtering
- ISecurityTenantContext - Interface combining security and tenant context

Configuration:
- CoreInterceptorOptions - Options class for interceptor configuration
- DependencyInjection - Static class with service registration extensions

**Dependencies:** Microsoft.EntityFrameworkCore 10.0.0

**Project References:** Services.Core.Abstractions

---

### Services.Core.TenantAuth

Context token authentication and tenant authorization middleware.

**Purpose:**
- Validate context tokens in request headers
- Extract and parse tenant context from tokens
- Populate IAppContext with tenant/user/security data
- Provide authorization attributes for controllers

**Key Types:**

Middleware:
- TenantAuthMiddleware - ASP.NET Core middleware for context token validation

Claim Parsers:
- IClaimParser<TResult> - Interface for claim parsing
- TenantHierarchyClaimParser - Parser for tenant hierarchy claims
- RolesClaimParser - Parser for role claims
- SecurityPolicyClaimParser - Parser for security policy claims
- AppPermissionsClaimParser - Parser for application permissions claims
- AccessLevelClaimParser - Parser for access level claims
- OrganisationAccessClaimParser - Parser for organisation access claims
- DivisionAccessClaimParser - Parser for division access claims

Token Validation:
- IContextTokenValidator - Interface for token validation
- ContextTokenValidator - Implementation of context token validation
- ContextTokenValidationResult - Result record for validation outcome
- ContextTokenValidationError - Enum for validation error types
- IContextTokenRequirementChecker - Interface for checking token requirements
- ContextTokenRequirementChecker - Implementation of requirement checking

Token Extraction:
- ITokenExtractor - Interface for extracting tokens from requests
- TokenExtractor - Implementation of token extraction
- IContextTokenKeyProvider - Interface for providing signing keys
- ContextTokenKeyProvider - Implementation of key provider

Response Handling:
- IContextTokenResponseWriter - Interface for writing error responses
- ProblemDetailsResponseWriter - ProblemDetails format response writer

Models:
- TenantContextData - Record containing extracted tenant context
- TenantContextExtractionResult - Record for extraction outcome

Authorization:
- RequirePermissionAttribute - Authorization filter attribute for permission checks

Configuration:
- ContextTokenStatusCodes - Static class with HTTP status code mappings

Extensions:
- ServiceCollectionExtensions - DI registration extensions
- TenantAuthServiceExtensions - Additional service registration extensions

**Dependencies:** Microsoft.AspNetCore.Authentication.JwtBearer 10.0.0, Microsoft.IdentityModel.Protocols.OpenIdConnect 8.14.0, Microsoft.IdentityModel.Tokens 8.14.0

**Project References:** Services.Core.Abstractions, Services.Core.TenantAuth.Abstractions, Services.Core, Services.Core.Auth.Keycloak

---

### Services.Core.TenantAuth.Abstractions

Abstractions for tenant authentication and authorization.

**Purpose:**
- Define token extraction interfaces
- Define authorization attributes
- Define context requirement interfaces

**Key Types:**

Token Extraction:
- ITokenExtractor - Interface for extracting tokens from HTTP requests
- TokenExtractionResult - Record containing extraction result

Authorization Attributes:
- RequireContextTokenAttribute - Filter requiring valid context token
- AllowAnonymousContextAttribute - Filter allowing anonymous context access
- RequirePermissionAttribute - Filter requiring specific permissions
- RequireTenantRoleAttribute - Filter requiring specific tenant role
- RequireMinimumScopeAttribute - Filter requiring minimum scope level

Context Requirements:
- ITenantContextRequirement - Interface for tenant context requirements
- TenantContextAttribute - Attribute for marking context requirements
- TenantContextMetadata - Record containing context metadata

RSA Key Storage:
- IRsaKeyStore - Interface for RSA key storage
- StoredRsaKey - Class representing stored RSA key

Configuration:
- TenantAuthOptions - Options class for tenant auth configuration

**Dependencies:** None (abstractions only)

---

### Services.Core.TenantAuth.Redis

Redis-backed RSA key storage for context token signing.

**Purpose:**
- Store RSA signing keys in Redis for distributed scenarios
- Manage key rotation and cleanup

**Key Types:**
- RedisRsaKeyStore - IRsaKeyStore implementation using Redis
- RedisRsaKeyStoreOptions - Configuration options for Redis key store
- DependencyInjection - Static class with service registration extensions

**Dependencies:** StackExchange.Redis 2.8.41, Microsoft.Extensions.Options, Microsoft.Extensions.Logging.Abstractions

**Project References:** Services.Core.TenantAuth.Abstractions

---

### Services.Core.Auth.Keycloak

Keycloak integration for JWT authentication.

**Purpose:**
- Configure JWT Bearer authentication with Keycloak
- Handle JWT events for user context population
- Support query string token authentication for SignalR

**Key Types:**

JWT Event Handling:
- IJwtBearerEventHandler - Interface for JWT event handlers
- JwtBearerEventHandlerBase - Abstract base for event handlers
- UserContextEventHandler - Handler populating user context from JWT
- QueryStringTokenEventHandler - Handler for query string tokens
- CompositeJwtBearerEvents - Aggregator for multiple event handlers

Middleware:
- UserContextMiddleware - Middleware for user context initialization
- UserContextMiddlewareExtensions - Extension methods for middleware registration

Configuration:
- KeycloakAuthOptions - Configuration options for Keycloak integration

Extensions:
- KeycloakAuthServiceExtensions - Service collection extensions for Keycloak auth

**Dependencies:** Microsoft.AspNetCore.Authentication.JwtBearer 10.0.0, Microsoft.Extensions.Options

**Project References:** Services.Core.Abstractions

---

### Services.Core.Observability

OpenTelemetry integration for distributed tracing and metrics.

**Purpose:**
- Configure OpenTelemetry tracing for ASP.NET Core
- Instrument EF Core, HTTP client, and runtime metrics
- Export traces via OTLP and metrics via Prometheus

**Key Types:**

Extensions:
- ObservabilityServiceCollectionExtensions - Service collection extensions for observability setup
- ObservabilityApplicationBuilderExtensions - Application builder extensions for middleware

Configuration:
- WellKnownActivitySources - Static class with activity source names
- ObservabilityOptions - Main configuration options
- OtlpExporterOptions - OTLP exporter configuration
- PrometheusExporterOptions - Prometheus exporter configuration

Additional:
- ObservabilityEnrichers - Trace enrichment utilities
- AssemblyInfo - Assembly metadata

**Dependencies:** OpenTelemetry.Exporter.Console 1.13.1, OpenTelemetry.Exporter.OpenTelemetryProtocol 1.13.1, OpenTelemetry.Extensions.Hosting 1.13.1, OpenTelemetry.Instrumentation.AspNetCore 1.13.0, OpenTelemetry.Instrumentation.EntityFrameworkCore 1.13.0-beta.2, OpenTelemetry.Instrumentation.Http 1.13.0, OpenTelemetry.Instrumentation.Runtime 1.13.0, OpenTelemetry.Exporter.Prometheus.AspNetCore 1.13.0-rc.1

**Project References:** Services.Core.Abstractions

---

### Services.Core.Caching

Hybrid caching implementation with L1 memory and L2 distributed cache, plus MediatR integration.

**Purpose:**
- Provide hybrid caching with tag-based invalidation
- Implement MediatR behaviors for automatic caching
- Support cache key and tag building patterns

**Key Types:**

Cache Building:
- CacheKeyBuilder - Static class for building cache keys
- CacheTagBuilder - Static class for building cache tags

MediatR Behaviors:
- CachingBehavior<TRequest, TResponse> - Pipeline behavior for caching query results
- ApiResultCachingBehavior<TRequest, TResponse> - Specialized behavior for API result caching

Cache Invalidation:
- ICacheInvalidator - Interface for cache invalidation
- DefaultCacheInvalidator - Standard cache invalidator implementation
- EmptyCacheInvalidator - No-op invalidator for testing

Configuration:
- CachingOptions - Configuration options for caching

Extensions:
- DependencyInjection - Service collection extensions

**Dependencies:** Microsoft.Extensions.Caching.Hybrid 10.0.0, Microsoft.Extensions.Configuration.Abstractions 10.0.0, Microsoft.Extensions.Options.ConfigurationExtensions 10.0.0, MediatR 11.1.0

**Project References:** Services.Core.Abstractions, Services.Core.Caching.Abstractions

---

### Services.Core.Caching.Abstractions

Abstractions for caching behavior interfaces.

**Purpose:**
- Define caching interfaces for MediatR queries
- Define cache invalidation interface

**Key Types:**
- ICacheInvalidator - Interface for invalidating cache entries by tags
- ICachedQuery - Interface for queries that should be cached
- ICachedApiResultQuery - Interface for API result queries that should be cached

**Dependencies:** None (abstractions only)

**Project References:** Services.Core.Abstractions

---

### Services.Core.Caching.EntityFramework

EF Core caching provider.

**Status:** Package structure exists but contains no implementations.

**Target Framework:** .NET 10.0

---

### Services.Core.Http

HTTP context middleware and global exception handling.

**Purpose:**
- Provide middleware for HTTP request context
- Implement global exception handler with ProblemDetails
- Support service account token handling

**Key Types:**

Middleware and Handlers:
- HttpContextMiddleware - Middleware for HTTP context initialization
- GlobalExceptionHandler - IExceptionHandler for unhandled exceptions

Problem Details:
- ProblemDetailsFactory - Factory for creating ProblemDetails responses
- ProblemDetailsExtensions - Extension methods for ProblemDetails

Service Accounts:
- ServiceAccountOptions - Configuration for service account authentication
- ServiceAccountExtensions - Extension methods for service account setup
- ServiceAccountTokenHandler - DelegatingHandler for service account tokens

Configuration:
- HttpContextOptions - Options for HTTP context middleware

Extensions:
- HttpContextServiceExtensions - Service collection extensions

**Dependencies:** Microsoft.AspNetCore.App (framework reference), Microsoft.Extensions.Hosting.Abstractions 10.0.0, Microsoft.Extensions.Options 10.0.0

**Project References:** Services.Core.Abstractions

---

### Services.Core.Eventing.Abstractions

Core abstractions for integration events and event publishing.

**Purpose:**
- Define integration event interface
- Define event publisher and handler interfaces
- Define event envelope for message transport

**Key Types:**
- IIntegrationEvent - Marker interface for integration events
- IIntegrationEventPublisher - Interface for publishing events
- IIntegrationEventHandler<TEvent> - Interface for handling events (where TEvent : IIntegrationEvent)
- IntegrationEventEnvelope - Record wrapping events with metadata for transport

**Dependencies:** None (abstractions only)

---

### Services.Core.Eventing.Contracts

Concrete integration event definitions shared across services.

**Purpose:**
- Define shared event contracts between services
- Provide notification event types

**Key Types:**

Events:
- ApiKeyUsageLoggedEvent - Event for API key usage logging
- NotificationBroadcast - Event for broadcasting notifications
- NotificationEvent - Event for individual notifications

Models:
- NotificationAction - Record for notification actions
- NotificationTarget - Record for notification targeting
- NotificationSender - Record for notification sender information

**Dependencies:** None (contracts only)

**Project References:** Services.Core.Eventing.Abstractions

---

### Services.Core.Eventing.Redis

Redis-backed event bus implementation with OpenTelemetry tracing.

**Purpose:**
- Implement event publishing via Redis pub/sub
- Implement event consumption with automatic deserialization
- Provide distributed tracing for events

**Key Types:**
- RedisEventingOptions - Configuration options for Redis eventing
- RedisEventConsumerBuilder - Builder for configuring event consumers
- DependencyInjection - Service collection extensions

Observability:
- EventingActivitySource - Static class for activity source
- Operations - Nested class with operation name constants
- Tags - Nested class with tag name constants

**Dependencies:** StackExchange.Redis 2.8.41, Microsoft.Extensions.Hosting.Abstractions 10.0.0, Microsoft.Extensions.Options 10.0.0, Microsoft.Extensions.Logging.Abstractions 10.0.0, Microsoft.Extensions.DependencyInjection.Abstractions 10.0.0, OpenTelemetry.Api 1.11.2

**Project References:** Services.Core.Eventing.Abstractions

---

## Module Federation Configuration

Shared dependencies configured as singletons across all microfrontends (verified from hr-mf/module-federation.config.ts and other MFs):

**Shared as Singletons:**
| Package | Singleton | Eager | Strict Version | Required Version |
|---------|-----------|-------|----------------|------------------|
| react | Yes | Yes | Yes | 18.3.1 |
| react-dom | Yes | Yes | Yes | 18.3.1 |
| @brainforgeau/security | Yes | Yes | No | - |
| jotai | Yes | No | - | - |
| @heroui/react | Yes | No | - | - |
| @heroicons/react | Yes | No | - | - |
| framer-motion | Yes | No | - | - |

**Critical Notes:**
- @brainforgeau/security MUST be singleton and eager - required for auth context sharing across module boundaries
- @brainforgeau/components is NOT shared - each MF bundles its own copy due to webpack SVG transformation incompatibilities with Rspack

**Remotes:**
- All hosts consume @brainforgeau/navbar from navbar-mf via remoteEntry.js

**Type Generation:**
- TypesFolder: @mf-types
- consumeAPITypes: true for TypeScript support across remotes

---

## Usage Rules

| Need | Use This | Not This |
|------|----------|----------|
| UI Components | @brainforgeau/components imports | Custom HTML elements |
| Authentication | @brainforgeau/security hooks | Direct OIDC library calls |
| API Calls | authorizedAxios or crossAppAxios | Raw fetch/axios |
| Theming | @brainforgeau/theme | Inline styles |
| Base Entity | TenantEntity | Custom entity classes |
| DB Context | Inherit BaseDbContext | Raw DbContext |
| Permissions | RequirePermissionAttribute | Custom auth logic |
| Tenant Filtering | Global query filters (automatic) | Manual WHERE clauses |
| Caching | ICachedQuery interface | Manual cache logic |
| Events | IIntegrationEvent | Direct Redis/message calls |

---

## References

- Frontend packages source: `mf-packages/packages/`
- Backend packages source: `dotnet-core/`
- Frontend services docs: `docs/confluence/EAHT/netcorp360/technical-overview/frontend-services/`
- Backend services docs: `docs/confluence/EAHT/netcorp360/technical-overview/backend-services/`
- Architecture overview: `docs/confluence/netcorp-backbone-architecture.md`
