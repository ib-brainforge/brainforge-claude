# Recipe: Suggest Mode

## Purpose

Recommend appropriate design patterns for new features based on requirements.

## Process

1. **Parse Feature Description**
   ```bash
   python tools/parse-feature.py \
     --description "$TARGET" \
     --output /tmp/feature-keywords.json
   ```

2. **Spawn Design Pattern Advisor**
   ```
   Task: spawn design-pattern-advisor
   Prompt: |
     Suggest patterns for feature: $TARGET
     Keywords: [from parsing]
     Mode: suggest

     Using knowledge from:
     - knowledge/architecture/design-patterns.md
     - knowledge/packages/core-packages.md
     - knowledge/validation/backend-patterns.md

     Provide:
     - Recommended patterns with rationale
     - Core components to use
     - Code examples for your stack
     - Common pitfalls to avoid
   ```

3. **Output Recommendations**

## Pattern Matching

See `cookbook/pattern-matching.md` for feature-to-pattern mapping rules.

## Output Format

```json
{
  "recommendations": [
    {
      "pattern": "Pattern Name",
      "rationale": "Why this pattern fits",
      "frontend": {
        "components": ["@core/ui/..."],
        "hooks": ["@core/hooks/..."],
        "example": "..."
      },
      "backend": {
        "services": ["Core.*.I..."],
        "pattern": "...",
        "example": "..."
      },
      "pitfalls": [...]
    }
  ]
}
```
