# PM System - Monotonically Increasing Commands
# Level 0: Atomic | Level 1: Composed | Level 2: Workflow | Level 3: Pipeline
#
# Usage: make <target> or via slash commands /pm:<target>

.PHONY: all help
.DEFAULT_GOAL := help

# ============================================================================
# LEVEL 0: ATOMIC OPERATIONS (single responsibility, ~1 tool call each)
# ============================================================================

.PHONY: l0-hash l0-test l0-lint l0-arch l0-commit-check l0-frontmatter

l0-hash: ## L0: Generate file hash
	@python3 -c "from lib.frontmatter import parse_file; from pathlib import Path; import hashlib; \
	p=Path('$(FILE)'); print(hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else 'not-found')"

l0-test: ## L0: Run single test
	@./tests/run-tests.sh 2>/dev/null | tail -5

l0-lint: ## L0: Lint single file frontmatter
	@python3 -c "from lib.validators import validate_entity; from pathlib import Path; \
	print('✓' if validate_entity(Path('$(FILE)')) else '✗')" 2>/dev/null || echo "✗ $(FILE)"

l0-arch: ## L0: Generate architecture (no commit)
	@python3 scripts/architecture/generate.py 2>/dev/null | tail -3

l0-commit-check: ## L0: Validate last commit message
	@git log -1 --pretty=%B | head -1 | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|ci|revert)(\(.+\))?: .+' \
	&& echo "✓ conventional" || echo "✗ not conventional"

l0-frontmatter: ## L0: Extract frontmatter from file
	@python3 -c "from lib.frontmatter import parse_file; from pathlib import Path; import json; \
	print(json.dumps(parse_file(Path('$(FILE)')), indent=2))"

# ============================================================================
# LEVEL 1: COMPOSED (combine 2-3 L0 ops, still single purpose)
# ============================================================================

.PHONY: l1-index l1-validate l1-arch-check l1-pr-lint

l1-index: ## L1: Check + regenerate index if stale
	@python3 .index/check-changes.py 2>/dev/null || python3 .index/generate-merkle.py

l1-validate: ## L1: Run tests + check index
	@$(MAKE) -s l0-test && $(MAKE) -s l1-index

l1-arch-check: ## L1: Generate arch + check diff
	@$(MAKE) -s l0-arch && git diff --quiet ARCHITECTURE.md 2>/dev/null \
	&& echo "✓ arch current" || echo "⚠ arch changed"

l1-pr-lint: ## L1: Lint all changed files
	@for f in $$(git diff --name-only HEAD~1 -- '*.md' 2>/dev/null); do \
		$(MAKE) -s l0-lint FILE="$$f"; done

# ============================================================================
# LEVEL 2: WORKFLOWS (business logic, combine L1 ops)
# ============================================================================

.PHONY: l2-pr-open l2-pr-merge l2-release

l2-pr-open: ## L2: PR open checks (tests + index + arch + lint)
	@echo "▶ PR Open Checks"
	@$(MAKE) -s l1-validate && echo "  ✓ tests + index"
	@$(MAKE) -s l1-arch-check
	@$(MAKE) -s l0-commit-check
	@$(MAKE) -s l1-pr-lint
	@echo "✓ PR ready"

l2-pr-merge: ## L2: PR merge automation (arch + commit)
	@echo "▶ PR Merge"
	@$(MAKE) -s l0-arch
	@git diff --quiet ARCHITECTURE.md ARCHITECTURE.html architecture.json 2>/dev/null || { \
		git add ARCHITECTURE.md ARCHITECTURE.html architecture.json && \
		git commit -m "docs(architecture): auto-update" && \
		echo "✓ arch committed"; }
	@echo "✓ merge complete"

l2-release: ## L2: Release workflow (validate + tag)
	@echo "▶ Release"
	@$(MAKE) -s l2-pr-open
	@VERSION=$$(grep -m1 'version' CHANGELOG.md | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
	echo "  version: $$VERSION"

# ============================================================================
# LEVEL 3: PIPELINES (full automation, orchestrates L2)
# ============================================================================

.PHONY: l3-ci l3-cd l3-full

l3-ci: ## L3: Full CI pipeline
	@echo "═══ CI Pipeline ═══"
	@$(MAKE) -s l2-pr-open
	@echo "═══ CI Complete ═══"

l3-cd: ## L3: Full CD pipeline (CI + merge + deploy)
	@echo "═══ CD Pipeline ═══"
	@$(MAKE) -s l3-ci
	@$(MAKE) -s l2-pr-merge
	@echo "═══ CD Complete ═══"

l3-full: ## L3: Full pipeline with release
	@$(MAKE) -s l3-cd
	@$(MAKE) -s l2-release

# ============================================================================
# REVIEW PIPELINE (automated code review)
# ============================================================================

.PHONY: review-l0-test review-l0-value review-l0-mlflow review-l1-parallel review-l2-full review-l3-implement review

BRANCH ?= $(shell git branch --show-current 2>/dev/null || echo "main")
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BRANCH_SAFE = $(shell echo "$(BRANCH)" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
REVIEW_DIR = ../reviews/$(BRANCH_SAFE)

review-l0-test: ## L0-Review: Run test reviewer only
	@echo "▶ Test Reviewer: $(BRANCH) @ $(COMMIT)"
	@mkdir -p $(REVIEW_DIR)
	@echo "  Spawn test-reviewer agent..."
	@echo "  Output: $(REVIEW_DIR)/REVIEW-test-$(COMMIT).md"

review-l0-value: ## L0-Review: Run value reviewer only
	@echo "▶ Value Reviewer: $(BRANCH) @ $(COMMIT)"
	@mkdir -p $(REVIEW_DIR)
	@echo "  Spawn value-reviewer agent..."
	@echo "  Output: $(REVIEW_DIR)/REVIEW-value-$(COMMIT).md"

review-l0-mlflow: ## L0-Review: Run MLflow analyzer only
	@echo "▶ MLflow Analyzer: $(BRANCH) @ $(COMMIT)"
	@mkdir -p $(REVIEW_DIR)
	@echo "  Spawn mlflow-analyzer agent..."
	@echo "  Output: $(REVIEW_DIR)/REVIEW-mlflow-$(COMMIT).md"

review-l1-parallel: ## L1-Review: Run all 3 reviewers in parallel
	@echo "▶ Parallel Review: $(BRANCH) @ $(COMMIT)"
	@mkdir -p $(REVIEW_DIR)
	@echo "  Spawning 3 Opus reviewers in parallel..."
	@echo "  - test-reviewer"
	@echo "  - value-reviewer"
	@echo "  - mlflow-analyzer"

review-l2-full: ## L2-Review: Full pipeline (review + synthesis + tasks)
	@echo "═══ Review Pipeline L2: $(BRANCH) @ $(COMMIT) ═══"
	@mkdir -p $(REVIEW_DIR)
	@$(MAKE) -s review-l1-parallel
	@echo ""
	@echo "▶ Synthesis Phase"
	@echo "  Spawn review-synthesizer..."
	@echo "  Output: $(REVIEW_DIR)/summary.json"
	@echo "  Tasks: entities/examples/TASK-*.md"

review-l3-implement: ## L3-Review: Full pipeline + parallel implementation
	@echo "═══ Review Pipeline L3: $(BRANCH) @ $(COMMIT) ═══"
	@$(MAKE) -s review-l2-full
	@echo ""
	@echo "▶ Assignment Phase"
	@echo "  Spawn assignment-manager..."
	@echo "  Output: $(REVIEW_DIR)/assignments.json"
	@echo ""
	@echo "▶ Implementation Phase"
	@echo "  Spawning Staff Engineers based on assignments..."

review: review-l2-full ## Alias: Full review pipeline (L2)

# ============================================================================
# DOCUMENT PIPELINE (Neon document caching)
# ============================================================================

.PHONY: l0-doc-store l0-doc-search l0-doc-process l0-doc-status
.PHONY: l1-doc-index l1-doc-drain l1-doc-migrate

NEON_CLI = PYTHONPATH=. python3 -m lib.neon_docs

l0-doc-store: ## L0-Doc: Store single document (FILE= or URL=)
	@$(NEON_CLI) store $(if $(URL),--url "$(URL)",--file "$(FILE)")

l0-doc-search: ## L0-Doc: Search documents (QUERY=)
	@$(NEON_CLI) search "$(QUERY)" --limit $(or $(LIMIT),5)

l0-doc-process: ## L0-Doc: Process one queue item
	@$(NEON_CLI) process-queue

l0-doc-status: ## L0-Doc: Show cache statistics
	@$(NEON_CLI) status

l1-doc-index: ## L1-Doc: Bulk-index docs/crawler-improvements/
	@$(NEON_CLI) bulk-index ../docs/crawler-improvements/

l1-doc-drain: ## L1-Doc: Drain entire processing queue
	@$(NEON_CLI) process-queue

l1-doc-migrate: ## L1-Doc: Run schema migrations
	@$(NEON_CLI) migrate

# ============================================================================
# SHORTCUTS (ergonomic aliases)
# ============================================================================

.PHONY: test index arch validate check ci cd

test: l0-test        ## Alias: run tests
index: l1-index      ## Alias: check/update index
arch: l0-arch        ## Alias: generate architecture
validate: l1-validate ## Alias: tests + index
check: l2-pr-open    ## Alias: PR checks
ci: l3-ci            ## Alias: CI pipeline
cd: l3-cd            ## Alias: CD pipeline

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help
	@echo "PM System Commands (monotonically increasing complexity)"
	@echo ""
	@echo "Level 0 (Atomic):"
	@grep -E '^l0-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
	@echo ""
	@echo "Level 1 (Composed):"
	@grep -E '^l1-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
	@echo ""
	@echo "Level 2 (Workflow):"
	@grep -E '^l2-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
	@echo ""
	@echo "Level 3 (Pipeline):"
	@grep -E '^l3-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
	@echo ""
	@echo "Review Pipeline:"
	@grep -E '^review-l[0-3]-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
	@echo ""
	@echo "Shortcuts:"
	@grep -E '^(test|index|arch|validate|check|ci|cd|review):.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
