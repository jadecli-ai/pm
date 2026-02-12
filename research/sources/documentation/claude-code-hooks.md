---
source: https://code.claude.com/docs/en/hooks
fetched: 2026-02-11
type: documentation
project: Claude Code
---

# Hooks reference

> Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, prompt hooks, and MCP tool hooks.

<Tip>
  For a quickstart guide with examples, see [Automate workflows with hooks](/en/hooks-guide).
</Tip>

Hooks are user-defined shell commands or LLM prompts that execute automatically at specific points in Claude Code's lifecycle. Use this reference to look up event schemas, configuration options, JSON input/output formats, and advanced features like async hooks and MCP tool hooks. If you're setting up hooks for the first time, start with the [guide](/en/hooks-guide) instead.

## Hook lifecycle

Hooks fire at specific points during a Claude Code session. When an event fires and a matcher matches, Claude Code passes JSON context about the event to your hook handler. For command hooks, this arrives on stdin. Your handler can then inspect the input, take action, and optionally return a decision. Some events fire once per session, while others fire repeatedly inside the agentic loop:

<div style={{maxWidth: "500px", margin: "0 auto"}}>
  <Frame>
    <img src="https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=7a351ea1cc3d5da7a2176bf51196bc1a" alt="Hook lifecycle diagram showing the sequence of hooks from SessionStart through the agentic loop to SessionEnd" data-og-width="520" width="520" data-og-height="960" height="960" data-path="images/hooks-lifecycle.svg" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?w=280&fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=8f32c67d025f0a318d5ed10a4f8ff2e6 280w, https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?w=560&fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=896fc424e39ff8d590720331a77e3d80 560w, https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?w=840&fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=a1c1c9739cde965e1eade843cee567c5 840w, https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?w=1100&fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=5bb083988de020e7d568e8dd8f1422fc 1100w, https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?w=1650&fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=343e9883c1e3172f08096c352aa46f12 1650w, https://mintcdn.com/claude-code/tpQvD9DKENFo4zX_/images/hooks-lifecycle.svg?w=2500&fit=max&auto=format&n=tpQvD9DKENFo4zX_&q=85&s=4de37b29de0f6df8b0c3e937a76c3bc6 2500w" />
  </Frame>
</div>

The table below summarizes when each event fires. The [Hook events](#hook-events) section documents the full input schema and decision control options for each one.

| Event                | When it fires                                                      |
| :------------------- | :----------------------------------------------------------------- |
| `SessionStart`       | When a session begins or resumes                                   |
| `UserPromptSubmit`   | When you submit a prompt, before Claude processes it               |
| `PreToolUse`         | Before a tool call executes. Can block it                          |
| `PermissionRequest`  | When a permission dialog appears                                   |
| `PostToolUse`        | After a tool call succeeds                                         |
| `PostToolUseFailure` | After a tool call fails                                            |
| `Notification`       | When Claude Code sends a notification                              |
| `SubagentStart`      | When a subagent is spawned                                         |
| `SubagentStop`       | When a subagent finishes                                           |
| `Stop`               | When Claude finishes responding                                    |
| `TeammateIdle`       | When an [agent team](/en/agent-teams) teammate is about to go idle |
| `TaskCompleted`      | When a task is being marked as completed                           |
| `PreCompact`         | Before context compaction                                          |
| `SessionEnd`         | When a session terminates                                          |

### How a hook resolves

To see how these pieces fit together, consider this `PreToolUse` hook that blocks destructive shell commands. The hook runs `block-rm.sh` before every Bash tool call:

```json  theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

The script reads the JSON input from stdin, extracts the command, and returns a `permissionDecision` of `"deny"` if it contains `rm -rf`:

```bash  theme={null}
#!/bin/bash
# .claude/hooks/block-rm.sh
COMMAND=$(jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by hook"
    }
  }'
else
  exit 0  # allow the command
fi
```

Now suppose Claude Code decides to run `Bash "rm -rf /tmp/build"`. Here's what happens:

<Frame>
  <img src="https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=7c13f51ffcbc37d22a593b27e2f2de72" alt="Hook resolution flow: PreToolUse event fires, matcher checks for Bash match, hook handler runs, result returns to Claude Code" data-og-width="780" width="780" data-og-height="290" height="290" data-path="images/hook-resolution.svg" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=280&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=36a39a07e8bc1995dcb4639e09846905 280w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=560&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=6568d90c596c7605bbac2c325b0a0c86 560w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=840&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=255a6f68b9475a0e41dbde7b88002dad 840w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=1100&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=dcecf8d5edc88cd2bc49deb006d5760d 1100w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=1650&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=04fe51bf69ae375e9fd517f18674e35f 1650w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=2500&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=b1b76e0b77fddb5c7fa7bf302dacd80b 2500w" />
</Frame>

<Steps>
  <Step title="Event fires">
    The `PreToolUse` event fires. Claude Code sends the tool input as JSON on stdin to the hook:

    ```json  theme={null}
    { "tool_name": "Bash", "tool_input": { "command": "rm -rf /tmp/build" }, ... }
    ```
  </Step>

  <Step title="Matcher checks">
    The matcher `"Bash"` matches the tool name, so `block-rm.sh` runs. If you omit the matcher or use `"*"`, the hook runs on every occurrence of the event. Hooks only skip when a matcher is defined and doesn't match.
  </Step>

  <Step title="Hook handler runs">
    The script extracts `"rm -rf /tmp/build"` from the input and finds `rm -rf`, so it prints a decision to stdout:

    ```json  theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Destructive command blocked by hook"
      }
    }
    ```

    If the command had been safe (like `npm test`), the script would hit `exit 0` instead, which tells Claude Code to allow the tool call with no further action.
  </Step>

  <Step title="Claude Code acts on the result">
    Claude Code reads the JSON decision, blocks the tool call, and shows Claude the reason.
  </Step>
</Steps>

The [Configuration](#configuration) section below documents the full schema, and each [hook event](#hook-events) section documents what input your command receives and what output it can return.

## Configuration

Hooks are defined in JSON settings files. The configuration has three levels of nesting:

1. Choose a [hook event](#hook-events) to respond to, like `PreToolUse` or `Stop`
2. Add a [matcher group](#matcher-patterns) to filter when it fires, like "only for the Bash tool"
3. Define one or more [hook handlers](#hook-handler-fields) to run when matched

See [How a hook resolves](#how-a-hook-resolves) above for a complete walkthrough with an annotated example.

<Note>
  This page uses specific terms for each level: **hook event** for the lifecycle point, **matcher group** for the filter, and **hook handler** for the shell command, prompt, or agent that runs. "Hook" on its own refers to the general feature.
</Note>

### Hook locations

Where you define a hook determines its scope:

| Location                                                   | Scope                         | Shareable                          |
| :--------------------------------------------------------- | :---------------------------- | :--------------------------------- |
| `~/.claude/settings.json`                                  | All your projects             | No, local to your machine          |
| `.claude/settings.json`                                    | Single project                | Yes, can be committed to the repo  |
| `.claude/settings.local.json`                              | Single project                | No, gitignored                     |
| Managed policy settings                                    | Organization-wide             | Yes, admin-controlled              |
| [Plugin](/en/plugins) `hooks/hooks.json`                   | When plugin is enabled        | Yes, bundled with the plugin       |
| [Skill](/en/skills) or [agent](/en/sub-agents) frontmatter | While the component is active | Yes, defined in the component file |

For details on settings file resolution, see [settings](/en/settings). Enterprise administrators can use `allowManagedHooksOnly` to block user, project, and plugin hooks. See [Hook configuration](/en/settings#hook-configuration).

### Matcher patterns

The `matcher` field is a regex string that filters when hooks fire. Use `"*"`, `""`, or omit `matcher` entirely to match all occurrences. Each event type matches on a different field:

| Event                                                                  | What the matcher filters  | Example matcher values                                                         |
| :--------------------------------------------------------------------- | :------------------------ | :----------------------------------------------------------------------------- |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest` | tool name                 | `Bash`, `Edit\|Write`, `mcp__.*`                                               |
| `SessionStart`                                                         | how the session started   | `startup`, `resume`, `clear`, `compact`                                        |
| `SessionEnd`                                                           | why the session ended     | `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `Notification`                                                         | notification type         | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`       |
| `SubagentStart`                                                        | agent type                | `Bash`, `Explore`, `Plan`, or custom agent names                               |
| `PreCompact`                                                           | what triggered compaction | `manual`, `auto`                                                               |
| `SubagentStop`                                                         | agent type                | same values as `SubagentStart`                                                 |
| `UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCompleted`            | no matcher support        | always fires on every occurrence                                               |

The matcher is a regex, so `Edit|Write` matches either tool and `Notebook.*` matches any tool starting with Notebook. The matcher runs against a field from the [JSON input](#hook-input-and-output) that Claude Code sends to your hook on stdin. For tool events, that field is `tool_name`. Each [hook event](#hook-events) section lists the full set of matcher values and the input schema for that event.

This example runs a linting script only when Claude writes or edits a file:

```json  theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/lint-check.sh"
          }
        ]
      }
    ]
  }
}
```

`UserPromptSubmit` and `Stop` don't support matchers and always fire on every occurrence. If you add a `matcher` field to these events, it is silently ignored.

#### Match MCP tools

[MCP](/en/mcp) server tools appear as regular tools in tool events (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`), so you can match them the same way you match any other tool name.

MCP tools follow the naming pattern `mcp__<server>__<tool>`, for example:

* `mcp__memory__create_entities`: Memory server's create entities tool
* `mcp__filesystem__read_file`: Filesystem server's read file tool
* `mcp__github__search_repositories`: GitHub server's search tool

Use regex patterns to target specific MCP tools or groups of tools:

* `mcp__memory__.*` matches all tools from the `memory` server
* `mcp__.*__write.*` matches any tool containing "write" from any server

This example logs all memory server operations and validates write operations from any MCP server:

```json  theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory operation initiated' >> ~/mcp-operations.log"
          }
        ]
      },
      {
        "matcher": "mcp__.*__write.*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/validate-mcp-write.py"
          }
        ]
      }
    ]
  }
}
```

### Hook handler fields

Each object in the inner `hooks` array is a hook handler: the shell command, LLM prompt, or agent that runs when the matcher matches. There are three types:

* **[Command hooks](#command-hook-fields)** (`type: "command"`): run a shell command. Your script receives the event's [JSON input](#hook-input-and-output) on stdin and communicates results back through exit codes and stdout.
* **[Prompt hooks](#prompt-and-agent-hook-fields)** (`type: "prompt"`): send a prompt to a Claude model for single-turn evaluation. The model returns a yes/no decision as JSON. See [Prompt-based hooks](#prompt-based-hooks).
* **[Agent hooks](#prompt-and-agent-hook-fields)** (`type: "agent"`): spawn a subagent that can use tools like Read, Grep, and Glob to verify conditions before returning a decision. See [Agent-based hooks](#agent-based-hooks).

#### Common fields

These fields apply to all hook types:

| Field           | Required | Description                                                                                                                                   |
| :-------------- | :------- | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`          | yes      | `"command"`, `"prompt"`, or `"agent"`                                                                                                         |
| `timeout`       | no       | Seconds before canceling. Defaults: 600 for command, 30 for prompt, 60 for agent                                                              |
| `statusMessage` | no       | Custom spinner message displayed while the hook runs                                                                                          |
| `once`          | no       | If `true`, runs only once per session then is removed. Skills only, not agents. See [Hooks in skills and agents](#hooks-in-skills-and-agents) |

#### Command hook fields

In addition to the [common fields](#common-fields), command hooks accept these fields:

| Field     | Required | Description                                                                                                         |
| :-------- | :------- | :------------------------------------------------------------------------------------------------------------------ |
| `command` | yes      | Shell command to execute                                                                                            |
| `async`   | no       | If `true`, runs in the background without blocking. See [Run hooks in the background](#run-hooks-in-the-background) |

#### Prompt and agent hook fields

In addition to the [common fields](#common-fields), prompt and agent hooks accept these fields:

| Field    | Required | Description                                                                                 |
| :------- | :------- | :------------------------------------------------------------------------------------------ |
| `prompt` | yes      | Prompt text to send to the model. Use `$ARGUMENTS` as a placeholder for the hook input JSON |
| `model`  | no       | Model to use for evaluation. Defaults to a fast model                                       |

All matching hooks run in parallel, and identical handlers are deduplicated automatically. Handlers run in the current directory with Claude Code's environment. The `$CLAUDE_CODE_REMOTE` environment variable is set to `"true"` in remote web environments and not set in the local CLI.

### Reference scripts by path

Use environment variables to reference hook scripts relative to the project or plugin root, regardless of the working directory when the hook runs:

* `$CLAUDE_PROJECT_DIR`: the project root. Wrap in quotes to handle paths with spaces.
* `${CLAUDE_PLUGIN_ROOT}`: the plugin's root directory, for scripts bundled with a [plugin](/en/plugins).

<Tabs>
  <Tab title="Project scripts">
    This example uses `$CLAUDE_PROJECT_DIR` to run a style checker from the project's `.claude/hooks/` directory after any `Write` or `Edit` tool call:

    ```json  theme={null}
    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>

  <Tab title="Plugin scripts">
    Define plugin hooks in `hooks/hooks.json` with an optional top-level `description` field. When a plugin is enabled, its hooks merge with your user and project hooks.

    This example runs a formatting script bundled with the plugin:

    ```json  theme={null}
    {
      "description": "Automatic code formatting",
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
                "timeout": 30
              }
            ]
          }
        ]
      }
    }
    ```

    See the [plugin components reference](/en/plugins-reference#hooks) for details on creating plugin hooks.
  </Tab>
</Tabs>

### Hooks in skills and agents

In addition to settings files and plugins, hooks can be defined directly in [skills](/en/skills) and [subagents](/en/sub-agents) using frontmatter. These hooks are scoped to the component's lifecycle and only run when that component is active.

All hook events are supported. For subagents, `Stop` hooks are automatically converted to `SubagentStop` since that is the event that fires when a subagent completes.

Hooks use the same configuration format as settings-based hooks but are scoped to the component's lifetime and cleaned up when it finishes.

This skill defines a `PreToolUse` hook that runs a security validation script before each `Bash` command:

```yaml  theme={null}
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

Agents use the same format in their YAML frontmatter.

### The `/hooks` menu

Type `/hooks` in Claude Code to open the interactive hooks manager, where you can view, add, and delete hooks without editing settings files directly. For a step-by-step walkthrough, see [Set up your first hook](/en/hooks-guide#set-up-your-first-hook) in the guide.

Each hook in the menu is labeled with a bracket prefix indicating its source:

* `[User]`: from `~/.claude/settings.json`
* `[Project]`: from `.claude/settings.json`
* `[Local]`: from `.claude/settings.local.json`
* `[Plugin]`: from a plugin's `hooks/hooks.json`, read-only

### Disable or remove hooks

To remove a hook, delete its entry from the settings JSON file, or use the `/hooks` menu and select the hook to delete it.

To temporarily disable all hooks without removing them, set `"disableAllHooks": true` in your settings file or use the toggle in the `/hooks` menu. There is no way to disable an individual hook while keeping it in the configuration.

Direct edits to hooks in settings files don't take effect immediately. Claude Code captures a snapshot of hooks at startup and uses it throughout the session. This prevents malicious or accidental hook modifications from taking effect mid-session without your review. If hooks are modified externally, Claude Code warns you and requires review in the `/hooks` menu before changes apply.

## Hook input and output

Hooks receive JSON data via stdin and communicate results through exit codes, stdout, and stderr. This section covers fields and behavior common to all events. Each event's section under [Hook events](#hook-events) includes its specific input schema and decision control options.

### Common input fields

All hook events receive these fields via stdin as JSON, in addition to event-specific fields documented in each [hook event](#hook-events) section:

| Field             | Description                                                                                                                                |
| :---------------- | :----------------------------------------------------------------------------------------------------------------------------------------- |
| `session_id`      | Current session identifier                                                                                                                 |
| `transcript_path` | Path to conversation JSON                                                                                                                  |
| `cwd`             | Current working directory when the hook is invoked                                                                                         |
| `permission_mode` | Current [permission mode](/en/permissions#permission-modes): `"default"`, `"plan"`, `"acceptEdits"`, `"dontAsk"`, or `"bypassPermissions"` |
| `hook_event_name` | Name of the event that fired                                                                                                               |

For example, a `PreToolUse` hook for a Bash command receives this on stdin:

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  }
}
```

The `tool_name` and `tool_input` fields are event-specific. Each [hook event](#hook-events) section documents the additional fields for that event.

### Exit code output

The exit code from your hook command tells Claude Code whether the action should proceed, be blocked, or be ignored.

**Exit 0** means success. Claude Code parses stdout for [JSON output fields](#json-output). JSON output is only processed on exit 0. For most events, stdout is only shown in verbose mode (`Ctrl+O`). The exceptions are `UserPromptSubmit` and `SessionStart`, where stdout is added as context that Claude can see and act on.

**Exit 2** means a blocking error. Claude Code ignores stdout and any JSON in it. Instead, stderr text is fed back to Claude as an error message. The effect depends on the event: `PreToolUse` blocks the tool call, `UserPromptSubmit` rejects the prompt, and so on. See [exit code 2 behavior](#exit-code-2-behavior-per-event) for the full list.

**Any other exit code** is a non-blocking error. stderr is shown in verbose mode (`Ctrl+O`) and execution continues.

For example, a hook command script that blocks dangerous Bash commands:

```bash  theme={null}
#!/bin/bash
# Reads JSON input from stdin, checks the command
command=$(jq -r '.tool_input.command' < /dev/stdin)

if [[ "$command" == rm* ]]; then
  echo "Blocked: rm commands are not allowed" >&2
  exit 2  # Blocking error: tool call is prevented
fi

exit 0  # Success: tool call proceeds
```

#### Exit code 2 behavior per event

Exit code 2 is the way a hook signals "stop, don't do this." The effect depends on the event, because some events represent actions that can be blocked (like a tool call that hasn't happened yet) and others represent things that already happened or can't be prevented.

| Hook event           | Can block? | What happens on exit 2                                             |
| :------------------- | :--------- | :----------------------------------------------------------------- |
| `PreToolUse`         | Yes        | Blocks the tool call                                               |
| `PermissionRequest`  | Yes        | Denies the permission                                              |
| `UserPromptSubmit`   | Yes        | Blocks prompt processing and erases the prompt                     |
| `Stop`               | Yes        | Prevents Claude from stopping, continues the conversation          |
| `SubagentStop`       | Yes        | Prevents the subagent from stopping                                |
| `TeammateIdle`       | Yes        | Prevents the teammate from going idle (teammate continues working) |
| `TaskCompleted`      | Yes        | Prevents the task from being marked as completed                   |
| `PostToolUse`        | No         | Shows stderr to Claude (tool already ran)                          |
| `PostToolUseFailure` | No         | Shows stderr to Claude (tool already failed)                       |
| `Notification`       | No         | Shows stderr to user only                                          |
| `SubagentStart`      | No         | Shows stderr to user only                                          |
| `SessionStart`       | No         | Shows stderr to user only                                          |
| `SessionEnd`         | No         | Shows stderr to user only                                          |
| `PreCompact`         | No         | Shows stderr to user only                                          |

### JSON output

Exit codes let you allow or block, but JSON output gives you finer-grained control. Instead of exiting with code 2 to block, exit 0 and print a JSON object to stdout. Claude Code reads specific fields from that JSON to control behavior, including [decision control](#decision-control) for blocking, allowing, or escalating to the user.

<Note>
  You must choose one approach per hook, not both: either use exit codes alone for signaling, or exit 0 and print JSON for structured control. Claude Code only processes JSON on exit 0. If you exit 2, any JSON is ignored.
</Note>

Your hook's stdout must contain only the JSON object. If your shell profile prints text on startup, it can interfere with JSON parsing. See [JSON validation failed](/en/hooks-guide#json-validation-failed) in the troubleshooting guide.

The JSON object supports three kinds of fields:

* **Universal fields** like `continue` work across all events. These are listed in the table below.
* **Top-level `decision` and `reason`** are used by some events to block or provide feedback.
* **`hookSpecificOutput`** is a nested object for events that need richer control. It requires a `hookEventName` field set to the event name.

| Field            | Default | Description                                                                                                                |
| :--------------- | :------ | :------------------------------------------------------------------------------------------------------------------------- |
| `continue`       | `true`  | If `false`, Claude stops processing entirely after the hook runs. Takes precedence over any event-specific decision fields |
| `stopReason`     | none    | Message shown to the user when `continue` is `false`. Not shown to Claude                                                  |
| `suppressOutput` | `false` | If `true`, hides stdout from verbose mode output                                                                           |
| `systemMessage`  | none    | Warning message shown to the user                                                                                          |

To stop Claude entirely regardless of event type:

```json  theme={null}
{ "continue": false, "stopReason": "Build failed, fix errors before continuing" }
```

#### Decision control

Not every event supports blocking or controlling behavior through JSON. The events that do each use a different set of fields to express that decision. Use this table as a quick reference before writing a hook:

| Events                                                                | Decision pattern     | Key fields                                                        |
| :-------------------------------------------------------------------- | :------------------- | :---------------------------------------------------------------- |
| UserPromptSubmit, PostToolUse, PostToolUseFailure, Stop, SubagentStop | Top-level `decision` | `decision: "block"`, `reason`                                     |
| TeammateIdle, TaskCompleted                                           | Exit code only       | Exit code 2 blocks the action, stderr is fed back as feedback     |
| PreToolUse                                                            | `hookSpecificOutput` | `permissionDecision` (allow/deny/ask), `permissionDecisionReason` |
| PermissionRequest                                                     | `hookSpecificOutput` | `decision.behavior` (allow/deny)                                  |

Here are examples of each pattern in action:

<Tabs>
  <Tab title="Top-level decision">
    Used by `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, and `SubagentStop`. The only value is `"block"`. To allow the action to proceed, omit `decision` from your JSON, or exit 0 without any JSON at all:

    ```json  theme={null}
    {
      "decision": "block",
      "reason": "Test suite must pass before proceeding"
    }
    ```
  </Tab>

  <Tab title="PreToolUse">
    Uses `hookSpecificOutput` for richer control: allow, deny, or escalate to the user. You can also modify tool input before it runs or inject additional context for Claude. See [PreToolUse decision control](#pretooluse-decision-control) for the full set of options.

    ```json  theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Database writes are not allowed"
      }
    }
    ```
  </Tab>

  <Tab title="PermissionRequest">
    Uses `hookSpecificOutput` to allow or deny a permission request on behalf of the user. When allowing, you can also modify the tool's input or apply permission rules so the user isn't prompted again. See [PermissionRequest decision control](#permissionrequest-decision-control) for the full set of options.

    ```json  theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow",
          "updatedInput": {
            "command": "npm run lint"
          }
        }
      }
    }
    ```
  </Tab>
</Tabs>

For extended examples including Bash command validation, prompt filtering, and auto-approval scripts, see [What you can automate](/en/hooks-guide#what-you-can-automate) in the guide and the [Bash command validator reference implementation](https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py).

[Content continues with remaining sections...]
