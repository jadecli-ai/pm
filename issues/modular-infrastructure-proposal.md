# Modular Infrastructure & Specialized Teams Proposal

> Write-once, reuse-everywhere architecture for jadecli-ai organization

## Summary

This proposal outlines architectural changes to `.claude-org` that:
1. Enforce write-once/reuse-through-imports patterns via a shared `core/` package
2. Add comprehensive testing infrastructure with pytest + fixtures + coverage
3. Set up CI/CD with pre-commits using free-tier services
4. Create specialized teams for LLMs.txt ingestion, Vercel, Neon, and Claude Code optimization
5. Establish shared MLflow 3.9 tracing across all teams

---

## Current State Analysis

### What Exists (Good Patterns to Preserve)

| Component | Location | Pattern |
|-----------|----------|---------|
| Frontmatter parsing | `pm/lib/frontmatter.py` | Reused by validators, architecture, chain_detector |
| Budget tracking | `steering/lib/budget_tracker.py` | Dataclass + Enum pattern |
| Generic CRUD | `team-agents-sdk/src/db/crud.py` | Reusable across all tables |
| Semantic YAML schemas | `team-agents-sdk/semantic/*.yaml` | Single source of truth |
| Safe env access | `team-agents-sdk/src/get_env.py` | Never exposes secrets |
| Monotonic tool hierarchy | `pm/lib/tools.py` | L0->L1->L2->L3 composition |
| Steering system | `steering/config/*.yaml` | Budget + threshold configs |
| Team templates | `templates/create-team.py` | Jinja2 team generation |

### What's Missing (Gaps to Address)

| Gap | Impact | Proposed Fix |
|-----|--------|--------------|
| No Python unit tests in .claude-org | Silent failures possible | Add pytest + fixtures |
| No pre-commit hooks enforced | Inconsistent quality | Add `.pre-commit-config.yaml` |
| MLflow not integrated org-wide | No tracing across teams | Create shared tracing module |
| No shared base classes | Code duplication across teams | Create `core/` package |
| No dependency injection | Hard to test | Use Protocol-based DI |
| Manual team setup error-prone | Missing imports, wrong paths | Enhance templates with core/ imports |
| No LLMs.txt crawler | Missing AI-readable docs discovery | Build crawler system |

---

## Proposed Architecture

### Phase 1: Core Package Structure

Create a shared `core/` package that all teams import from:

```
.claude-org/
├── core/                           # SHARED: Write once, import everywhere
│   ├── __init__.py
│   ├── py.typed                    # PEP 561 marker
│   ├── base/
│   │   ├── __init__.py
│   │   ├── agent.py               # BaseAgent with steering integration
│   │   ├── entity.py              # BaseEntity with frontmatter
│   │   └── team.py                # BaseTeam with MLflow tracing
│   ├── tracing/
│   │   ├── __init__.py
│   │   ├── mlflow_hooks.py        # MLflow 3.9 autolog integration
│   │   ├── activity_logger.py     # Agent activity -> Neon
│   │   └── cost_tracker.py        # Token cost tracking
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py              # Async SQLAlchemy for Neon
│   │   ├── crud.py                # Generic CRUD operations
│   │   └── embeddings.py          # pgvector embedding storage
│   ├── crawlers/
│   │   ├── __init__.py
│   │   ├── llms_txt.py            # llms.txt / llms-full.txt parser
│   │   └── deep_linker.py         # Cross-document linking
│   └── testing/
│       ├── __init__.py
│       ├── fixtures.py            # Shared pytest fixtures
│       └── mocks.py               # Standardized mock factories
│
├── teams/
│   ├── claude-ops/                # NEW: Infrastructure team
│   ├── pm/                        # EXISTING: Product Management (move from root)
│   ├── backend-engineering/       # EXISTING: Backend team (move from root)
│   └── ...
│
├── steering/                      # EXISTING: Budget tracking (keep at root)
├── templates/                     # EXISTING: Team generation (enhance)
├── tests/                         # NEW: Org-level tests
│   ├── conftest.py               # Shared pytest config
│   ├── test_core_base.py
│   ├── test_core_tracing.py
│   └── test_core_crawlers.py
│
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Lint + test + type check
│       ├── pre-commit.yml         # Pre-commit hook enforcement
│       └── release.yml            # Semantic versioning
├── .pre-commit-config.yaml        # Pre-commit hooks
├── pyproject.toml                 # Python dependencies (org-level)
└── CLAUDE.md                      # Organization standards (update)
```

### Key Design Principles

1. **Write-once, import everywhere**: Code in `core/` is the source of truth
2. **Protocol-based DI**: Use `typing.Protocol` for testable interfaces
3. **Fail-fast, fail-loud**: Raise on bad state, never silently degrade
4. **Async everywhere**: `asyncpg` + `AsyncSession` for all DB operations

---

## Phase 2: Shared MLflow 3.9 Tracing

### Integration Pattern

All teams inherit tracing from `core/tracing/`:

```python
# core/tracing/mlflow_hooks.py
"""MLflow 3.9 tracing hooks for agent execution.

schema: N/A (core library)
depends_on:
  - core/base/team.py
depended_by:
  - teams/*/lib/__init__.py
semver: minor
"""

from typing import Protocol, Optional
from dataclasses import dataclass
import mlflow
from mlflow.entities import SpanType


class TracingHooks(Protocol):
    """Protocol for agent tracing hooks."""

    def pre_tool_use(self, tool_name: str, input: dict) -> None: ...
    def post_tool_use(self, tool_name: str, output: dict, duration_ms: float) -> None: ...
    def on_agent_stop(self, num_turns: int, cost_usd: float) -> None: ...


@dataclass
class MLflowHooksImpl:
    """MLflow-enabled hooks implementation."""

    agent_name: str
    task_id: str
    experiment_name: str

    def pre_tool_use(self, tool_name: str, input: dict) -> None:
        with mlflow.start_span(name=f"tool:{tool_name}", span_type=SpanType.TOOL) as span:
            span.set_inputs(input)

    def post_tool_use(self, tool_name: str, output: dict, duration_ms: float) -> None:
        mlflow.log_metric(f"{tool_name}_duration_ms", duration_ms)

    def on_agent_stop(self, num_turns: int, cost_usd: float) -> None:
        mlflow.log_metrics({
            "total_turns": num_turns,
            "total_cost_usd": cost_usd,
        })


def get_mlflow_hooks(
    experiment_name: str,
    agent_name: str,
    task_id: str,
) -> TracingHooks:
    """Create MLflow-enabled hooks for agent execution.

    Args:
        experiment_name: MLflow experiment (e.g., "jadecli-ai/claude-ops")
        agent_name: Name of the agent being traced
        task_id: Current task identifier

    Returns:
        TracingHooks implementation with MLflow integration
    """
    mlflow.set_experiment(experiment_name)

    # Auto-capture all Anthropic SDK calls
    mlflow.anthropic.autolog()

    return MLflowHooksImpl(
        agent_name=agent_name,
        task_id=task_id,
        experiment_name=experiment_name,
    )
```

### Team Integration Example

```python
# teams/claude-ops/lib/__init__.py
"""Claude Ops team library.

schema: N/A (team library)
depends_on:
  - core/tracing/mlflow_hooks.py
  - core/base/team.py
depended_by:
  - teams/claude-ops/agents/*.md
semver: minor
"""

from core.tracing import get_mlflow_hooks
from core.base import BaseTeam


class ClaudeOpsTeam(BaseTeam):
    """Claude Ops team with inherited MLflow tracing."""

    def __init__(self):
        super().__init__(
            name="claude-ops",
            experiment_name="jadecli-ai/claude-ops",
        )
        self.hooks = get_mlflow_hooks(
            experiment_name=self.experiment_name,
            agent_name="ops-orchestrator",
            task_id=self.current_task_id,
        )
```

---

## Phase 3: Claude Ops Team

### Purpose

Infrastructure management for jadecli-ai organization, including:
- LLMs.txt web crawling and document ingestion
- Claude Code release tracking and optimization
- Vercel deployment expertise
- Neon database management

### Agent Specifications

| Agent | Model | Turns | Role |
|-------|-------|-------|------|
| `ops-orchestrator` | claude-opus-4-6-20260201 | 30 | Extended thinking team lead, designs systems |
| `vercel-specialist` | claude-sonnet-4-5-20250929 | 15 | Vercel deployments, edge functions, caching |
| `neon-specialist` | claude-sonnet-4-5-20250929 | 15 | Neon Postgres, pgvector, branching workflow |
| `release-reviewer` | claude-opus-4-5-20251101 | 25 | Claude Code release analysis, agent optimization |

### Ops Orchestrator Responsibilities

1. **LLMs.txt Web Crawler System**
   - Ingest `llms.txt` and `llms-full.txt` from discovered domains
   - Parse structured format (# comments, > paths, - descriptions)
   - Store in Neon Postgres 17 with:
     - Original document hash (SHA-256)
     - Last fetched timestamp
     - pgvector embeddings (1536-dim)
     - Extracted action items
     - Deep links to related documents

2. **Claude Code Integration Discovery**
   - Search for existing Claude Code MCP servers
   - Identify reusable patterns from community
   - Propose integrations for jadecli-ai

### Release Reviewer Responsibilities

On every Claude Code release:
1. Fetch release notes via GitHub API
2. Analyze changes for impact on our agents
3. Generate optimization recommendations:
   - Token usage reduction
   - Latency improvements
   - Tool selection optimization
   - New feature adoption

---

## Phase 4: Testing Infrastructure

### pytest Configuration

```toml
# pyproject.toml (org-level)
[project]
name = "jadecli-org"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mlflow>=3.9",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "pydantic>=2.0",
    "httpx>=0.27",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "ruff>=0.9",
    "mypy>=1.8",
    "pre-commit>=4.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests", "teams/*/tests"]
addopts = "-v --cov=core --cov=teams --cov-report=term-missing --cov-fail-under=80"
markers = [
    "unit: Unit tests (no external dependencies)",
    "integration: Integration tests (requires Neon)",
    "slow: Slow tests (>5s)",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "ASYNC"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### Shared Fixtures

```python
# core/testing/fixtures.py
"""Shared pytest fixtures for all teams.

schema: N/A (testing utilities)
depends_on: []
depended_by:
  - tests/conftest.py
  - teams/*/tests/conftest.py
semver: minor
"""

import pytest
from unittest.mock import AsyncMock, patch
from typing import Generator, AsyncGenerator
from datetime import datetime, timezone


@pytest.fixture
def mock_neon_session() -> Generator[AsyncMock, None, None]:
    """Mock Neon database session for unit tests."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    yield session


@pytest.fixture
def mock_mlflow() -> Generator[AsyncMock, None, None]:
    """Mock MLflow for unit tests."""
    with patch("mlflow.set_experiment"), \
         patch("mlflow.start_span") as mock_span, \
         patch("mlflow.log_metrics"), \
         patch("mlflow.anthropic.autolog"):
        yield mock_span


@pytest.fixture
def frozen_time() -> datetime:
    """Frozen datetime for deterministic tests."""
    return datetime(2026, 2, 11, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_llms_txt() -> str:
    """Sample llms.txt content for testing."""
    return """# Example API
> This is an AI-friendly documentation site.

## Endpoints
- /api/v1/users: User management
- /api/v1/tasks: Task operations

## Authentication
> Bearer token required for all endpoints.
"""
```

---

## Phase 5: CI/CD Pipeline

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--unsafe]  # Allow custom tags
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0, sqlalchemy>=2.0]
        args: [--strict]

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/ -x -q --tb=short
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
```

### GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv pip install -e ".[dev]"
      - uses: astral-sh/ruff-action@v2

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv pip install -e ".[dev]"
      - run: mypy core/ teams/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv pip install -e ".[dev]"
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          fail_ci_if_error: false

  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: pre-commit/action@v3.0.1
```

---

## Phase 6: Neon Schema for LLMs.txt

### Migration: `migrations/001_llms_txt_documents.sql`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- LLMs.txt documents table
CREATE TABLE llms_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN ('llms.txt', 'llms-full.txt')),
    content_hash TEXT NOT NULL,  -- SHA-256 of raw content
    raw_content TEXT NOT NULL,
    parsed_json JSONB NOT NULL,  -- Structured parse result
    embedding vector(1536),      -- OpenAI ada-002 or similar
    last_fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Action items extracted from documents
CREATE TABLE llms_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES llms_documents(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,   -- 'endpoint', 'tool', 'resource', etc.
    action_path TEXT NOT NULL,   -- Path from document
    description TEXT,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cross-document links
CREATE TABLE llms_deep_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_id UUID REFERENCES llms_documents(id) ON DELETE CASCADE,
    target_document_id UUID REFERENCES llms_documents(id) ON DELETE CASCADE,
    link_type TEXT NOT NULL,     -- 'references', 'extends', 'similar'
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_document_id, target_document_id, link_type)
);

-- Performance indexes
CREATE INDEX idx_llms_documents_domain ON llms_documents(domain);
CREATE INDEX idx_llms_documents_type ON llms_documents(document_type);
CREATE INDEX idx_llms_documents_updated ON llms_documents(updated_at DESC);

-- Vector similarity indexes (IVFFlat for < 1M rows)
CREATE INDEX idx_llms_documents_embedding ON llms_documents
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_llms_actions_embedding ON llms_actions
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_llms_documents_updated_at
    BEFORE UPDATE ON llms_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### LLMs.txt Parser

```python
# core/crawlers/llms_txt.py
"""LLMs.txt parser for AI-readable documentation.

schema: llms_documents
depends_on:
  - core/db/engine.py
depended_by:
  - teams/claude-ops/lib/crawler.py
semver: minor

Reference: https://llmstxt.org/
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class LLMsAction:
    """Extracted action from llms.txt document."""
    action_type: str  # 'endpoint', 'tool', 'resource', 'section'
    path: str
    description: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMsDocument:
    """Parsed llms.txt document."""
    url: str
    domain: str
    document_type: str  # 'llms.txt' or 'llms-full.txt'
    raw_content: str
    content_hash: str
    title: Optional[str] = None
    description: Optional[str] = None
    actions: list[LLMsAction] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def parse_llms_txt(url: str, content: str) -> LLMsDocument:
    """Parse llms.txt content into structured document.

    Args:
        url: Source URL of the document
        content: Raw text content

    Returns:
        Parsed LLMsDocument with extracted actions

    Raises:
        ValueError: If content is empty or malformed
    """
    if not content or not content.strip():
        raise ValueError("Empty llms.txt content")

    # Extract domain from URL
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Determine document type
    doc_type = "llms-full.txt" if "llms-full" in url else "llms.txt"

    # Calculate content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Parse content
    lines = content.split("\n")
    actions: list[LLMsAction] = []
    sections: dict[str, str] = {}
    current_section: Optional[str] = None
    section_content: list[str] = []
    title: Optional[str] = None
    description: Optional[str] = None

    for line in lines:
        line = line.rstrip()

        # Title (# at start of document)
        if line.startswith("# ") and title is None:
            title = line[2:].strip()
            continue

        # Section header (##)
        if line.startswith("## "):
            # Save previous section
            if current_section:
                sections[current_section] = "\n".join(section_content)
            current_section = line[3:].strip()
            section_content = []
            continue

        # Description block (> at start)
        if line.startswith("> "):
            desc_text = line[2:].strip()
            if description is None:
                description = desc_text
            else:
                section_content.append(desc_text)
            continue

        # Action item (- path: description)
        if line.startswith("- "):
            action_text = line[2:].strip()
            if ":" in action_text:
                path, desc = action_text.split(":", 1)
                actions.append(LLMsAction(
                    action_type="endpoint" if path.startswith("/") else "resource",
                    path=path.strip(),
                    description=desc.strip(),
                    metadata={"section": current_section} if current_section else {},
                ))
            else:
                actions.append(LLMsAction(
                    action_type="item",
                    path=action_text,
                    metadata={"section": current_section} if current_section else {},
                ))
            continue

        # Regular content
        if line and current_section:
            section_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = "\n".join(section_content)

    return LLMsDocument(
        url=url,
        domain=domain,
        document_type=doc_type,
        raw_content=content,
        content_hash=content_hash,
        title=title,
        description=description,
        actions=actions,
        sections=sections,
    )
```

---

## Implementation Checklist

### Phase 1: Core Package Setup
- [ ] Create `core/` directory structure
- [ ] Move shared code from `pm/lib/frontmatter.py` to `core/`
- [ ] Create `core/base/` with BaseAgent, BaseEntity, BaseTeam
- [ ] Add `pyproject.toml` with dev dependencies
- [ ] Add `tests/conftest.py` with shared fixtures
- [ ] Update imports in existing code to use `core/`

### Phase 2: MLflow Integration
- [ ] Create `core/tracing/mlflow_hooks.py`
- [ ] Integrate with existing `activity_tracker` pattern from team-agents-sdk
- [ ] Add experiment tracking per team
- [ ] Create `core/tracing/cost_tracker.py` for token costs

### Phase 3: Claude Ops Team
- [ ] Run `templates/create-team.py --name "Claude Ops"` to scaffold
- [ ] Add custom agents (ops-orchestrator, vercel-specialist, neon-specialist, release-reviewer)
- [ ] Implement `core/crawlers/llms_txt.py` parser
- [ ] Create Neon migration for llms_documents tables
- [ ] Add release reviewer automation with GitHub webhook

### Phase 4: CI/CD Hardening
- [ ] Create `.pre-commit-config.yaml`
- [ ] Create `.github/workflows/ci.yml`
- [ ] Add Codecov integration
- [ ] Set up Dependabot for dependencies

### Phase 5: Testing
- [ ] Write tests for `core/base/` classes
- [ ] Write tests for `core/tracing/` hooks
- [ ] Write tests for `core/crawlers/llms_txt.py`
- [ ] Achieve 80% coverage minimum
- [ ] Add integration tests against Neon (guarded by env var)

### Phase 6: Documentation
- [ ] Update `CLAUDE.md` with testing requirements
- [ ] Update `templates/create-team.py` to include core/ imports
- [ ] Add `ARCHITECTURE.md` for core/ package
- [ ] Create migration guide for existing teams

---

## Verification Criteria

After implementation:
1. `make test` passes with coverage >= 80%
2. `pre-commit run --all-files` passes
3. All teams can import from `core/` without circular dependencies
4. MLflow traces appear in dashboard for all team activities
5. LLMs.txt documents ingested to Neon with pgvector embeddings
6. Claude Code releases trigger automated review workflow
7. CI/CD pipeline blocks PRs with failing tests or lint errors

---

## Open Questions

1. **Team directory location**: Should teams move from root to `teams/` subdirectory, or stay at root level?
2. **Embedding model**: Use OpenAI ada-002 (1536-dim) or switch to Anthropic embeddings when available?
3. **MLflow deployment**: Self-hosted vs managed (Databricks, AWS)?
4. **LLMs.txt crawl frequency**: Daily? Weekly? On-demand only?

---

## References

- [LLMs.txt Specification](https://llmstxt.org/)
- [MLflow 3.9 Tracing](https://mlflow.org/docs/latest/llms/tracing/index.html)
- [Neon pgvector](https://neon.tech/docs/extensions/pgvector)
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Pre-commit](https://pre-commit.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
