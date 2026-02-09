# System Architecture

<!--
This file is referenced by: master-architect, validation-orchestrator, feature-planner
Last verified: January 2025
-->

## Overview

BrainForge (NetCorp360) is a multi-tenant SaaS platform built on a **Netcorp Backbone Architecture** that centralizes identity, authorization, and observability while providing shared packages for consistent patterns across applications. The architecture follows microservices principles with a distributed microfrontend composition.

**Core Principles:**
- Unified identity/authorization centralized in identity-management service
- Standardized telemetry and observability via shared infrastructure
- Shared packages for backend (dotnet-core) and frontend (mf-packages)
- Accelerated new app development via reusable building blocks and common patterns

## Platform Architecture Layers

| Layer | Components |
|-------|------------|
| Ingress (HTTPS) | app.brainforge.com.au, auth.brainforge.com.au |
| Frontend | App Shell, HR MF, Asset MF, Identity MF, Inventory MF, DriveCom MF, LMS MF, Tracking MF |
| Backend | HR API, Asset API, Inventory API, Identity API, Notification API, LMS API, Onboard API, Tracking API |
| Public API | API Gateway (API Key Authentication) |
| Infrastructure | Keycloak, PostgreSQL, Redis, RabbitMQ |

## Repository Structure

The following repositories exist in the bf-github workspace:

**Core Services:**
- identity-mf - Frontend for auth UI, login flows, and invitations
- identity-management - Backend for identity, tenancy, permissions, and context token APIs
- dotnet-core - Shared .NET packages (15+ NuGet projects)
- mf-packages - Shared frontend packages (6 npm packages)

**Application Services (Backend + Frontend pairs):**
- asset-backend / asset-mf - Asset management (vehicles, equipment, maintenance)
- hr-backend / hr-mf - HR management (employees, scheduling, timesheets, payroll)
- inventory-backend / inventory-mf - Inventory tracking and management
- lms-backend / lms-mf - Learning management system
- tracking-backend / tracking-mf - GPS tracking, fleet management, geofencing, driver fatigue
- tracking-ingestion - TCP listener for GPS device protocols (StatefulSet)
- tracking-persistence-worker - Redis-to-PostgreSQL position writer
- onboard-backend / onboard-mf - Employee onboarding workflows
- onboard-app - Standalone onboarding application
- drivecom-mf - Driver communication microfrontend
- navbar-mf - Shared navigation component

**Shell Applications:**
- app - Main shell application (microfrontend host)
- auth - Auth shell application
- common-mf - Common/shared microfrontend utilities
- common-backend - Common backend utilities

**Infrastructure:**
- infra - Kubernetes manifests, CI/CD, observability (Flux GitOps)
- api-gateway - API gateway for external access
- aspire - .NET Aspire local development orchestration

**Public Sites:**
- public-website - Marketing website
- public-website-strapi - Strapi CMS for website
- netcorp-public-website - Netcorp branding variant

**Documentation:**
- docs - Confluence export and technical documentation

## Services Map

### Core Platform Services

| Service | Type | Responsibility |
|---------|------|----------------|
| identity-management | backend | User identity, tenancy hierarchy, permissions, API keys, context token issuance |
| identity-mf | frontend | Auth UI, login flows, invitations, user/role management, tenant/org/division selection |
| api-gateway | gateway | External API access, API key authentication, request routing to backend services |

### Application Services

| Service | Type | Responsibility |
|---------|------|----------------|
| asset-backend | backend | Asset lifecycle, maintenance, tracking, work orders |
| hr-backend | backend | Employees, positions, scheduling, timesheets, payroll, organizational structure |
| inventory-backend | backend | Products, stock, warehouse management |
| lms-backend | backend | Learning management, training modules |
| onboard-backend | backend | Employee onboarding workflows |
| tracking-backend | backend | GPS tracking, fleet management, geofences, alerts, speed rules, driver fatigue |
| tracking-ingestion | backend | TCP listener for GPS device protocols, writes raw positions to Redis |
| tracking-persistence-worker | backend | Consumes GPS positions from Redis, writes to PostgreSQL |
| notification-backend | backend | Email, SMS, push notifications, SignalR real-time updates |

### Shared Packages (dotnet-core)

| Package | Purpose |
|---------|---------|
| Services.Core | Core shared utilities |
| Services.Core.Abstractions | Interfaces, base entities (TenantEntity, TrackedEntity) |
| Services.Core.Auth.Keycloak | Keycloak authentication integration |
| Services.Core.Caching | Distributed caching implementation |
| Services.Core.Caching.Abstractions | Caching interfaces |
| Services.Core.Caching.EntityFramework | EF Core caching integration |
| Services.Core.EntityFrameworkCore | DbContext, interceptors, global query filters |
| Services.Core.Eventing.Abstractions | Event interfaces |
| Services.Core.Eventing.Contracts | Event contracts |
| Services.Core.Eventing.Redis | Redis pub/sub event implementation |
| Services.Core.Http | HTTP client utilities |
| Services.Core.Observability | Logging, tracing, metrics |
| Services.Core.TenantAuth | Context token middleware, tenant authentication |
| Services.Core.TenantAuth.Abstractions | Tenant auth interfaces |
| Services.Core.TenantAuth.Redis | Redis-backed tenant auth |

### Shared Packages (mf-packages)

| Package | Namespace | Purpose |
|---------|-----------|---------|
| components | @brainforgeau/components | Core UI components library |
| security | @brainforgeau/security | Authentication context, authorized axios, OIDC integration |
| theme | @brainforgeau/theme | Tailwind CSS theme configuration |
| observability | @brainforgeau/observability | Logging, tracing, metrics |
| federation-types | Internal | Module federation type definitions |
| tailwind-config | Internal | Shared Tailwind configuration |

## Service ID Registry

Unique identifiers configured in each service's appsettings.json. The canonical registry is maintained in Confluence documentation.

| Service | Service ID | Service Name |
|---------|-----------|--------------|
| asset-backend | 00000000-0000-0000-0000-000000000001 | AssetManagement |
| tracking-backend | 00000000-0000-0000-0000-000000000002 | Tracking |
| identity-management | (see identity config) | IdentityManagement |
| hr-backend | (see hr config) | HumanResources |
| lms-backend | (see lms config) | LearningManagement |
| inventory-backend | (see inventory config) | InventoryManagement |
| onboard-backend | (see onboard config) | OnboardManagement |

> **Important:** Coordinate with the team before assigning a new Service ID to avoid conflicts. The canonical registry is in docs/confluence/netcorp-backbone-architecture.md.

## Two-Stage Authentication

NetCorp360 uses a two-stage authentication system:

**Stage 1: OIDC Authentication (Keycloak)**
- User authenticates via passwordless email OTP flow
- Keycloak issues Access Token, ID Token, and Refresh Token
- Proves WHO the user is

**Stage 2: Context Token (Identity Management)**
- User selects tenant/organization/division context
- Identity Management API issues Context Token
- Determines WHAT data the user can access

Both tokens are required for all API requests:
- Authorization header: Bearer token from Keycloak
- X-Context-Token header: Context token from Identity Management

### Authentication Flow

1. User enters email address
2. System sends 6-character alphanumeric OTP code
3. User enters code or clicks magic link
4. Keycloak validates and issues JWT tokens
5. App fetches available contexts via Identity Management API
6. User selects context (or auto-selects if only one)
7. App requests Context Token for selected context
8. All subsequent API calls include both tokens

## Multi-Tenancy Architecture

**Hierarchical Structure:**

Tenant (Customer Account) - All data belongs to a tenant
- Organization (Business Unit) - Department or branch within tenant
- Division (Team/Department) - Team or unit within organization

Users can belong to multiple tenants with different roles in each.

**Data Isolation Enforcement:**
- Every entity inherits from TenantEntity which includes TenantId, OrganisationId, DivisionId
- Global query filters in EF Core automatically filter by tenant context
- AuditStampingInterceptor automatically populates tenant fields on save
- TenantAuthMiddleware validates Context Token and populates IAppContext
- All queries automatically filter to user's current context

**Context Token Contents:**
- tenant_id, organisation_id, division_id
- user_id, session_id
- roles (array)
- app_permissions (JSON)
- Expiration time

## Communication Patterns

### Synchronous (HTTP)
- Frontend to Backend via ingress routing
- Service-to-service via Kubernetes DNS for internal endpoints
- Internal endpoints on /internal/v1/* paths
- Context token propagation via X-Context-Token header

### Asynchronous (Events)
- RabbitMQ for message transport
- Each service has its own exchange
- Consumers subscribe to relevant events
- Domain events for eventual consistency

### Real-time
- SignalR for live updates and notifications
- WebSocket connections from frontend to notification-backend
- Endpoint: /hubs/notifications

## Data Stores

| Store | Type | Purpose |
|-------|------|---------|
| PostgreSQL | RDBMS | Primary data store for all services (each service has own database) |
| Redis | Cache | Distributed caching, rate limiting |
| RabbitMQ | Queue | Message queue for async operations |
| MongoDB | Document | Notification service data storage |

**PostgreSQL Databases (per service):**
- hrdb2000 - HR service
- assetdb2000 - Asset service
- identitydb100 - Identity service
- keycloak - Keycloak data

## Frontend Architecture

**Distributed Microfrontend Architecture:**
- Each microfrontend is an autonomous application
- No central shell/host - each MF can run standalone
- Navbar is shared via Module Federation
- Each MF handles its own authentication via Keycloak

**Technology Stack:**
- Framework: Modern.js v2 + Rspack
- Module Federation: @module-federation/enhanced
- UI Framework: HeroUI + Tailwind CSS
- State Management: Jotai
- Data Fetching: React Query, urql (GraphQL)
- Forms: TanStack Form + Zod validation
- Auth: react-oidc-context
- Real-time: SignalR
- Testing: Playwright

**Shared Dependencies (Singleton via Module Federation):**
- react, react-dom
- @brainforgeau/security (CRITICAL - must be eager singleton)
- jotai
- @heroui/react
- framer-motion

## Service Routing

**Primary Domain (app.brainforge.com.au):**
- / - Main frontend application
- /hr - HR microfrontend
- /asset - Asset management microfrontend
- /identity - Identity management microfrontend
- /inventory - Inventory microfrontend
- /tracking - GPS tracking microfrontend
- /drivecom - DriveCOM microfrontend
- /onboard - Onboarding application
- /backend - HR API
- /backend/asset - Asset API
- /backend/tracking - Tracking API
- /backend/inventory - Inventory API
- /backend/notification - Notification API
- /hubs/notifications - SignalR WebSocket
- /hubs/tracking - Tracking SignalR WebSocket
- /public - Public API (API key authentication)
- /mfs/packages/navbar - Shared navigation

**Auth Domain (auth.brainforge.com.au):**
- /realms - Keycloak OIDC token endpoint
- /resources - Keycloak resources
- /identity - Identity Management API

## External Integrations

| Integration | Purpose | Method |
|-------------|---------|--------|
| Keycloak | Identity Provider (OIDC) | OAuth 2.0 / OpenID Connect |
| Grafana | Dashboards & visualization | HTTP |
| Prometheus | Metrics collection | Scrape endpoints |
| Loki | Log aggregation | HTTP push |
| Tempo | Distributed tracing | OTLP export |

## Infrastructure Overview

**Platform:** Kubernetes managed via Flux CD GitOps

**Observability Stack:**
- Prometheus + Grafana for metrics and dashboards
- Loki for log aggregation
- Tempo for distributed tracing
- OpenTelemetry for instrumentation

## API Gateway

The API Gateway provides secure external access for third-party integrations:
- Uses API key authentication (not JWT)
- Routes requests to appropriate backend services
- Enforces rate limiting per API key
- Generates Context Token for external requests based on API key's tenant

**API Key Features:**
- Scopes control what operations a key can perform
- Rate limits: requests per minute, per hour, burst limits
- Keys associated with specific tenant

## Architectural Decisions (ADRs)

### ADR-001: Centralized Identity and Authorization
- **Decision:** All identity, tenancy, and permission logic centralized in identity-management
- **Rationale:** Avoid duplication, single security posture, consistent claims

### ADR-002: Two-Stage Authentication
- **Stage 1:** Keycloak JWT for user identity (via OIDC with email OTP)
- **Stage 2:** Context token for tenant hierarchy and permissions (issued by identity-management)

### ADR-003: Shared Package Architecture
- **Decision:** Common patterns extracted to dotnet-core (backend) and mf-packages (frontend)
- **Rationale:** Consistency, faster onboarding, centralized security fixes

### ADR-004: GitOps with Flux CD
- **Decision:** All infrastructure as code managed via Git with Flux reconciliation
- **Rationale:** Auditability, reproducibility, declarative infrastructure

### ADR-005: Distributed Microfrontend Architecture
- **Decision:** Each microfrontend is autonomous, sharing only navbar via Module Federation
- **Rationale:** Independent deployment, standalone development capability, reduced coupling

## References

- Architecture diagrams: docs/confluence/netcorp-backbone-architecture.md
- Identity management: docs/confluence/identity-management.md
- Permission management: docs/confluence/permission-management.md
- Tenancy management: docs/confluence/tenancy-management.md
- Observability: docs/confluence/observability-management.md
- Storage: docs/confluence/storage-management.md
- Technical overview: docs/confluence/EAHT/netcorp360/technical-overview/content.md
- Multi-tenancy: docs/confluence/EAHT/netcorp360/technical-overview/multi-tenancy/content.md
- Authentication: docs/confluence/EAHT/netcorp360/technical-overview/core-platform/authentication-and-authorization/content.md
