---
id: "DOC-FETCH-001"
version: "1.0.0"
type: doc
status: completed
created: 2026-02-11
updated: 2026-02-11
source: "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags"
dependsOn: []
dependedBy:
  - "docs/research/prompt-engineering-guide.md"
---

# Use XML Tags to Structure Your Prompts

> Fetched from Anthropic official documentation

## Overview

XML tags help Claude parse prompts more accurately by clearly separating different components. They act as semantic markers that create structure and hierarchy.

## Key Benefits

1. **Clarity**: Delineates sections unambiguously
2. **Accuracy**: Reduces misinterpretation
3. **Flexibility**: Easy to modify or extend
4. **Parseability**: Consistent output extraction

## Best Practices

### 1. Be Consistent with Tag Names

Use the same tag names throughout your prompts:

```xml
<instructions>
Your task instructions here
</instructions>

<context>
Background information
</context>

<output_format>
How to structure the response
</output_format>
```

### 2. Nest Tags for Hierarchy

```xml
<document>
  <metadata>
    <author>Name</author>
    <date>2026-02-11</date>
  </metadata>
  <content>
    Document body here
  </content>
</document>
```

### 3. Common Tag Patterns

| Tag | Purpose |
|-----|---------|
| `<instructions>` | Task directives |
| `<context>` | Background information |
| `<examples>` | Few-shot examples |
| `<input>` | User-provided data |
| `<output>` | Expected response format |
| `<thinking>` | Chain of thought |
| `<answer>` | Final response |
| `<constraints>` | Limitations or rules |

### 4. Combine with Other Techniques

**With multishot prompting:**
```xml
<examples>
  <example>
    <input>Sample input 1</input>
    <output>Expected output 1</output>
  </example>
  <example>
    <input>Sample input 2</input>
    <output>Expected output 2</output>
  </example>
</examples>
```

**With chain of thought:**
```xml
<instructions>
First think step-by-step in <thinking> tags, then provide your answer in <answer> tags.
</instructions>
```

## Extraction Pattern

Claude can output structured XML for easy parsing:

```xml
<response>
  <status>success</status>
  <data>
    <field1>value1</field1>
    <field2>value2</field2>
  </data>
</response>
```

## Anti-Patterns

- Don't mix XML with other structural formats (Markdown headers, JSON) in the same section
- Don't use inconsistent tag names (`<input>` vs `<user_input>` vs `<query>`)
- Don't nest excessively (3-4 levels max for readability)
