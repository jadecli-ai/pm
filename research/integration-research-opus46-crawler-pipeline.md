# Integration Research: Neon Crawler Pipeline + Modular Infrastructure

> Opus 4.6 Extended Thinking Agent Requirements for Full Implementation

## Executive Summary

The Neon Crawler Pipeline architecture represents a significant enhancement to the `modular-infrastructure-proposal` (Issue #4). Integration requires **Opus 4.6 extended thinking agents** with sophisticated context management due to:

1. **Multi-component orchestration** (Docker + Neon + Vercel + Ollama)
2. **Complex schema dependencies** (6 interrelated tables with embeddings)
3. **Asynchronous task pipeline** (pgqueuer with 6 enrichment task types)
4. **Cross-language code generation** (Python workers + TypeScript dashboard)

---

## Key Differences: Proposal vs Pipeline Architecture

| Aspect | Issue #4 Proposal | Pipeline Architecture |
|--------|-------------------|----------------------|
| **Embedding dimension** | 1536 (OpenAI ada-002) | 768 (Ollama nomic-embed-text) |
| **Task queue** | None specified | pgqueuer (Postgres LISTEN/NOTIFY) |
| **LLM backend** | External API | Local Ollama (llama3.1:8b, mistral:7b) |
| **Schema tables** | 3 (llms_documents, llms_actions, llms_deep_links) | 5 (raw_pages, page_embeddings, page_metadata, crawl_jobs, code_snippets) |
| **Dashboard** | Not specified | Next.js 15 with 8 pages |
| **Infrastructure** | Neon only | Docker + Neon + Vercel + Ollama |

---

## Integration Recommendations

### 1. Schema Unification

**Merge the two schemas** - the pipeline schema is more comprehensive:

```sql
-- Unified schema (combines both approaches)
CREATE TABLE llms_documents (
    -- From Issue #4
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN ('llms.txt', 'llms-full.txt')),
    content_hash TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    parsed_json JSONB NOT NULL,

    -- From Pipeline (additional columns)
    http_status INTEGER,
    headers_json JSONB,
    crawl_duration_ms INTEGER,

    -- Timestamps
    last_fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Use 768-dim for local Ollama, 1536-dim for OpenAI
-- Support both with separate columns or dynamic dimension
CREATE TABLE llms_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES llms_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_768 vector(768),      -- Ollama nomic-embed-text
    embedding_1536 vector(1536),    -- OpenAI ada-002 (optional)
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2. Embedding Model Strategy

**Recommendation**: Use Ollama locally for development, OpenAI for production

| Environment | Model | Dimension | Cost |
|-------------|-------|-----------|------|
| Local dev | nomic-embed-text | 768 | Free |
| CI/CD | mxbai-embed-large | 1024 | Free |
| Production | text-embedding-3-small | 1536 | $0.02/1M tokens |

**Implementation**:
```python
# core/crawlers/embeddings.py
from typing import Protocol, Literal

class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""
    dimension: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...

class OllamaEmbeddings:
    """Local Ollama embeddings (768-dim)."""
    dimension = 768
    model = "nomic-embed-text"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Call http://ollama:11434/api/embeddings
        ...

class OpenAIEmbeddings:
    """OpenAI embeddings (1536-dim)."""
    dimension = 1536
    model = "text-embedding-3-small"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Call OpenAI API
        ...
```

### 3. pgqueuer Integration

**Add to `core/db/`** - this is a critical missing component:

```python
# core/db/queuer.py
"""pgqueuer task queue integration.

schema: N/A (infrastructure)
depends_on:
  - core/db/engine.py
depended_by:
  - teams/claude-ops/lib/enrichment.py
semver: minor
"""

from pgqueuer import PGQueuer
from pgqueuer.decorators import task
from typing import Callable, TypeVar

T = TypeVar("T")

class EnrichmentQueue:
    """Task queue for llms.txt enrichment pipeline."""

    def __init__(self, database_url: str):
        self.queuer = PGQueuer(database_url)

    @task("generate_embeddings")
    async def generate_embeddings(self, document_id: str) -> None:
        """Generate embeddings for a document."""
        ...

    @task("extract_metadata")
    async def extract_metadata(self, document_id: str) -> None:
        """Extract structured metadata via LLM."""
        ...

    @task("classify_content")
    async def classify_content(self, document_id: str) -> None:
        """Classify document type."""
        ...

    @task("extract_links")
    async def extract_links(self, document_id: str) -> None:
        """Extract outbound links for recursive crawling."""
        ...

    @task("summarize")
    async def summarize(self, document_id: str) -> None:
        """Generate document summary."""
        ...

    @task("extract_code_snippets")
    async def extract_code_snippets(self, document_id: str) -> None:
        """Extract code blocks from document."""
        ...
```

### 4. Docker Compose for Local Development

**Add to `.claude-org/docker/`**:

```yaml
# docker/docker-compose.yml
version: "3.9"

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  crawler:
    build:
      context: ../teams/claude-ops
      dockerfile: Dockerfile.crawler
    environment:
      - DATABASE_URL=${NEON_DATABASE_URL}
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

  enrichment:
    build:
      context: ../teams/claude-ops
      dockerfile: Dockerfile.enrichment
    environment:
      - DATABASE_URL=${NEON_DATABASE_URL}
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    command: python -m pgqueuer run enrichment_worker
    deploy:
      replicas: 3  # Scale enrichment workers

volumes:
  ollama_data:
```

### 5. Vercel Dashboard Integration

**Enhance the proposal** with specific dashboard pages:

```
teams/claude-ops/dashboard/
├── app/
│   ├── page.tsx                 # Overview: crawl status, stats
│   ├── crawl-jobs/
│   │   └── page.tsx             # Job list with progress
│   ├── documents/
│   │   ├── page.tsx             # Browse llms_documents
│   │   └── [id]/page.tsx        # Document detail
│   ├── embeddings/
│   │   └── page.tsx             # Vector search UI
│   ├── enrichment/
│   │   └── page.tsx             # pgqueuer queue status
│   └── analytics/
│       └── page.tsx             # Charts: throughput, costs
├── lib/
│   └── db.ts                    # @neondatabase/serverless
└── package.json
```

---

## Opus 4.6 Extended Thinking Requirements

### Why Extended Thinking is Required

| Challenge | Complexity | Extended Thinking Need |
|-----------|------------|----------------------|
| Multi-file code generation | High | Maintain consistency across 20+ files |
| Schema migration planning | High | Track dependencies, rollback paths |
| Docker networking | Medium | Service discovery, GPU passthrough |
| Async pipeline debugging | High | Trace task flow across workers |
| Cross-language coherence | High | Python workers ↔ TypeScript dashboard |

### Recommended Agent Architecture

```yaml
# agents/opus-pipeline-architect.md
---
name: opus-pipeline-architect
model: claude-opus-4-6-20260201
max_turns: 50
extended_thinking: true
thinking_budget: 32000  # Max thinking tokens
context_window: 200000
wrap_up_threshold: 0.75

tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Task  # For spawning sub-agents

steering:
  enabled: true
  handoff_to: opus-pipeline-implementer

responsibilities:
  - Design unified schema merging both proposals
  - Plan migration sequence with rollback points
  - Architect pgqueuer task pipeline
  - Design Docker service topology
  - Coordinate sub-agents for implementation
---

# Opus Pipeline Architect

You are the lead architect for the Neon Crawler Pipeline integration.

## Context

You have access to:
1. `/research/neon-crawler-pipeline-architecture.json` - Full pipeline spec
2. `/issues/modular-infrastructure-proposal.md` - GitHub Issue #4
3. `/teams/claude-ops/` - Target team directory

## Your Mission

Design and coordinate the integration of the Neon Crawler Pipeline into
the jadecli-ai organization infrastructure.

## Extended Thinking Protocol

For complex decisions, use extended thinking to:
1. Enumerate all options
2. Evaluate trade-offs
3. Consider failure modes
4. Document decision rationale

## Handoff Protocol

At 75% budget, hand off to `opus-pipeline-implementer` with:
- Finalized schema SQL
- pgqueuer task definitions
- Docker compose configuration
- Dashboard page specifications
```

### Sub-Agent Team

| Agent | Model | Role |
|-------|-------|------|
| `opus-pipeline-architect` | Opus 4.6 | Lead architect, extended thinking |
| `opus-pipeline-implementer` | Opus 4.5 | Code generation, file writing |
| `sonnet-schema-migrator` | Sonnet 4.5 | SQL migrations, Neon branching |
| `sonnet-docker-specialist` | Sonnet 4.5 | Docker compose, Ollama config |
| `haiku-test-runner` | Haiku 3.5 | Run tests, validate migrations |

---

## Implementation Phases

### Phase 1: Schema & Infrastructure (Week 1)

1. **Merge schemas** into unified `llms_documents` structure
2. **Add pgqueuer** to dependencies and configure
3. **Create Docker setup** for local Ollama development
4. **Write migrations** for Neon (use branching workflow)

### Phase 2: Core Crawler (Week 2)

1. **Implement `core/crawlers/llms_txt.py`** (already drafted in Issue #4)
2. **Add embedding providers** (Ollama + OpenAI Protocol)
3. **Implement pgqueuer tasks** for enrichment pipeline
4. **Write integration tests** against Neon branch

### Phase 3: Workers & Queue (Week 3)

1. **Build Docker images** for crawler and enrichment workers
2. **Configure GPU passthrough** for Ollama
3. **Implement task handlers** for all 6 enrichment types
4. **Add monitoring** (MLflow traces for each task)

### Phase 4: Dashboard (Week 4)

1. **Scaffold Next.js app** with shadcn/ui
2. **Connect to Neon** via serverless driver
3. **Build all 8 pages** from pipeline spec
4. **Deploy to Vercel** with preview branching

---

## Resource Links

### Neon Documentation
- [TypeScript SDK](https://neon.com/docs/reference/typescript-sdk)
- [Python SDK](https://neon.com/docs/reference/python-sdk)
- [AI Agent Integration](https://neon.com/docs/guides/ai-agent-integration)
- [Vercel Integration](https://neon.com/docs/guides/neon-managed-vercel-integration)
- [@neondatabase/toolkit](https://neon.com/docs/reference/neondatabase-toolkit)

### pgqueuer
- [GitHub](https://github.com/janbjorge/pgqueuer)
- [Documentation](https://pgqueuer.readthedocs.io/)

### Ollama
- [Models Library](https://ollama.com/library)
- [API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Docker Setup](https://hub.docker.com/r/ollama/ollama)

---

## Pre-Compact Checklist

Before running `/compact`:

- [x] Saved pipeline architecture to `/research/neon-crawler-pipeline-architecture.json`
- [x] Created this integration research document
- [x] Issue #4 exists at https://github.com/jadecli-ai/pm/issues/4
- [x] Identified Opus 4.6 extended thinking requirements
- [ ] Developer reviews and approves integration approach
- [ ] Create Opus 4.6 agent definition file
- [ ] Scaffold Docker and dashboard directories

---

## Next Steps After Compact

1. **Create `agents/opus-pipeline-architect.md`** with extended thinking config
2. **Update Issue #4** with pipeline integration addendum
3. **Run Opus 4.6 agent** to begin schema unification
4. **Set up Docker environment** for local Ollama testing
5. **Create Neon branch** `feature/crawler-pipeline` for safe iteration
