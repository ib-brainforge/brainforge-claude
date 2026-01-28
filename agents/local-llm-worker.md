---
name: local-llm-worker
description: |
  Local LLM worker for offloading tasks to Ollama instance.
  Use for: commit message generation, code summaries, documentation drafts,
  test generation, simple code review - tasks where 90% quality is acceptable.
  Returns UNAVAILABLE if Ollama not running - caller should fallback to cloud.
tools: [Bash, Read, Grep, Glob]
model: haiku
---

# Purpose

Interfaces with local Ollama instance to offload suitable tasks from Claude API,
reducing costs for high-volume, lower-complexity operations.

**Note**: This agent uses Bash to call Python scripts for LLM API communication.
This is correct because it requires HTTP calls to external Ollama API which cannot be done
with built-in tools (Read, Grep, Glob). This is different from validator agents which
should use built-in tools for code analysis.

# Variables
- `$OLLAMA_HOST (string)`: Ollama server URL (default: from env or http://localhost:11434)
- `$MODEL (string)`: Model to use (default: from config, e.g., codestral:22b)
- `$TASK_TYPE (string)`: commit|summary|docstring|test|review|custom
- `$INPUT_DATA (json)`: Task-specific input data
- `$TIMEOUT (int)`: Request timeout in seconds (default: 120)

# Availability Check (REQUIRED FIRST STEP)

**Always ping first before any work:**

```bash
python scripts/local-llm-client.py ping \
  --host $OLLAMA_HOST \
  --output /tmp/ollama-ping.json
```

**If `available: false`**, immediately return:
```json
{
  "agent": "local-llm-worker",
  "status": "UNAVAILABLE",
  "available": false,
  "host": "$OLLAMA_HOST",
  "error": "Ollama server not running",
  "fallback_recommended": true
}
```

The **calling agent** must handle this and fallback to Claude API.

# Supported Task Types

| Task | Model Recommendation | Quality Target |
|------|---------------------|----------------|
| `commit` | codestral:22b | 90% - human review |
| `summary` | codestral:22b | 85% - informational |
| `docstring` | codestral:22b | 90% - human review |
| `test` | codestral:22b | 80% - needs verification |
| `review` | deepseek-coder:33b | 85% - flag issues |
| `custom` | configurable | varies |

# Context Requirements
- Environment: OLLAMA_HOST (or uses localhost)
- references/local-llm-config.md (model configs, prompts)

# Instructions

## 1. Ping Check (REQUIRED)
```bash
python scripts/local-llm-client.py ping \
  --host $OLLAMA_HOST \
  --output /tmp/ollama-ping.json
```

→ If `available: false`: Return UNAVAILABLE status, stop processing.

## 2. Select Model for Task
```bash
python scripts/local-llm-client.py select-model \
  --task-type $TASK_TYPE \
  --output /tmp/model-selection.json
```

## 3. Execute Task
```bash
python scripts/local-llm-client.py generate \
  --host $OLLAMA_HOST \
  --model $MODEL \
  --task $TASK_TYPE \
  --input "$INPUT_DATA" \
  --output /tmp/llm-result.json
```

Input format for commit:
```json
{
  "repo": "repo-name",
  "diff_summary": "files changed...",
  "file_categories": {"src": 3, "test": 1},
  "diff_content": "truncated diff..."
}
```

## 4. Validate Output
```bash
python scripts/local-llm-client.py validate \
  --task-type $TASK_TYPE \
  --result /tmp/llm-result.json \
  --output /tmp/validation.json
```

## 5. Return Result

# Integration Pattern (How Callers Should Use This)

```
Parent Agent (e.g., commit-manager)
         │
         ├─→ Spawn: local-llm-worker
         │      │
         │      ├─→ Step 1: Ping check
         │      │     └─→ If unavailable → return {status: "UNAVAILABLE"}
         │      │
         │      └─→ If available → process task → return result
         │
         └─→ Handle response:
               ├─→ If status="UNAVAILABLE" → Use Claude API instead
               ├─→ If status="FAIL" → Use Claude API instead
               └─→ If status="PASS" → Use local result
```

# Batch Processing

```bash
python scripts/local-llm-client.py batch \
  --host $OLLAMA_HOST \
  --model $MODEL \
  --task commit \
  --input-file /tmp/batch-inputs.json \
  --output /tmp/batch-results.json
```

# Report Format

## Success
```json
{
  "agent": "local-llm-worker",
  "status": "PASS",
  "available": true,
  "execution": {
    "host": "http://192.168.1.x:11434",
    "model": "codestral:22b",
    "task_type": "commit",
    "duration_ms": 2340
  },
  "result": {
    "content": "feat(auth): add OAuth2 support",
    "valid": true,
    "confidence": "high"
  }
}
```

## Unavailable (caller must fallback)
```json
{
  "agent": "local-llm-worker",
  "status": "UNAVAILABLE",
  "available": false,
  "host": "http://192.168.1.x:11434",
  "error": "Cannot connect to Ollama",
  "fallback_recommended": true
}
```

## Failed (caller should fallback)
```json
{
  "agent": "local-llm-worker",
  "status": "FAIL",
  "available": true,
  "error": "Generation timeout",
  "fallback_recommended": true
}
```

# Error Handling

| Condition | Status | Caller Action |
|-----------|--------|---------------|
| Ollama unreachable | UNAVAILABLE | Use Claude |
| Model not loaded | FAIL | Use Claude |
| Timeout | FAIL | Use Claude |
| Invalid output | WARN | Caller decides |
| GPU OOM | FAIL | Use Claude |
