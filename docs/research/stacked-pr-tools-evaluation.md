---
id: "RESEARCH-001"
version: "1.0.0"
type: research
status: complete
created: 2026-02-11
updated: 2026-02-11
author: "steering-orchestrator"
topic: "Stacked PR Tools for Claude Agent Workflows"
decision: "spr (recommended) + git-town (optional)"
---

# Stacked PR Tools Evaluation

> Free alternatives to Graphite for working with chains of commits, breaking them into atomic PRs for Claude agent review.

## Context

### Why Stacked PRs for Claude Agents?

Claude agents work best with:
1. **Small, atomic changes** - Easier to review and test
2. **Clear dependency chains** - Agent can understand "what came before"
3. **Fast iteration** - Quick merge cycles keep agents productive
4. **Deterministic ordering** - Reproducible workflows

### Problem Statement

Graphite provides excellent stacked diff workflow but:
- Proprietary (merging with Cursor as of Dec 2025)
- Paid tiers for team features
- Vendor lock-in concerns

Need: Free, open-source alternative that works well with Claude Code agents.

---

## Tool Comparison Matrix

| Tool | Stars | License | Install | Commit Model | Agent-Friendly | Last Updated |
|------|-------|---------|---------|--------------|----------------|--------------|
| **git-town** | 3.1k | MIT | brew/apt | Branch-based | ⭐⭐⭐⭐ | Jan 2026 (v22.5.0) |
| **spr** | 1.1k | MIT | brew/apt | Commit→PR | ⭐⭐⭐⭐⭐ | Jan 2026 (v0.16.0) |
| **ghstack** | 918 | MIT | uv/pip | Commit→PR | ⭐⭐⭐ | Active |
| **stack-pr** | 493 | Apache | pipx | Commit→PR | ⭐⭐⭐⭐ | Jan 2025 |
| **Graphite** | N/A | Proprietary | npm | Branch-based | ⭐⭐⭐⭐⭐ | N/A |

---

## Detailed Analysis

### 1. spr (Stacked Pull Requests)

**Repository**: https://github.com/ejoffe/spr
**Stars**: 1.1k | **License**: MIT | **Last Release**: v0.16.0 (Jan 2026)

**Best for**: Claude agents that work commit-by-commit

#### Pros
- Each commit = 1 PR (perfect for atomic work)
- No extra branches to manage
- MIT license, actively maintained
- Simple CLI: `spr diff`, `spr update`, `spr merge`
- Works with any GitHub repo
- GitHub Enterprise compatible
- Multiple merge strategies (rebase, squash, merge)

#### Cons
- Can't merge via GitHub UI (must use `spr merge`)
- Combines commits on merge (can be surprising)
- Requires discipline in commit hygiene

#### Installation
```bash
# Homebrew
brew tap ejoffe/homebrew-tap
brew install ejoffe/tap/spr

# APT (Debian/Ubuntu)
# Via Inigo Labs repository
```

#### Workflow
```bash
# Agent creates atomic commits
git commit -m "feat(auth): add middleware skeleton"
git commit -m "feat(auth): implement JWT validation"
git commit -m "test(auth): add middleware tests"

# Export as stacked PRs
spr diff

# Review status
spr status

# Merge all approved PRs bottom-up
spr merge
```

---

### 2. git-town

**Repository**: https://github.com/git-town/git-town
**Stars**: 3.1k | **License**: MIT | **Last Release**: v22.5.0 (Jan 2026)

**Best for**: Teams wanting full Git workflow automation

#### Pros
- Most mature project (3.1k stars)
- Full workflow automation beyond stacking
- `append`, `prepend`, `swap` commands for stack manipulation
- Works with GitLab, Gitea, Bitbucket (not just GitHub)
- Excellent documentation at git-town.com
- Active development and community

#### Cons
- More complex than spr
- Branch-based model (more overhead)
- Steeper learning curve
- May be overkill for simple stacking needs

#### Installation
```bash
# Homebrew
brew install git-town

# See git-town.com for other methods
```

#### Workflow
```bash
# Create child branch
git town append feature-auth

# Work and commit
git commit -m "feat: add auth"

# Insert branch before current
git town prepend feature-setup

# Sync entire stack with upstream
git town sync

# Swap position with parent
git town swap
```

---

### 3. stack-pr (Modular)

**Repository**: https://github.com/modular/stack-pr
**Stars**: 493 | **License**: Apache 2.0 | **Last Commit**: Jan 2025

**Best for**: Python-centric teams, ghstack replacement

#### Pros
- Clean Python implementation
- Fixes ghstack limitations (no force-push required)
- Simple commands: `submit`, `view`, `land`, `abandon`
- Good for Mojo/Python development shops
- Inspired by ghstack but improved

#### Cons
- Newer project (493 stars)
- Less battle-tested than alternatives
- Requires pipx for installation
- Smaller community

#### Installation
```bash
# Via pipx (recommended)
pipx install stack-pr

# From source
git clone https://github.com/modular/stack-pr
cd stack-pr
pipx install .
```

#### Workflow
```bash
# Create commits on feature branch
git commit -m "feat: part 1"
git commit -m "feat: part 2"

# Export as stacked PRs
stack-pr submit

# View without pushing
stack-pr view

# Merge bottom PR, rebase rest
stack-pr land

# Clean up stack
stack-pr abandon
```

---

### 4. ghstack (Meta/PyTorch)

**Repository**: https://github.com/ezyang/ghstack
**Stars**: 918 | **License**: MIT

**Best for**: Large monorepos with strict review culture

#### Pros
- Battle-tested at Meta scale
- Designed for PyTorch workflow
- Strong rebase handling
- Proven at scale

#### Cons
- Requires force-push enabled on repo
- Creates 3x branches per stack (`base`, `head`, `orig`)
- Can't use GitHub merge UI
- Requires Personal Access Token configuration
- Python 3.9.1+ required

#### Installation
```bash
uv tool install ghstack
```

#### Limitations
- Users cannot merge through GitHub's normal UI
- Must use rebase (not merge) for stack rebasing
- Write permission to repository mandatory

---

## Anthropic Engineering Context

Based on Claude Code patterns and Anthropic's engineering practices:

1. **Atomic commits** - Claude Code's `/commit` generates conventional commits
2. **Hooks-based automation** - GitButler integration creates commits per session
3. **Trunk-based development** - Short-lived branches, frequent merges
4. **Agent-friendly review** - Small PRs that agents can understand

**Inferred approach**: Simple tooling that doesn't fight Git, emphasizes atomic commits, integrates with existing GitHub workflows.

---

## Recommendation

### Primary: **spr**

#### Rationale

1. **Perfect agent mental model**: 1 commit = 1 PR = 1 reviewable unit
2. **Zero branch management**: Agents don't track branch names
3. **Simple commands**: `spr diff`, `spr update`, `spr merge`
4. **MIT licensed, actively maintained** (v0.16.0, Jan 2026)
5. **Works with existing GitHub repos** - no special server setup
6. **Easy installation** - Homebrew/apt, easy CI integration

### Secondary (Optional): **git-town**

Add if you need:
- Complex branch manipulation (`prepend`, `swap`)
- Multi-remote support (GitLab, Bitbucket)
- Full workflow automation beyond stacking

### Why NOT the others?

| Tool | Rejection Reason |
|------|------------------|
| Graphite | Proprietary, merging with Cursor |
| ghstack | Force-push required, 3x branch overhead |
| stack-pr | Newer, less ecosystem support |

---

## Decision Matrix

| If You Value... | Choose |
|-----------------|--------|
| Simplicity + Agent-friendly | **spr** |
| Full workflow control | **git-town** |
| Python ecosystem | **stack-pr** |
| Meta/PyTorch patterns | **ghstack** |
| Visual UI + paid support | **Graphite** |

---

## Proposed Agent Workflow

```bash
# 1. Agent creates atomic commits
git commit -m "feat(auth): add middleware skeleton"
git commit -m "feat(auth): implement JWT validation"
git commit -m "test(auth): add middleware tests"

# 2. Export as stacked PRs
spr diff

# 3. Each PR can be:
#    - Reviewed independently
#    - Tested in CI independently
#    - Approved in any order
#    - Merged bottom-up automatically

# 4. Merge all approved PRs
spr merge
```

---

## Implementation Tasks

| Priority | Task | Description |
|----------|------|-------------|
| P0 | Install spr | `brew install ejoffe/tap/spr` |
| P0 | Test with sample stack | Create 3-commit stack, export, merge |
| P1 | Document agent workflow | Add to `.claude-org/CLAUDE.md` |
| P1 | Create `/stack` command | Slash command for `spr diff` |
| P2 | CI integration | Add spr to GitHub Actions |
| P2 | Evaluate git-town | If spr insufficient, add git-town |
| P3 | Hook integration | Auto-run `spr diff` after agent commits |

---

## References

See `docs/research/sources/stacked-pr-sources.md` for full source list.
