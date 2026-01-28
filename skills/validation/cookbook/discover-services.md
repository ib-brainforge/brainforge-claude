# Recipe: Discover Services

How to discover and classify services in a repository structure.

## Tool

`tools/discover-services.py`

## Input

- `--root`: Repository root path
- `--output`: Output JSON file path

## Logic

1. Scan root directory for subdirectories
2. Classify each by type:
   - **frontend**: Has `package.json` with React/Vue/Angular
   - **backend**: Has `.csproj`, `go.mod`, `requirements.txt`
   - **shared**: Name contains "core", "common", "shared"
   - **infrastructure**: Has `terraform/`, `kubernetes/`, `Dockerfile`

3. Extract metadata:
   - Service name
   - Tech stack
   - Dependencies
   - Last modified

## Output Format

```json
{
  "services": [
    {
      "name": "user-service",
      "path": "/path/to/user-service",
      "type": "backend",
      "tech": "dotnet",
      "dependencies": ["Core.Common", "Core.Data"]
    }
  ],
  "summary": {
    "total": 40,
    "frontend": 10,
    "backend": 25,
    "shared": 3,
    "infrastructure": 2
  }
}
```

## Customization

To change classification rules, modify `detect_service_type()` in the tool.

The tool is domain-agnostic - it detects by file patterns, not by naming conventions specific to your project.
