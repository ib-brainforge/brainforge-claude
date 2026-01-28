# Jira Configuration

Configuration for Jira integration with the NetCorp360 multi-agent system.

---

## Atlassian Instance

| Setting | Value | Source |
|---------|-------|--------|
| Site Name | netcorpgps | Verified from Confluence space |
| Base URL | netcorpgps.atlassian.net | Verified from Confluence space |
| Confluence Space Key | EAHT | Verified from docs/confluence/EAHT/_space.json |
| Confluence Space Name | Dev Knowledgebase | Verified from docs/confluence/EAHT/_space.json |

**Note**: The Jira project key should be verified directly from Jira. The Confluence space key (EAHT) may or may not match the Jira project key.

---

## Authentication

Authentication requires three environment variables. Set these before using Jira integration:

| Variable | Description |
|----------|-------------|
| JIRA_URL | Base URL (netcorpgps.atlassian.net) |
| JIRA_USER | Atlassian account email |
| JIRA_API_TOKEN | Personal API token from Atlassian |

Alternative variable names supported: ATLASSIAN_SITE_NAME, ATLASSIAN_USER_EMAIL, ATLASSIAN_API_TOKEN.

To generate an API token, visit the Atlassian account security page at id.atlassian.com and create a new token under "API tokens".

---

## Product Information

| Property | Value | Source |
|----------|-------|--------|
| Product Name | NetCorp360 | Verified from Confluence documentation |
| Description | Modular enterprise platform with multiple business applications | Verified from Confluence |

### Business Applications (Verified from Confluence)

| Application | Description | Repository Prefix |
|-------------|-------------|-------------------|
| HR Management | Human resources, timesheets, scheduling, payroll, leave tracking | hr-* |
| Asset Management (NAMS) | Asset lifecycle, work orders, maintenance, disposals | asset-* |
| DriveCom | Driver communication and fleet management | drivecom-* |
| Inventory | Stock management and inventory control | inventory-* |
| Identity (Foundation) | Authentication, authorization, user management | identity-* |
| LMS (Brightmind) | Learning management system | lms-* |

---

## Repository to Component Mapping

Maps repository names to logical components. All repositories verified to exist in the bf-github workspace.

### Frontend Microfrontends

| Repository | Component Name |
|------------|----------------|
| hr-mf | HR Frontend |
| asset-mf | Asset Frontend |
| identity-mf | Identity Frontend |
| inventory-mf | Inventory Frontend |
| drivecom-mf | DriveCom Frontend |
| navbar-mf | Navigation |
| lms-mf | LMS Frontend |
| common-mf | Common Frontend |
| onboard-mf | Onboarding Frontend |

### Backend Services

| Repository | Component Name |
|------------|----------------|
| hr-backend | HR Backend |
| asset-backend | Asset Backend |
| identity-management | Identity Management |
| inventory-backend | Inventory Backend |
| lms-backend | LMS Backend |
| notification-backend | Notifications |
| common-backend | Common Backend |
| onboard-backend | Onboarding Backend |

### Applications

| Repository | Component Name |
|------------|----------------|
| app | Main Web Application |
| onboard-app | Onboarding Mobile App |
| public-website | Public Website |
| netcorp-public-website | NetCorp Public Website |
| public-website-strapi | Public Website CMS |

### Core and Infrastructure

| Repository | Component Name |
|------------|----------------|
| dotnet-core | .NET Core Libraries |
| mf-packages | Frontend Shared Packages |
| api-gateway | API Gateway |
| infra | Infrastructure |
| aspire | Aspire Orchestration |
| auth | Authentication Service |

---

## Jira REST API Endpoints

Standard Jira Cloud REST API v3 endpoints used by the integration:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /rest/api/3/myself | GET | Verify connection, get current user |
| /rest/api/3/issue/{key} | GET | Fetch issue details |
| /rest/api/3/issue/{key}/transitions | GET | Get available status transitions |
| /rest/api/3/issue/{key}/transitions | POST | Execute a status transition |
| /rest/api/3/issue/{key}/comment | POST | Add comment to issue |
| /rest/api/3/issue/{key}/remotelink | POST | Add link to commit or PR |
| /rest/api/3/project/search | GET | List available projects |

---

## Ticket Type to Commit Convention Mapping

Maps Jira issue types to conventional commit prefixes. These should be verified against your actual Jira configuration.

| Jira Issue Type | Commit Prefix | Description |
|-----------------|---------------|-------------|
| Bug | fix | Bug fixes |
| Story | feat | New features |
| Task | chore | Maintenance tasks |
| Improvement | feat | Feature improvements |

---

## Configuration Notes

### What Needs Verification

The following should be verified directly from your Jira instance:

1. **Jira Project Key** - May differ from Confluence space key (EAHT)
2. **Workflow Statuses** - Actual status names in your Jira workflow
3. **Available Transitions** - Depends on your project's workflow configuration
4. **Custom Fields** - Any project-specific custom fields
5. **Issue Types** - Verify against your project's scheme

### To Verify Configuration

Run this command to test the connection and fetch project details:

Test connection by calling the /rest/api/3/myself endpoint with authentication.

List projects by calling the /rest/api/3/project/search endpoint.

Fetch a sample issue to see actual workflow statuses by calling /rest/api/3/issue/{key} with expand=transitions parameter.

---

## Related Documentation

- Jira Integration Skill: .claude/skills/jira-integration/SKILL.md
- Commit Conventions: .claude/knowledge/commit-conventions.md
- Confluence Documentation: docs/confluence/EAHT/
