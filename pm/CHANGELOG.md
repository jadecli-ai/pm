# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-02-11

### Added

- **Entity Hierarchy**: Epic → Story → Task → Subtask with YAML frontmatter
  - Tasks aligned with Claude Code TaskCreate/TaskUpdate
  - SemVer versioning for all entities
  - Dependency tracking via `dependsOn`, `blockedBy`, `blocks` fields

- **Merkle Tree Index** (`.index/`)
  - SHA256 file hashes for O(1) change detection
  - `AGENT-INDEX.md` for instant agent context (68 lines)
  - `generate-merkle.py` for index regeneration
  - `check-changes.py` for staleness detection

- **Agent Definitions** (`agents/`)
  - VP Product (Opus 4.5) - owns Epics
  - SDM (Sonnet) - owns Stories/Tasks
  - Staff Engineer (Sonnet) - owns Tasks/Subtasks
  - Sprint Master (Haiku) - ceremonies
  - All agents have `memory: project` for persistent learning

- **Integration Tests** (`tests/`)
  - Schema validation
  - Claude Code alignment verification
  - Dependency consistency checks
  - SemVer compliance validation

- **Documentation** (`docs/`)
  - `fetch/` - Fetched external documentation
  - `research/` - Compiled research on Claude Code memory system

- **CLAUDE.md** - Compact instruction file with:
  - Patterns to follow / Anti-patterns to avoid
  - Fail fast philosophy
  - TDD red/green/refactor approach
  - Conventional commits + SemVer rules
  - Known issues / lessons learned section

### Technical Details

- Root hash: `0eb4327a0168f9df0e479762f3782406297a700dbbc260160dfb036e9bcc3dff`
- Files indexed: 23
- Total lines: ~4,000

[Unreleased]: https://github.com/jadecli-ai/pm/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jadecli-ai/pm/releases/tag/v1.0.0
