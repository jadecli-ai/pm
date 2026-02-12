"""PM System Tools for Agent SDK programmatic calling.

Implements monotonically increasing tool hierarchy:
- Level 0: Atomic (single operation)
- Level 1: Composed (2-3 atomics)
- Level 2: Workflow (business logic)
- Level 3: Pipeline (full automation)

Usage with Agent SDK:
    from lib.tools import PMTools
    tools = PMTools(project_root)
    result = tools.l0_test()
    result = tools.l2_pr_open()
"""

import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: str
    level: int
    tool: str
    tokens_approx: int  # Approximate output tokens


class PMTools:
    """PM System tools with monotonically increasing complexity.

    Token-efficient: Each level minimizes output while maintaining quality.
    Latency-optimized: Higher levels parallelize where possible.
    """

    def __init__(self, project_root: Path | str = None):
        self.root = Path(project_root) if project_root else Path(__file__).parent.parent

    def _run(self, cmd: str, level: int, tool: str) -> ToolResult:
        """Execute command and return structured result."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout.strip() or result.stderr.strip()
            return ToolResult(
                success=result.returncode == 0,
                output=output[:500],  # Cap output for token efficiency
                level=level,
                tool=tool,
                tokens_approx=len(output.split())
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "timeout", level, tool, 1)
        except Exception as e:
            return ToolResult(False, str(e)[:100], level, tool, 10)

    def _make(self, target: str, level: int, **kwargs) -> ToolResult:
        """Run make target with optional args."""
        args = " ".join(f"{k}={v}" for k, v in kwargs.items())
        cmd = f"make -s {target} {args}".strip()
        return self._run(cmd, level, target)

    # =========================================================================
    # LEVEL 0: ATOMIC
    # =========================================================================

    def l0_test(self) -> ToolResult:
        """Run tests. ~50 tokens output."""
        return self._make("l0-test", 0)

    def l0_arch(self) -> ToolResult:
        """Generate architecture. ~30 tokens output."""
        return self._make("l0-arch", 0)

    def l0_lint(self, file: str) -> ToolResult:
        """Lint single file. ~5 tokens output."""
        return self._make("l0-lint", 0, FILE=file)

    def l0_hash(self, file: str) -> ToolResult:
        """Get file hash. ~20 tokens output."""
        return self._make("l0-hash", 0, FILE=file)

    def l0_commit_check(self) -> ToolResult:
        """Check commit message. ~5 tokens output."""
        return self._make("l0-commit-check", 0)

    def l0_frontmatter(self, file: str) -> ToolResult:
        """Extract frontmatter. ~50 tokens output."""
        return self._make("l0-frontmatter", 0, FILE=file)

    # =========================================================================
    # LEVEL 1: COMPOSED
    # =========================================================================

    def l1_index(self) -> ToolResult:
        """Check and regenerate index. ~30 tokens output."""
        return self._make("l1-index", 1)

    def l1_validate(self) -> ToolResult:
        """Run tests + check index. ~60 tokens output."""
        return self._make("l1-validate", 1)

    def l1_arch_check(self) -> ToolResult:
        """Generate arch + check diff. ~40 tokens output."""
        return self._make("l1-arch-check", 1)

    def l1_pr_lint(self) -> ToolResult:
        """Lint all changed files. ~20 tokens per file."""
        return self._make("l1-pr-lint", 1)

    # =========================================================================
    # LEVEL 2: WORKFLOW
    # =========================================================================

    def l2_pr_open(self) -> ToolResult:
        """Full PR open checks. ~150 tokens output."""
        return self._make("l2-pr-open", 2)

    def l2_pr_merge(self) -> ToolResult:
        """PR merge automation. ~100 tokens output."""
        return self._make("l2-pr-merge", 2)

    def l2_release(self) -> ToolResult:
        """Release workflow. ~200 tokens output."""
        return self._make("l2-release", 2)

    # =========================================================================
    # LEVEL 3: PIPELINE
    # =========================================================================

    def l3_ci(self) -> ToolResult:
        """Full CI pipeline. ~200 tokens output."""
        return self._make("l3-ci", 3)

    def l3_cd(self) -> ToolResult:
        """Full CD pipeline. ~300 tokens output."""
        return self._make("l3-cd", 3)

    def l3_full(self) -> ToolResult:
        """Full pipeline with release. ~400 tokens output."""
        return self._make("l3-full", 3)

    # =========================================================================
    # CHAINING HELPERS
    # =========================================================================

    def chain(self, *tools: Callable[[], ToolResult]) -> list[ToolResult]:
        """Execute tools in sequence, stop on first failure.

        Example:
            tools.chain(tools.l0_test, tools.l0_arch)
        """
        results = []
        for tool in tools:
            result = tool()
            results.append(result)
            if not result.success:
                break
        return results

    def parallel(self, *tools: Callable[[], ToolResult]) -> list[ToolResult]:
        """Execute tools in parallel (future: actual parallelism).

        Currently sequential, but API supports future optimization.
        """
        return [tool() for tool in tools]

    def to_json(self, result: ToolResult) -> str:
        """Convert result to JSON for Agent SDK consumption."""
        return json.dumps({
            "success": result.success,
            "output": result.output,
            "level": result.level,
            "tool": result.tool,
            "tokens": result.tokens_approx
        })


# Singleton for quick access
_tools: PMTools | None = None

def get_tools() -> PMTools:
    """Get singleton PMTools instance."""
    global _tools
    if _tools is None:
        _tools = PMTools()
    return _tools


# Agent SDK compatible function signatures
def pm_test() -> dict:
    """Run tests (Agent SDK compatible)."""
    r = get_tools().l0_test()
    return {"success": r.success, "output": r.output}

def pm_validate() -> dict:
    """Validate PR (Agent SDK compatible)."""
    r = get_tools().l1_validate()
    return {"success": r.success, "output": r.output}

def pm_ci() -> dict:
    """Run CI pipeline (Agent SDK compatible)."""
    r = get_tools().l3_ci()
    return {"success": r.success, "output": r.output}
