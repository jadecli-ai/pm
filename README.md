# jadecli Organization Settings

> Shared Claude Code configuration for all jadecli projects.

## Structure

```
.claude-org/
├── README.md              # This file
├── CLAUDE.md              # Org-wide coding standards
├── settings.json          # Org-level permissions, sandbox, telemetry
├── agents/                # Shared agent definitions
│   ├── team-lead.md       # Coordination agent
│   ├── implementer.md     # Feature development agent
│   ├── tester.md          # QA agent
│   └── reviewer.md        # Code review agent
├── hooks/                 # Shared hook scripts
│   ├── pre-commit-check.sh
│   └── test-on-edit.sh
├── templates/             # Project templates
│   ├── project-settings.json
│   └── project-CLAUDE.md
└── scripts/               # Utility scripts
    └── init-project.sh    # Initialize new project
```

## Usage

### Initialize a New Project

```bash
~/projects/.claude-org/scripts/init-project.sh my-new-project
```

This creates:
- `.claude/settings.json` - inherits from org settings
- `CLAUDE.md` - project instructions template
- Standard directory structure
- `.gitignore` and `.env.example`

### Settings Inheritance

Projects automatically inherit org settings. Override specific settings in project's `.claude/settings.json`:

```json
{
  "_inherits": "~/projects/.claude-org/settings.json",
  "permissions": {
    "allow": ["Bash(project-specific *)"]
  }
}
```

### Using Org Agents

Reference org agents in your project:

```bash
# In Claude Code
claude --agent ~/projects/.claude-org/agents/team-lead.md
```

Or copy to project and customize:
```bash
cp ~/projects/.claude-org/agents/implementer.md .claude/agents/
```

## Migration to Claude Teams

When migrating to Claude for Teams/Enterprise:

1. **Server-managed settings (recommended)**:
   - Go to claude.ai → Admin Settings → Claude Code → Managed settings
   - Paste contents of `settings.json`

2. **Endpoint-managed settings (MDM)**:
   ```bash
   # Linux/WSL
   sudo cp settings.json /etc/claude-code/managed-settings.json

   # macOS
   sudo cp settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"
   ```

3. **Update OpenTelemetry endpoint**:
   ```json
   {
     "env": {
       "OTEL_EXPORTER_OTLP_ENDPOINT": "http://your-collector:4317"
     }
   }
   ```

## Key Configurations

### Permissions Summary

| Category | Allowed | Denied | Ask |
|----------|---------|--------|-----|
| Package managers | npm, pnpm, yarn, uv, cargo | publish commands | install commands |
| Git | status, diff, log, add, commit, pull | force push, hard reset | push |
| Docker | build, compose, ps, logs | push | run, exec |
| Files | Read ~/projects/**, Edit src/** | .env, secrets/, ~/.ssh | - |

### Sandbox

- Enabled with auto-allow if sandboxed
- Network allowlist: github, npm, pypi, crates.io, anthropic

### Telemetry

- OpenTelemetry enabled (console exporter for local dev)
- Resource attributes: organization, project, environment
- Ready for collector endpoint when migrating

## Team Configuration

Standard 6-agent team structure:

| Role | Agent | Focus |
|------|-------|-------|
| Lead | team-lead.md | Coordination |
| Impl 1-3 | implementer.md | Feature development |
| Test | tester.md | Quality assurance |
| Review | reviewer.md | Code review |

Launch with WezTerm: `Ctrl+A Ctrl+4` (4 teams × 6 panes)
