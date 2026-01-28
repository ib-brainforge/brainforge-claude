# Recipe: Synthesize Implementation Plan

## Purpose

Combine all architectural inputs into a coherent implementation plan.

## Inputs Required

- Discovery results (affected services)
- Design pattern recommendations
- Master architect constraints
- Frontend analysis
- Backend analysis
- Core library impact
- Infrastructure needs

## Synthesis Process

1. **Dependency Mapping**
   - Build dependency graph from all inputs
   - Identify critical path
   - Flag circular dependencies

2. **Phase Generation**
   - Group tasks by dependency order
   - Each phase should be deployable independently
   - Include rollback considerations

3. **Task Breakdown**
   - Break each phase into atomic tasks
   - Estimate complexity (S/M/L)
   - Assign to service/team

4. **Integration Points**
   - Identify cross-service contracts
   - Define API boundaries early
   - Plan integration testing

## Tool Usage

```bash
python tools/feature-analysis.py synthesize \
  --master-input /tmp/master-input.json \
  --frontend-input /tmp/frontend-input.json \
  --backend-input /tmp/backend-input.json \
  --core-input /tmp/core-input.json \
  --infra-input /tmp/infra-input.json \
  --design-patterns-input /tmp/design-patterns-input.json \
  --output /tmp/synthesized.json
```

## Output Structure

```json
{
  "phases": [
    {
      "name": "Phase 1: Core Setup",
      "tasks": [...],
      "dependencies": [],
      "deliverables": [...]
    }
  ],
  "total_tasks": 24,
  "estimated_days": 8,
  "complexity": "medium",
  "risks": [...],
  "patterns_applied": [...]
}
```
