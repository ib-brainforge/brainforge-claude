# Recipe: Discover Affected Services

## Purpose

Find all services, components, and infrastructure affected by a feature.

## Process

1. **Keyword Extraction**
   - Parse feature name and description
   - Extract domain terms (e.g., "auth", "user", "order")
   - Identify technical requirements (e.g., "real-time", "file upload")

2. **Service Scanning**
   - Scan `$REPOS_ROOT/services/` for matching service names
   - Check service manifests for capability tags
   - Map keywords to service domains

3. **Classification**
   - Frontend: Services with React/Vue/Angular code
   - Backend: Services with API endpoints
   - Shared: Core libraries that may need updates
   - Infrastructure: Deployment or config changes needed

## Tool Usage

```bash
python tools/feature-analysis.py discover \
  --feature "$FEATURE_NAME" \
  --description "$DESCRIPTION" \
  --repos-root $REPOS_ROOT \
  --output /tmp/affected-services.json
```

## Output Format

```json
{
  "affected_services": ["auth-service", "user-frontend"],
  "frontend_components": ["LoginForm", "ResetPassword"],
  "backend_endpoints": ["/api/auth/*"],
  "database_changes": true,
  "classification": {
    "frontend": ["user-frontend"],
    "backend": ["auth-service"],
    "shared": ["@core/auth"],
    "infra": ["auth-deployment"]
  }
}
```

## Knowledge Dependencies

- `knowledge/architecture/system-architecture.md` - Service map
- `knowledge/architecture/service-boundaries.md` - Service responsibilities
