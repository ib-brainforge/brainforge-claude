# Recipe: Validate Structure

How to validate service directory structure.

## Tool

`tools/validate-structure.py`

## Input

- `--services`: JSON file from discover-services
- `--output`: Output JSON file path

## What It Checks

### Frontend Services

```
✓ package.json exists
✓ src/ directory exists
✓ tsconfig.json or jsconfig.json exists
✓ Has test files (*.test.*, *.spec.*)
✓ Has README.md
```

### Backend Services (.NET)

```
✓ *.csproj exists
✓ Program.cs or Startup.cs exists
✓ Has test project (*Tests.csproj)
✓ Has appsettings.json
✓ Has README.md
```

### Infrastructure

```
✓ Has main.tf or similar
✓ Has variables defined
✓ Has README.md
```

## Output Format

```json
{
  "results": [
    {
      "service": "user-service",
      "status": "PASS",
      "checks": [
        { "check": "has_csproj", "passed": true },
        { "check": "has_tests", "passed": true }
      ]
    },
    {
      "service": "legacy-service",
      "status": "WARN",
      "checks": [
        { "check": "has_readme", "passed": false, "severity": "warning" }
      ]
    }
  ]
}
```

## Customization

Structure expectations are generic. For project-specific requirements, the tool reads from `knowledge/architecture/system-architecture.md` if additional rules are defined there.

## Severity Levels

| Severity | Meaning |
|----------|---------|
| error | Must fix, blocks validation |
| warning | Should fix, doesn't block |
| info | Nice to have |
