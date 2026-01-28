# /update-dashboard Command

Create or update Grafana dashboards for service observability.

## Usage

```
/update-dashboard SERVICE_NAME
/update-dashboard --sync    # Update all dashboards
```

## Aliases / Trigger Phrases

- "create grafana dashboard for..."
- "update dashboard for..."
- "setup observability dashboard..."
- "sync grafana dashboards"

## Examples

```
/update-dashboard asset-backend
/update-dashboard hr-mf
/update-dashboard --sync
```

Or naturally:
```
User: "Create a Grafana dashboard for the new inventory-backend service"
User: "Update the dashboards to include the new tenant filters"
User: "Sync all our Grafana dashboards"
```

## What It Does

1. **Detects service type** (backend/.NET or frontend/MF)
2. **Generates dashboard JSON** with appropriate panels:
   - Backend: Request duration, rate, error rate, Prometheus metrics
   - Frontend: Page views, user actions, errors, Loki logs
3. **Adds standard panels**: Log volume, error logs, traces
4. **Saves to infrastructure repo**: `infrastructure/grafana/dashboards/`

## Workflow

```
/update-dashboard asset-backend
    │
    ▼
[main] Spawn grafana-dashboard-manager
    │
    ├──► Detect: asset-backend is .NET backend
    ├──► Load existing dashboard (if any)
    ├──► Generate panels for backend service
    ├──► Add Loki log panels with tenant filtering
    ├──► Add Tempo trace panels
    └──► Write: grafana-dashboard-asset-backend.json
```

## Dashboard Includes

### Backend Services
| Panel | Data Source |
|-------|-------------|
| Request Duration (P95) | Prometheus |
| Request Rate | Prometheus |
| Error Rate | Prometheus |
| Log Volume by Level | Loki |
| Error Logs | Loki |
| Traces Search | Tempo |
| Service Map | Tempo |

### Frontend Services
| Panel | Data Source |
|-------|-------------|
| Page Views | Loki |
| User Actions | Loki |
| User Errors | Loki |
| Web Vitals | Loki |
| Log Volume | Loki |
| Error Logs | Loki |

## Variables in Dashboard

All dashboards include these filter variables:
- `app` - Application name
- `env` - Environment (production/staging)
- `tenant_id` - Tenant filter
- `user_id` - User filter
- `organization_id` - Organization filter
- `division_id` - Division filter
- `level` - Log level filter
