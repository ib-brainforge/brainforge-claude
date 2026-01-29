# Frontend Validation Patterns

<!--
PROJECT-SPECIFIC: Frontend validation patterns for BrainForge platform.
This is referenced by: frontend-pattern-validator
Last verified: 2026-01-27
Source: Verified against hr-mf, asset-mf, identity-mf, inventory-mf, common-mf, drivecom-mf, navbar-mf, mf-packages repositories
-->

---

## UI Design Language (CRITICAL)

**The BrainForge UI follows the JIRA Design Language.** All UI changes must adhere to this design system to maintain consistency across the platform.

### Component Library Priority

**ALWAYS prefer @brainforgeau/components over direct HeroUI usage.**

| Priority | Library | When to Use |
|----------|---------|-------------|
| 1st | @brainforgeau/components | All primary UI components (buttons, inputs, modals, tables, etc.) |
| 2nd | @heroui/react | Only for utilities (addToast, theming) or components not yet wrapped |

The @brainforgeau/components library wraps HeroUI with BrainForge-specific styling that follows the JIRA design language. Using raw HeroUI components breaks visual consistency.

### Mandatory Component Usage

**Always use these @brainforgeau/components instead of HeroUI equivalents:**

| Use This (@brainforgeau/components) | NOT This (@heroui/react) |
|-------------------------------------|--------------------------|
| BaseButton | Button |
| BaseInput | Input |
| BaseSelect, BaseSelectItem | Select, SelectItem |
| BaseCheckbox, BaseCheckboxGroup | Checkbox, CheckboxGroup |
| BaseModal, BaseModalHeader, BaseModalBody, BaseModalFooter | Modal (direct) |
| BaseTable with TablePagination | Custom table implementations |
| BaseDatePicker | DatePicker |
| BaseAutocomplete | Autocomplete |
| BaseTextarea | Textarea |
| Icon (125+ icons) | @heroicons/react (for custom icons only) |
| PageSpinner | Spinner |
| BaseBreadcrumbs | Breadcrumbs |

### Acceptable Direct HeroUI Usage

These HeroUI components may be used directly (no @brainforgeau wrapper exists):

- addToast (notification utility)
- Alert (for inline alerts - use ValidationAlert for form errors)
- HeroUIProvider, ToastProvider (provider wrappers)
- Popover (when BaseSelect does not fit)

### Design System Colors

The BrainForge design system defines specific colors that must be used consistently:

**Primary Colors:**
- Primary Blue: #1868db (main actions, links)
- Primary Blue Hover: #4688ec
- Primary Blue Light: #cce0ff (backgrounds)

**Gray Scale:**
- Standard Gray: #59636e (body text)
- Light Gray: #8c8f97 (secondary text)
- Dark Gray: #505258 (headings)
- Border Gray: #d1d9e0 (borders, dividers)
- Background Gray: #f5f5f5 (light backgrounds)

**Status Colors:**
- Danger/Error: #f15050, dark: #ae2e24
- Success: #6a9a23, dark: #216e4e
- Warning: #7f5f01, soft: #f8e6a0
- Purple (accent): #bf63f3, dark: #943073, light: #dfd8fd

**Dark Mode:**
- Dark Background: #292a2e
- Dark mode is fully supported via class-based strategy

### Typography

- Font Family: Inter (primary), Arial, system fallbacks
- Use Tailwind text utilities: text-xs, text-sm, text-base, text-3xl
- Bold/semibold for labels and important text
- Font sizes adapt across components (xs for small inputs/labels, sm for content)

### Spacing and Border Conventions

- Border Radius: rounded-[3px] is standard (3px) for most components
- Input Padding: px-2.5 py-1.75 for form inputs
- Header Padding: px-5 py-2.75 for headers/sections
- Gap/Spacing: gap-2.5 and gap-1 for component separation
- Border Style: border-light as default, border-blue for focused/active, border-danger for errors

### Component Styling States

- Focus: focus-within:border-blue-2
- Hover: hover:bg-light-blue or hover:bg-light-2
- Error: danger color (red) with outline offset styling
- Disabled: opacity reduction and cursor-not-allowed
- Dark mode: Use .dark: prefix for dark mode variants

---

## Architecture Overview

BrainForge uses a distributed microfrontend architecture where each module is an autonomous application. There is no central shell - each microfrontend can run standalone with only the navbar shared via Module Federation. Each microfrontend handles its own authentication via Keycloak.

### Active Microfrontends

| Microfrontend | Repository | Port | Description |
|---------------|------------|------|-------------|
| HR | hr-mf | 8081 | Employee, scheduling, timesheet management |
| Asset Management | asset-mf | 8082 | Vehicle and equipment management |
| Identity | identity-mf | 8090 | User, role, permission management |
| Inventory | inventory-mf | - | Stock and inventory management |
| DriveCom | drivecom-mf | - | Driver communication features |
| Navbar | navbar-mf | 3001 | Shared navigation component (provider) |
| Common | common-mf | - | Shared common features |
| Onboard | onboard-app | - | Employee onboarding flow |

---

## Framework Detection

All BrainForge frontend microfrontends use React 18 with Modern.js:

| Framework | package.json Dependency | Config File |
|-----------|------------------------|-------------|
| React 18 | react: 18.3.1 (strict) | - |
| Modern.js | @modern-js/app-tools: 2.68.9 | modern.config.ts |

## Build System

| Tool | Config File | Purpose |
|------|-------------|---------|
| Modern.js | modern.config.ts | Build, dev server, and bundling via Rspack |
| Module Federation | module-federation.config.ts | Microfrontend architecture |
| PostCSS | postcss.config.mjs | CSS processing with @tailwindcss/postcss |
| TypeScript | tsconfig.json | Type checking |
| Biome | biome.json | Linting and formatting |

Note: navbar-mf uses Webpack directly instead of Modern.js due to specific build requirements.

---

## Component Structure

Microfrontends follow a feature-based organization pattern:

### Directory Organization

| Directory | Purpose |
|-----------|---------|
| src/components/[feature]/ | Feature-based component folders |
| src/components/[feature]/components/ | UI components for the feature |
| src/components/[feature]/hooks/ | Feature-specific hooks |
| src/components/[feature]/state/ | Jotai atoms for the feature |
| src/components/[feature]/shared/ | API services, types, utilities for the feature |
| src/components/shared/ | Global shared components |
| src/state/ | App-level state (config, API clients) |
| src/hooks/ | Global shared hooks |
| src/providers/ | React context providers |
| src/routes/ | File-based routing (Modern.js) |
| src/constants/ | Global constants and enums |
| src/utils/ | Utility functions |
| src/observability/ | Logging and monitoring setup |

### Provider Structure

All microfrontends use these core providers (wrapped at app root):

| Provider | Package | Purpose |
|----------|---------|---------|
| ObservabilityProvider | @brainforgeau/observability | Logging, tracing setup |
| AuthProvider | @brainforgeau/security | Authentication context |
| HeroProvider | local wrapper | HeroUIProvider + ToastProvider with routing integration |
| QueryProvider | local wrapper | TanStack Query client setup with Jotai hydration |
| SignalRProvider | local (hr-mf only) | Real-time communication |
| TenantAppSettingsProvider | local (asset-mf only) | Tenant-specific settings |

---

## State Management

### Jotai (Primary Client State)

| Pattern | Description |
|---------|-------------|
| Simple atoms | Basic state using atom with initial value |
| Derived atoms | Computed state with read/write functions |
| atomWithDebounce | Custom factory for debounced input values |
| atomWithQuery | Integration with TanStack Query (from jotai-tanstack-query) |
| atomWithMutation | Mutation integration with TanStack Query |
| queryClientAtom | Shared QueryClient instance via Jotai |

State files are organized in [feature]/state/ directories with common patterns:
- state.ts for main atoms
- filter-state.ts for filter-related atoms
- [entity]-dropdown-state.ts for dropdown options

Note: atomWithObservable is NOT used in this codebase.

### TanStack Query (Server State)

| Pattern | Description |
|---------|-------------|
| Query keys | Hierarchical arrays with context: ['entity-type', contextKey, ...filters] |
| Context-aware queries | All queries include context key built from selectedContextAtom |
| Query invalidation | Targeted invalidation after mutations via queryClient.invalidateQueries |
| Default configuration | staleTime 30s, retry 1 for queries, retry 0 for mutations |

QueryClient is hydrated into Jotai using useHydrateAtoms and invalidated automatically on context token changes.

---

## UI Component Library

### HeroUI (Base Components)

All microfrontends use HeroUI v2.8.2 as the base component library. Components are wrapped with HeroUIProvider and ToastProvider.

Common HeroUI components used: Button, Modal, Input, Select, Popover, Pagination, Progress, RadioGroup, Checkbox, Accordion, Link, Spinner, Dropdown, Card, Switch, Drawer.

### @brainforgeau/components (Extended Components)

Shared component library that extends HeroUI using extendVariants. All components use "Base" prefix.

| Component | Description |
|-----------|-------------|
| BaseButton | Extended button with variants |
| BaseInput | Extended input with validation support |
| BaseTextarea | Extended textarea |
| BaseSelect / BaseSelectItem | Extended select with items |
| BaseCheckbox / BaseCheckboxGroup | Extended checkbox controls |
| BaseRadio / BaseRadioGroup | Extended radio controls |
| BaseToggle | Switch wrapper component |
| BaseNumberInput | Numeric input control |
| BaseFilterSelect | Filter-specific select |
| BaseModal / BaseModalContent / BaseModalHeader / BaseModalBody / BaseModalFooter | Modal components |
| BaseAccordion | Collapsible content |
| BaseTable | TanStack React Table wrapper |
| TablePagination | Pagination for tables |
| BaseDatePicker | Date selection |
| BaseWeekPicker | Week selection |
| BaseTimeInput | Time input |
| BaseAutocomplete | Autocomplete input |
| BaseBreadcrumbs | Navigation breadcrumbs |
| BaseAvatar | User avatar with initials fallback |
| BaseStatusSelect | Status badge dropdown |
| SideNav / SideNavDesktopMode / SideNavMobile | Navigation sidebar |
| PageSpinner | Full-page loading spinner |
| ErrorBoundary | React error boundary |
| Icon | Icon library wrapper (125+ icons) |
| DonutChart / BarChart / TabbedBarChart | Chart components |
| NotificationPanel / NotificationBell | Notification UI |

Note: @brainforgeau/components is NOT shared via Module Federation due to Webpack/Rspack SVG transformation incompatibilities. Each microfrontend bundles its own copy.

---

## Styling

### Tailwind CSS v4

| Configuration | Details |
|---------------|---------|
| Version | 4.1.13+ |
| PostCSS | @tailwindcss/postcss ^4.1.12 |
| Dark mode | class-based |
| Custom prefix | "bf" in components package |

### tailwind-variants

Used for slot-based styling in complex components (tv function). Applied to: TableLoading, PageSpinner, BaseCheckbox, BaseRadio.

Note: tailwind-merge (twMerge) is NOT used. Class merging is done via manual string concatenation.

Note: @brainforgeau/tailwind-config shared package exists but is NOT actively imported. Each microfrontend has its own Tailwind configuration.

### Framer Motion

Limited usage for modal animations only. Enter/exit transitions with easeOut/easeIn timing.

---

## API Client Patterns

### Authorized Axios

All API calls use authorizedAxios from @brainforgeau/security:
- Automatically attaches Keycloak JWT (Authorization header)
- Automatically attaches Context Token (X-Context-Token header)
- Adds X-Session-Id and request-id headers for observability
- Proactive token refresh (access token at 30s buffer, context token at 60s buffer)
- Handles 401 (access token refresh) and 419 (context token refresh) errors

### Generated API Clients

OpenAPI-generated clients with type-safe factory functions:

| Package | Purpose |
|---------|---------|
| @brainforgeau/hr-backend-client | HR API operations |
| @brainforgeau/asset-backend-client | Asset API operations |
| @brainforgeau/identity-management-client | Identity/auth API operations |
| @brainforgeau/inventory-backend-client | Inventory API operations |
| @brainforgeau/learning-backend-client | LMS API operations |

Factory pattern: createHrBackendApiClient, createLearningApiClient, etc. Accept API class constructor and return configured client using authorizedAxios.

Note: createCrossAppAxios is NOT used in this codebase.

---

## Authentication

### Two-Token System

| Token | Purpose | Header |
|-------|---------|--------|
| Access Token | Keycloak JWT for user identity | Authorization: Bearer |
| Context Token | Tenant/organization/division context | X-Context-Token |

### Authentication State Machine

| State | Description |
|-------|-------------|
| initializing | OIDC library loading |
| validating | Token validation in progress |
| loading-context | Fetching contexts and issuing context token |
| ready | Fully authenticated with context |
| unauthenticated | No user session |
| error | Authentication failed |

### Provider Modes

| Mode | Description |
|------|-------------|
| shell | Full OIDC provider + AuthContextProvider |
| microfrontend | AuthContextProvider only (relies on shell for OIDC) |

FlexibleAuthProvider determines mode automatically based on isMicrofrontend prop.

### Context Token Management

- Contexts represent tenant/organization/division hierarchy
- Selected context persisted to localStorage with key 'bf:selected-context-id'
- Format: tenantId:organisationId:divisionId (uses 'none' for null values)
- Cross-microfrontend sync via CONTEXT_TOKEN_CHANGED_EVENT custom event

### useAuth Hook Returns

| Property | Description |
|----------|-------------|
| status | Current auth state |
| user | OIDC user object |
| token | Access token |
| isAuthenticated | Boolean auth status |
| isLoading | Loading state |
| requestSignIn | Trigger login |
| requestSignOut | Trigger logout |

### useContextToken Hook Returns

| Property | Description |
|----------|-------------|
| contextToken | Current context token |
| contexts | Available contexts (tenants/orgs/divisions) |
| selectedContext | Currently selected context |
| selectContext | Function to change context |
| issueTokenForContext | Function to issue new token |

---

## Permissions

### usePermissions Hook

Extracts permissions from multiple JWT sources (profile, ID token, access token, context token).

| Method | Logic |
|--------|-------|
| hasPermission | Check single permission (OR) |
| hasAnyPermission | Check if user has ANY listed permission (OR) |
| hasAllPermissions | Check if user has ALL listed permissions (AND) |
| hasRole | Check single role |
| hasAnyRole | Check ANY role (OR) |
| hasAllRoles | Check ALL roles (AND) |

### PermissionGuard Component

Conditional rendering based on permissions.

| Prop | Description |
|------|-------------|
| requiredPermissions | Permissions needed (OR by default) |
| requiredRoles | Roles needed (OR by default) |
| requireAll | If true, ALL permissions required (AND) |
| requireAllRoles | If true, ALL roles required (AND) |
| fallback | Component to render if denied |

Security note: Roles are only extracted from Keycloak tokens, not context tokens, to prevent injection attacks.

---

## Form Handling

### TanStack Form + Zod

| Pattern | Description |
|---------|-------------|
| useForm hook | Form state management with validation |
| zodValidator | Adapter from @tanstack/zod-form-adapter |
| z.object schemas | Field structure and validation rules |
| form.Field | Individual field components |
| form.setFieldValue | Programmatic value manipulation |

Forms configured with: defaultValues, validators (onChange), onSubmit handler.

---

## Observability

### @brainforgeau/observability Package

| Feature | Description |
|---------|-------------|
| X-Session-Id | UUID v4 per browser session (sessionStorage) |
| request-id | UUID v4 per HTTP request |
| traceparent/tracestate | W3C trace context headers |
| OpenTelemetry | OTLP exporter for trace collection |

### Hooks Available

useObservability, useLogger, useTracer, useMetrics, useTracker

Session ID is rotated after authentication and cleared on logout.

---

## Real-Time Communication

### SignalR (HR-MF only)

| Configuration | Details |
|---------------|---------|
| Package | @microsoft/signalr |
| Hub | /hubs/award-processing |
| Authentication | Tokens via query string (WebSocket limitation) |
| Reconnection | Exponential backoff up to 32s delay |

Connection reconnects automatically when tokens are refreshed via ACCESS_TOKEN_REFRESH_EVENT and CONTEXT_TOKEN_REFRESH_EVENT.

---

## Module Federation

### Configuration Files

| Microfrontend | Config File |
|---------------|-------------|
| Most MFs | module-federation.config.ts |
| navbar-mf | webpack.config.ts (uses Webpack directly) |

### Shared Dependencies (Singleton)

| Package | Eager | Notes |
|---------|-------|-------|
| react | Yes | v18.3.1 strict |
| react-dom | Yes | v18.3.1 strict |
| @brainforgeau/security | Yes | CRITICAL - must be eager singleton |
| jotai | No | Singleton for state sharing |
| @heroui/react | No | Singleton for UI consistency |
| @heroicons/react | No | Singleton |
| framer-motion | No | Singleton |

### Remote Configuration

All consumer microfrontends import navbar as remote:
- Remote name: @brainforgeau/navbar
- Entry point: {MF_NAVBAR_URL}/remoteEntry.js

navbar-mf exposes: root export (.) and ./Navbar

### Type Generation

- Consumers: consumeTypes with maxRetries=3
- Providers: generateTypes

---

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.3.1 | UI framework |
| @modern-js/app-tools | 2.68.9 | Build system |
| @module-federation/enhanced | 0.21.4 | Module Federation |
| jotai | 2.13.1 | State management |
| jotai-tanstack-query | - | Query/mutation atoms |
| @tanstack/react-query | 5.89.0 | Server state |
| @tanstack/react-form | 1.23.0 | Form handling |
| zod | 3.25.76 | Schema validation |
| @heroui/react | 2.8.2 | UI components |
| tailwindcss | 4.1.13 | CSS framework |
| axios | 1.7.9 - 1.13.2 | HTTP client (version varies) |
| react-oidc-context | 3.3.0 | OIDC authentication |
| framer-motion | 12.23.12 | Animations |
| @tanstack/react-table | 8.21.3 | Table management |
| date-fns | 4.1.0 | Date utilities (hr-mf only) |
| @microsoft/signalr | 8.0.0 | Real-time (hr-mf only) |
| urql | 5.0.1 | GraphQL client |

## Shared Packages (@brainforgeau/*)

| Package | Purpose |
|---------|---------|
| @brainforgeau/components | Extended UI component library |
| @brainforgeau/security | Authentication, authorization, axios utilities |
| @brainforgeau/observability | Logging, tracing, metrics |
| @brainforgeau/theme | Global CSS theme |
| @brainforgeau/federation-types | Module Federation type definitions |
| @brainforgeau/*-backend-client | OpenAPI-generated API clients |

---

## Anti-Patterns to Detect

### UI Component Anti-Patterns (CRITICAL)

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| Using @heroui/react Button instead of BaseButton | error | Import BaseButton from @brainforgeau/components |
| Using @heroui/react Input instead of BaseInput | error | Import BaseInput from @brainforgeau/components |
| Using @heroui/react Modal directly | error | Use BaseModal, BaseModalHeader, BaseModalBody, BaseModalFooter from @brainforgeau/components |
| Using @heroui/react Select instead of BaseSelect | error | Import BaseSelect, BaseSelectItem from @brainforgeau/components |
| Using @heroui/react Checkbox instead of BaseCheckbox | error | Import BaseCheckbox from @brainforgeau/components |
| Custom table implementations | warning | Use BaseTable with TablePagination from @brainforgeau/components |
| Inline styles instead of Tailwind classes | warning | Use Tailwind utility classes |
| Custom colors not from design system | warning | Use design system color tokens |
| Custom border radius values | info | Use rounded-[3px] standard |

### API Anti-Patterns

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| Direct fetch to external URLs | error | Use authorizedAxios from @brainforgeau/security |
| Raw axios import without security package | error | Use authorizedAxios |
| Hardcoded API URLs in code | warning | Use environment variables |
| Temporary/local API client classes | error | Must use generated clients from @brainforgeau/*-backend-client packages |
| Custom API classes duplicating backend endpoints | error | Wait for backend PR merge, client regeneration, then use generated client |
| REVIEW/TODO comments for temporary API implementations | error | Blocker - must resolve before merge |

### Generated API Client Workflow (CRITICAL)

All API calls must use the generated OpenAPI clients from brainforgeau backend-client packages. Creating temporary local API classes is not acceptable and will be flagged as a blocking issue.

**Required Workflow for New API Endpoints:**

When implementing a feature that requires new backend API endpoints:

1. Backend team implements the endpoint and merges PR to develop
2. CI/CD automatically regenerates the brainforgeau backend-client npm package from the OpenAPI specification
3. Wait for the new package version to be published to npm registry
4. Update the frontend package.json to reference the new client version
5. Import and use the generated API class from the package

**What to Look For:**

The validator should detect and flag any locally-defined API classes that should come from the generated client. This includes classes that mimic the generated client pattern, comments indicating temporary implementations, comments about waiting for client regeneration, and locally-defined DTO interfaces that mirror backend types.

**Why This Matters:**

Generated clients provide type safety that matches the actual backend contract. Manual API classes can drift from the real backend, leading to runtime errors. Temporary code often becomes permanent if not blocked at review time. The pattern validator cannot verify correctness of custom implementations.

**Validator Behavior:**

When temporary API implementations are detected, the validator must report this as a critical severity issue that blocks the PR. The guidance should direct the developer to either wait for the backend client package update or ensure the backend PR is merged first before proceeding with frontend work.

### State Anti-Patterns

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| useState for server data | warning | Use TanStack Query |
| Direct localStorage for auth data | error | Use session management from security package |
| Window global assignments | warning | Use Jotai state management |

### TypeScript Anti-Patterns

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| Explicit any type | warning | Use proper types |
| as any type assertion | warning | Fix underlying type issue |
| Excessive non-null assertions | info | Handle null cases properly |

### React Anti-Patterns

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| Array index as key | warning | Use stable unique ID |
| Inline object styles | info | Use Tailwind classes |
| useEffect with empty deps but external variables | warning | Add proper dependencies |

### Console Anti-Patterns

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| console.log in production code | warning | Remove or use observability logger |
| alert() calls | error | Use toast or modal |

### Security Anti-Patterns

| Anti-Pattern | Severity | Suggestion |
|--------------|----------|------------|
| Hardcoded API keys or secrets | error | Use environment variables |
| dangerouslySetInnerHTML | warning | Sanitize HTML or avoid |
| eval() usage | error | Never use eval |
