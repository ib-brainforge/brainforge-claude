# Recipe: Pattern Matching

## Purpose

Map feature keywords to recommended design patterns.

## Keyword-to-Pattern Mapping

This is the domain-agnostic matching logic. Actual patterns are defined in
`knowledge/architecture/design-patterns.md`.

### Frontend Patterns

| Keywords | Pattern Category | Notes |
|----------|------------------|-------|
| list, table, grid, data | DataGrid | Pagination, sorting, filtering |
| form, input, validation | Form | Validation, submission, errors |
| login, auth, session | Auth Flow | Login, logout, session management |
| upload, file, image | File Upload | Progress, chunking, preview |
| search, filter | Search | Debounce, suggestions, results |
| modal, dialog, popup | Modal | Focus trap, backdrop, animations |
| notification, toast, alert | Toast | Queue, duration, actions |
| real-time, live, websocket | WebSocket | Connection, reconnect, state sync |
| wizard, stepper, multi-step | Wizard | Steps, validation, navigation |
| infinite, scroll, lazy | Infinite Scroll | Load more, placeholder, viewport |

### Backend Patterns

| Keywords | Pattern Category | Notes |
|----------|------------------|-------|
| crud, create, update, delete | Repository + CQRS | Separate read/write models |
| query, filter, search | Specification | Composable query building |
| event, async, publish | Domain Events | Event-driven architecture |
| cache, performance | Caching | Read-through, invalidation |
| batch, bulk, import | Batch Processing | Chunking, progress, retry |
| auth, permission, role | Authorization | Claims, policies, guards |
| file, storage, blob | File Storage | Streaming, chunking |
| external, integration, api | Anti-Corruption Layer | Adapters, mapping |

## Matching Algorithm

1. Extract keywords from feature description
2. Normalize (lowercase, stem)
3. Match against keyword tables
4. Return patterns with confidence scores
5. Include related patterns (e.g., Form often needs Validation)

## Confidence Scoring

- **High (>0.8)**: Multiple keyword matches
- **Medium (0.5-0.8)**: Single keyword match
- **Low (<0.5)**: Inferred from context
