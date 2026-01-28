# Recipe: Validate Mode

## Purpose

Validate existing code against established design patterns and detect anti-patterns.

## Process

1. **Detect Tech Stack**
   ```bash
   python tools/detect-stack.py \
     --target "$TARGET" \
     --output /tmp/stack-info.json
   ```

2. **Spawn Design Pattern Advisor**
   ```
   Task: spawn design-pattern-advisor
   Prompt: |
     Validate design patterns in: $TARGET
     Tech stack: [from detection]
     Strict mode: $STRICT

     Check:
     - Pattern compliance (knowledge/architecture/design-patterns.md)
     - Core component usage (knowledge/packages/core-packages.md)
     - Anti-patterns (knowledge/validation/backend-patterns.md)

     Return detailed report with locations and suggestions.
   ```

3. **Generate Report**
   ```bash
   python tools/generate-report.py \
     --validation /tmp/validation-result.json \
     --format markdown \
     --output "$OUTPUT_DIR/pattern-report.md"
   ```

## Checks Performed

| Check | Source | Severity |
|-------|--------|----------|
| Pattern compliance | knowledge/architecture/design-patterns.md | Error/Warning |
| Core component usage | knowledge/packages/core-packages.md | Warning |
| Anti-pattern detection | knowledge/validation/backend-patterns.md | Error |

## Output

Generates compliance report with:
- Pattern compliance score
- Core component usage score
- Anti-pattern free score
- Specific violations with locations
- Recommendations for fixing
