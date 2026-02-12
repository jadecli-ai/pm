# jadecli Organization Standards

> Shared conventions and standards for all jadecli projects.
> This file is inherited by all projects in ~/projects/

## Organization Profile

| Field | Value |
|-------|-------|
| **Organization** | jadecli |
| **Team** | jadecli-agents |
| **Environment** | Ubuntu 26.04 WSL2 |
| **Hardware** | Ryzen 9 3900X (24t), 92GB RAM, RTX 2080 Ti |

## Code Standards

### Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

### Branch Naming

```
<type>/<ticket>-<description>
```

Examples:
- `feat/123-add-auth`
- `fix/456-memory-leak`
- `docs/789-api-reference`

### Code Review Checklist

Before submitting PR:
- [ ] Tests pass locally
- [ ] Linting passes
- [ ] No secrets in code
- [ ] Conventional commit messages
- [ ] PR description explains changes

## Security Requirements

### Never Commit

- `.env` files (use `.env.example` templates)
- API keys, tokens, credentials
- Private keys (*.pem, *.key, *_rsa)
- Database connection strings with passwords
- AWS/GCP/Azure credentials

### Required Security Practices

1. Use environment variables for secrets
2. Add secrets to `.gitignore`
3. Use secret scanning in CI
4. Rotate credentials regularly

## Technology Stack

### Preferred Tools

| Category | Tool |
|----------|------|
| **Python** | uv, ruff, mypy, pytest |
| **Node.js** | pnpm, eslint, prettier, vitest |
| **Rust** | cargo, rustfmt, clippy |
| **Container** | Docker, docker-compose |
| **CI/CD** | GitHub Actions |
| **Tracing** | MLflow, OpenTelemetry |

### Version Requirements

- Python 3.11+
- Node.js 20+
- Rust 1.75+
- Docker 24+

## Agent Teams

### Standard Team Structure

For multi-agent work, use this 6-pane grid layout:

```
┌──────────┬──────────┬──────────┐
│  Lead    │ Impl-1   │ Impl-2   │
│  (1)     │  (2)     │  (3)     │
├──────────┼──────────┼──────────┤
│ Impl-3   │  Test    │ Review   │
│  (4)     │  (5)     │  (6)     │
└──────────┴──────────┴──────────┘
```

### Agent Roles

| Role | Responsibilities |
|------|-----------------|
| **Lead** | Coordination, task breakdown, PR review |
| **Impl-1/2/3** | Feature implementation, different modules |
| **Test** | Test writing, coverage, integration tests |
| **Review** | Code review, security audit, docs |

### Team Naming

Teams: `alpha`, `beta`, `gamma`, `delta`

## File Structure Standards

### Project Root

```
project/
├── .claude/           # Claude Code project settings
│   ├── settings.json  # Project-specific overrides
│   └── agents/        # Custom agents
├── CLAUDE.md          # Project instructions
├── src/               # Source code
├── tests/             # Test files
├── docs/              # Documentation
├── scripts/           # Automation scripts
└── .env.example       # Environment template
```

### Settings Inheritance

```
~/.claude/settings.json (user)
    ↓
~/projects/.claude-org/settings.json (org)
    ↓
~/projects/{project}/.claude/settings.json (project)
    ↓
~/projects/{project}/.claude/settings.local.json (local)
```

## MCP Server Standards

### Required Servers

| Server | Purpose |
|--------|---------|
| `filesystem` | File I/O in allowed directories |
| `memory` | Knowledge graph persistence |
| `git` | Git operations |

### Optional Servers

| Server | When to Use |
|--------|-------------|
| `redis` | Progress tracking, caching |
| `fetch` | Web content retrieval |
| `sequential-thinking` | Complex reasoning |

## Error Handling

### Standard Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Misuse of command |
| 124 | Timeout |
| 127 | Command not found |

### Logging Standards

Use structured logging with these levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARN`: Warning conditions
- `ERROR`: Error conditions
- `FATAL`: Critical errors requiring shutdown

## Migration Notes

When migrating to Claude Teams/Enterprise:

1. Copy `~/projects/.claude-org/settings.json` to managed settings:
   - Linux: `/etc/claude-code/managed-settings.json`
   - macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`

2. Or use server-managed settings via Claude.ai Admin Console

3. Update `OTEL_EXPORTER_OTLP_ENDPOINT` to your collector

4. Configure SSO if using Enterprise
