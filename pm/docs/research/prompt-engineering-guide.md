---
id: "DOC-RESEARCH-001"
version: "1.0.0"
type: research
status: completed
created: 2026-02-11
updated: 2026-02-11
dependsOn:
  - "docs/fetch/anthropic-xml-tags.md"
  - "docs/fetch/anthropic-prompt-engineering.md"
dependedBy:
  - "agents/vp-product.md"
  - "agents/sdm.md"
  - "agents/staff-engineer.md"
  - "agents/sprint-master.md"
---

# PM System Prompt Engineering Guide

> Compiled research on Anthropic's prompt engineering conventions applied to this PM system

## Executive Summary

Anthropic's official documentation establishes XML tags as the primary structural convention for Claude prompts. This guide applies those patterns to our agent hierarchy and entity system.

## XML Tag Convention

### Standard Tags for PM System

```xml
<role>Agent role definition</role>
<context>Entity state, project context</context>
<instructions>Step-by-step task directives</instructions>
<constraints>Boundaries and limitations</constraints>
<output_format>Expected response structure</output_format>
<examples>Few-shot demonstrations</examples>
```

### Agent Prompt Structure

All PM agents should follow this template:

```xml
<agent name="{{AGENT_NAME}}">
  <role>
    {{ROLE_DESCRIPTION}}
  </role>

  <context>
    <entity type="{{TYPE}}" id="{{ID}}">
      {{FRONTMATTER_YAML}}
    </entity>
    <project_state>
      {{MERKLE_ROOT_HASH}}
    </project_state>
  </context>

  <instructions>
    1. {{STEP_1}}
    2. {{STEP_2}}
    3. {{STEP_3}}
  </instructions>

  <constraints>
    - {{CONSTRAINT_1}}
    - {{CONSTRAINT_2}}
  </constraints>

  <output_format>
    <response>
      <status>pending|in_progress|completed|blocked</status>
      <entities_modified>
        <entity id="{{ID}}" version="{{NEW_VERSION}}"/>
      </entities_modified>
      <summary>{{BRIEF_SUMMARY}}</summary>
    </response>
  </output_format>
</agent>
```

## Entity-Specific Patterns

### Epic Context

```xml
<epic id="EPIC-001">
  <title>{{TITLE}}</title>
  <stories>
    <story id="STORY-001" status="completed"/>
    <story id="STORY-002" status="in_progress"/>
  </stories>
  <metrics>
    <progress>0.45</progress>
    <blocked_count>1</blocked_count>
  </metrics>
</epic>
```

### Task Instructions

```xml
<task id="TASK-004">
  <instructions>
    <step order="1">Read current implementation</step>
    <step order="2">Identify gap against acceptance criteria</step>
    <step order="3">Implement minimal solution</step>
    <step order="4">Update task status to completed</step>
  </instructions>
  <acceptance_criteria>
    <criterion id="1">JWT tokens expire after 1 hour</criterion>
    <criterion id="2">Refresh tokens work correctly</criterion>
  </acceptance_criteria>
</task>
```

## Agent Hierarchy Communication

### VP Product → SDM

```xml
<delegation>
  <from>VP Product</from>
  <to>SDM</to>
  <entity type="epic" id="EPIC-001"/>
  <directive>
    Break this epic into stories with clear acceptance criteria.
    Each story should be independently deployable.
  </directive>
  <constraints>
    <max_stories>5</max_stories>
    <story_size>2-5 tasks each</story_size>
  </constraints>
</delegation>
```

### SDM → Staff Engineer

```xml
<assignment>
  <from>SDM</from>
  <to>Staff Engineer</to>
  <entity type="story" id="STORY-002"/>
  <directive>
    Design technical approach and break into tasks.
    Consider existing patterns in lib/.
  </directive>
  <context>
    <codebase_index>{{AGENT_INDEX_CONTENT}}</codebase_index>
  </context>
</assignment>
```

## Tool Calling Patterns

### Sequential Operations

```xml
<tool_chain>
  <step order="1">
    <tool>pm_l0_test</tool>
    <on_failure>abort</on_failure>
  </step>
  <step order="2">
    <tool>pm_l0_arch</tool>
    <depends_on>step_1</depends_on>
  </step>
</tool_chain>
```

### Parallel Operations

```xml
<parallel_tools>
  <tool>pm_l0_lint FILE=entities/TASK-001.md</tool>
  <tool>pm_l0_lint FILE=entities/TASK-002.md</tool>
  <tool>pm_l0_lint FILE=entities/TASK-003.md</tool>
</parallel_tools>
```

## Chain of Thought Integration

For complex decisions, request explicit reasoning:

```xml
<instructions>
  Before updating entity status, analyze in <thinking> tags:
  1. Are all acceptance criteria met?
  2. Are there any blockers?
  3. What version bump is appropriate?

  Then provide your action in <action> tags.
</instructions>
```

Expected output:

```xml
<thinking>
Checking TASK-004 acceptance criteria:
- [x] JWT tokens generated correctly
- [x] Tokens expire after 1 hour
- [x] Refresh flow works

All criteria met. No blockers. This completes a feature, so MINOR bump (1.0.0 → 1.1.0).
</thinking>

<action>
  <update entity="TASK-004">
    <status>completed</status>
    <version>1.1.0</version>
  </update>
</action>
```

## Few-Shot Examples for Agents

### Entity Validation Example

```xml
<examples>
  <example>
    <input>
      <entity id="TASK-005">
        <status>pending</status>
        <blockedBy>TASK-004</blockedBy>
      </entity>
      <query>Can TASK-005 start?</query>
    </input>
    <output>
      <answer>No</answer>
      <reason>TASK-004 is not completed</reason>
    </output>
  </example>

  <example>
    <input>
      <entity id="TASK-006">
        <status>pending</status>
        <blockedBy></blockedBy>
      </entity>
      <query>Can TASK-006 start?</query>
    </input>
    <output>
      <answer>Yes</answer>
      <reason>No blockers</reason>
    </output>
  </example>
</examples>
```

## Integration with Claude Code Tools

### TaskCreate Mapping

```xml
<mapping from="entity" to="claude_code">
  <field entity="subject" claude="subject"/>
  <field entity="description" claude="description"/>
  <field entity="activeForm" claude="activeForm"/>
</mapping>
```

### TaskUpdate Pattern

```xml
<task_update>
  <when>entity.status changes to in_progress</when>
  <call>
    TaskUpdate({
      taskId: "{{claude_task_id}}",
      status: "in_progress"
    })
  </call>
  <then>bump entity version +0.0.1</then>
</task_update>
```

## Summary

| Component | XML Pattern |
|-----------|-------------|
| Agent definition | `<agent><role><instructions></agent>` |
| Entity context | `<entity type="" id=""><frontmatter/></entity>` |
| Tool chains | `<tool_chain><step order="N"/></tool_chain>` |
| Parallel ops | `<parallel_tools><tool/></parallel_tools>` |
| Reasoning | `<thinking>...</thinking><action>...</action>` |
| Examples | `<examples><example><input/><output/></example></examples>` |

## References

- [Anthropic XML Tags](./fetch/anthropic-xml-tags.md)
- [Anthropic Prompt Engineering](./fetch/anthropic-prompt-engineering.md)
- [Claude Code TaskCreate/TaskUpdate](../tests/claude-code-alignment.md)
