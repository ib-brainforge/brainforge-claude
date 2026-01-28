# Commit Conventions

<!--
PROJECT-SPECIFIC: Update with your commit message format.
This is referenced by: commit-manager
-->

## Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

## Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add OAuth2 login` |
| `fix` | Bug fix | `fix(cart): correct total calculation` |
| `chore` | Maintenance | `chore(deps): update dependencies` |
| `refactor` | Code restructuring | `refactor(api): simplify error handling` |
| `docs` | Documentation | `docs(readme): update setup instructions` |
| `test` | Tests | `test(user): add registration tests` |
| `style` | Formatting | `style: apply prettier formatting` |
| `perf` | Performance | `perf(query): add index for user lookup` |
| `ci` | CI/CD changes | `ci: add deploy workflow` |

## Scopes

<!-- Define your project's scopes -->

| Scope | Description |
|-------|-------------|
| `auth` | Authentication |
| `user` | User management |
| `order` | Order processing |
| `ui` | UI components |
| `api` | API layer |
| `deps` | Dependencies |
| `config` | Configuration |

## Rules

1. **Subject**: Imperative mood, no period, ≤72 chars
   - ✅ `add user registration`
   - ❌ `added user registration.`

2. **Body**: Explain what and why (not how)

3. **Footer**: Reference issues
   - `Closes #123`
   - `Refs #456`

## Examples

### Simple
```
feat(auth): add password reset flow
```

### With Body
```
fix(cart): correct total calculation

The total was not including tax for international orders.
This fix applies the correct tax rate based on shipping country.

Closes #234
```

### Breaking Change
```
feat(api)!: change user endpoint response format

BREAKING CHANGE: User endpoint now returns camelCase keys
instead of snake_case. Update all API clients.
```

## Auto-Detection Rules

Used by `commit-manager` to suggest commit type:

| File Pattern | Suggested Type |
|--------------|----------------|
| `*.test.*`, `*.spec.*` | `test` |
| `README*`, `docs/*` | `docs` |
| `package.json`, `*.csproj` | `chore` |
| `.github/*`, `Dockerfile` | `ci` |
| New files + functions | `feat` |
| Bug-related keywords | `fix` |
