---
id: "DOC-FETCH-002"
version: "1.0.0"
type: doc
status: completed
created: 2026-02-11
updated: 2026-02-11
source: "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering"
dependsOn: []
dependedBy:
  - "docs/research/prompt-engineering-guide.md"
---

# Anthropic Prompt Engineering Best Practices

> Fetched from Anthropic official documentation

## Core Principles

### 1. Be Explicit

Claude follows instructions literally. State exactly what you want:

```
Bad:  "Summarize this"
Good: "Summarize this document in 3 bullet points, each under 20 words"
```

### 2. Provide Context and Motivation

Explain why instructions matter:

```xml
<instructions>
Use formal language throughout.
This document will be reviewed by legal counsel and must maintain professional tone.
</instructions>
```

### 3. Use Structured Formats

For complex state or multi-step tasks, use JSON or XML:

```json
{
  "current_step": 2,
  "completed": ["step_1"],
  "remaining": ["step_3", "step_4"],
  "context": {}
}
```

### 4. Break Down Complex Tasks

Chain simpler prompts rather than one complex prompt:

1. **Prompt 1**: Extract key information
2. **Prompt 2**: Analyze extracted data
3. **Prompt 3**: Generate recommendations

## Parallel Tool Calling

When multiple operations are independent, execute them simultaneously:

```
If you need files A, B, and C:
- Don't: Read A, then read B, then read C
- Do: Read A, B, and C in parallel
```

## System Prompts

Use system prompts for:
- Persistent instructions
- Role definitions
- Behavioral constraints
- Output format specifications

## Few-Shot Prompting

Provide examples to establish patterns:

```xml
<examples>
<example>
Input: "The product is great!"
Output: {"sentiment": "positive", "confidence": 0.95}
</example>
<example>
Input: "Terrible experience."
Output: {"sentiment": "negative", "confidence": 0.90}
</example>
</examples>

Now analyze: "It works okay I guess"
```

## Chain of Thought

For reasoning tasks, request explicit thinking:

```
Before answering, think through the problem step by step in <thinking> tags.
Then provide your final answer in <answer> tags.
```

## Temperature and Sampling

| Task Type | Temperature | Use Case |
|-----------|-------------|----------|
| Deterministic | 0.0 | Code generation, extraction |
| Balanced | 0.5 | General tasks |
| Creative | 0.8-1.0 | Brainstorming, creative writing |

## Anti-Patterns to Avoid

1. **Ambiguous instructions**: "Make it better" → specify what "better" means
2. **Missing context**: Always include relevant background
3. **Over-constraining**: Too many rules can conflict
4. **Under-constraining**: No format = inconsistent output
5. **Ignoring failures**: Always handle edge cases explicitly
