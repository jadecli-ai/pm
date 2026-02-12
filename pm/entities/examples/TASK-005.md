---
id: "TASK-005"
version: "1.0.0"
type: task
status: pending
created: 2026-02-11
updated: 2026-02-11

# Claude Code Alignment
subject: "Research decision tree packages for prompt adapter"
description: "Evaluate modern decision tree packages to replace regex-based intent detection with systematic input capture and confirmation flow"
activeForm: "Researching decision tree packages"

# Hierarchy
parent: "STORY-003"
subtasks: []

# Assignment
owner: "staff-engineer"
domain: "backend"

# Sizing
size: "M"
agentHours: 3
storyPoints: 3

# Dependencies
dependsOn: []
blockedBy: []
blocks:
  - "TASK-006"  # Implement decision tree adapter

# Labels
labels:
  - "research"
  - "spike"
  - "prompt-adapter"
---

# [TASK-005] Research Decision Tree Packages for Prompt Adapter

## Objective

Evaluate modern decision tree packages that could replace the current regex-based `lib/prompt_adapter.py` with a more systematic approach for:
- Capturing developer input
- Confirming detected intent
- Guiding through missing information
- Building structured prompts

## Current Approach (Limitations)

```python
# lib/prompt_adapter.py uses regex patterns
INTENT_PATTERNS = [
    (r'\b(fix|bug|error|broken)\b', PromptIntent.FIX),
    (r'\b(add|create|implement)\b', PromptIntent.IMPLEMENT),
]
```

**Problems**:
- No confirmation step (silent misclassification)
- Can't ask follow-up questions
- Flat pattern matching (no branching logic)
- Hard to extend with new intents

## Research Areas

### 1. Python Decision Tree Libraries

| Package | Type | Notes |
|---------|------|-------|
| `transitions` | State machine | FSM with callbacks |
| `python-statemachine` | State machine | Async support |
| `pydantic` + custom | Validation tree | Type-driven branching |
| `questionary` | CLI prompts | Interactive confirmation |
| `inquirer` | CLI prompts | Node-style prompts |
| `textual` | TUI framework | Rich terminal UI |

### 2. Conversation Flow Frameworks

| Package | Type | Notes |
|---------|------|-------|
| `rasa` | NLU + Dialog | ML-based intent detection |
| `botpress` | Flow builder | Visual decision trees |
| `langchain` | LLM chains | Agent-based routing |

### 3. Form/Wizard Libraries

| Package | Type | Notes |
|---------|------|-------|
| `WTForms` | Web forms | Multi-step validation |
| `django-formtools` | Wizards | Step-by-step flows |

## Desired Flow

```
Developer Input
    │
    ▼
┌─────────────────┐
│ Detect Intent   │ ← Decision node 1
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Confirm Intent? │ ← Confirmation step
│ [feat/fix/...]  │
└─────────────────┘
    │ yes/no
    ▼
┌─────────────────┐
│ Detect Repos    │ ← Decision node 2
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Missing Info?   │ ← Gap detection
│ Ask follow-up   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Generate XML    │ ← Output
└─────────────────┘
```

## Acceptance Criteria

- [ ] Evaluate 3+ decision tree / state machine packages
- [ ] Evaluate 2+ CLI prompt libraries for confirmation
- [ ] Create comparison matrix (features, complexity, maintenance)
- [ ] Prototype one approach with simple 3-node tree
- [ ] Document recommendation in `docs/research/decision-tree-eval.md`

## Research Questions

1. Can we use `pydantic` validators as decision nodes?
2. Does `transitions` support async for Claude Code integration?
3. Can `questionary` work within Claude Code's permission system?
4. Is there a way to serialize/resume decision tree state?

## Out of Scope

- Full implementation (separate task TASK-006)
- ML-based intent detection (too complex for v1)
- Visual flow builder (overkill for CLI)

## Notes

The goal is **systematic capture with confirmation**, not AI/ML intent detection. A simple decision tree with explicit confirmation steps is better than a smart system that silently misclassifies.

## References

- Current implementation: `lib/prompt_adapter.py`
- Current command: `.claude/commands/ask.md`
- Anthropic prompt patterns: `docs/research/prompt-engineering-guide.md`
