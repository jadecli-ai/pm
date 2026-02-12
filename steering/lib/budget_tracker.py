"""Budget Tracker - Monitors token/turn consumption against budget.

schema: N/A (core library)
depends_on:
  - steering/config/budgets.yaml
  - steering/config/thresholds.yaml
depended_by:
  - steering/hooks/post_tool_use.py
  - agents/steering-orchestrator.md
semver: minor
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
import yaml


class BudgetPhase(str, Enum):
    """Current budget phase based on consumption ratio."""
    NORMAL = "normal"       # < warning threshold
    WARNING = "warning"     # >= warning, < wrap_up
    WRAP_UP = "wrap_up"     # >= wrap_up, < critical
    CRITICAL = "critical"   # >= critical


@dataclass
class BudgetState:
    """Current state of budget consumption."""
    # Turn tracking
    current_turn: int
    max_turns: int

    # Token tracking
    tokens_consumed: int
    token_budget: int

    # Calculated values
    turn_ratio: float
    token_ratio: float
    budget_ratio: float
    phase: BudgetPhase

    # Thresholds
    wrap_up_threshold: float
    warning_threshold: float
    critical_threshold: float

    # Timestamps
    started_at: datetime
    updated_at: datetime

    def should_wrap_up(self) -> bool:
        """Return True if agent should begin wrap-up."""
        return self.phase in (BudgetPhase.WRAP_UP, BudgetPhase.CRITICAL)

    def is_critical(self) -> bool:
        """Return True if budget is critically low."""
        return self.phase == BudgetPhase.CRITICAL

    def remaining_turns(self) -> int:
        """Return estimated remaining turns."""
        return max(0, self.max_turns - self.current_turn)

    def remaining_tokens(self) -> int:
        """Return estimated remaining tokens."""
        return max(0, self.token_budget - self.tokens_consumed)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "tokens_consumed": self.tokens_consumed,
            "token_budget": self.token_budget,
            "turn_ratio": round(self.turn_ratio, 3),
            "token_ratio": round(self.token_ratio, 3),
            "budget_ratio": round(self.budget_ratio, 3),
            "phase": self.phase.value,
            "remaining_turns": self.remaining_turns(),
            "remaining_tokens": self.remaining_tokens(),
            "should_wrap_up": self.should_wrap_up(),
        }


@dataclass
class BudgetTracker:
    """Tracks token/turn budget consumption for an agent session."""

    # Configuration
    model: str
    max_turns: int
    token_budget: int

    # Thresholds
    wrap_up_threshold: float = 0.80
    warning_threshold: float = 0.70
    critical_threshold: float = 0.90

    # State
    current_turn: int = 0
    tokens_consumed: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _config_dir: Optional[Path] = None

    @classmethod
    def from_config(
        cls,
        model: str,
        config_dir: Optional[Path] = None,
        max_turns_override: Optional[int] = None,
    ) -> "BudgetTracker":
        """Create tracker from configuration files."""
        if config_dir is None:
            # Default to steering/config relative to this file
            config_dir = Path(__file__).parent.parent / "config"

        budgets_file = config_dir / "budgets.yaml"
        thresholds_file = config_dir / "thresholds.yaml"

        # Load budgets
        with open(budgets_file) as f:
            budgets = yaml.safe_load(f)

        # Load thresholds
        with open(thresholds_file) as f:
            thresholds = yaml.safe_load(f)

        # Get model config
        model_config = budgets.get("models", {}).get(model, {})
        if not model_config:
            raise ValueError(f"Unknown model: {model}")

        # Get threshold config
        threshold_config = thresholds.get("thresholds", {})

        return cls(
            model=model,
            max_turns=max_turns_override or model_config.get("default_turns", 15),
            token_budget=model_config.get("token_budget", 160000),
            wrap_up_threshold=threshold_config.get("wrap_up", 0.80),
            warning_threshold=threshold_config.get("warning", 0.70),
            critical_threshold=threshold_config.get("critical", 0.90),
            _config_dir=config_dir,
        )

    def record_turn(self, tokens_used: int = 0) -> BudgetState:
        """Record a turn and optional token usage, return current state."""
        self.current_turn += 1
        self.tokens_consumed += tokens_used
        return self.get_state()

    def record_tokens(self, tokens: int) -> BudgetState:
        """Record token usage without incrementing turn, return current state."""
        self.tokens_consumed += tokens
        return self.get_state()

    def get_state(self) -> BudgetState:
        """Get current budget state."""
        # Calculate ratios
        turn_ratio = self.current_turn / self.max_turns if self.max_turns > 0 else 0.0
        token_ratio = self.tokens_consumed / self.token_budget if self.token_budget > 0 else 0.0
        budget_ratio = max(turn_ratio, token_ratio)

        # Determine phase
        if budget_ratio >= self.critical_threshold:
            phase = BudgetPhase.CRITICAL
        elif budget_ratio >= self.wrap_up_threshold:
            phase = BudgetPhase.WRAP_UP
        elif budget_ratio >= self.warning_threshold:
            phase = BudgetPhase.WARNING
        else:
            phase = BudgetPhase.NORMAL

        return BudgetState(
            current_turn=self.current_turn,
            max_turns=self.max_turns,
            tokens_consumed=self.tokens_consumed,
            token_budget=self.token_budget,
            turn_ratio=turn_ratio,
            token_ratio=token_ratio,
            budget_ratio=budget_ratio,
            phase=phase,
            wrap_up_threshold=self.wrap_up_threshold,
            warning_threshold=self.warning_threshold,
            critical_threshold=self.critical_threshold,
            started_at=self.started_at,
            updated_at=datetime.now(timezone.utc),
        )

    def reset(self) -> None:
        """Reset tracker state."""
        self.current_turn = 0
        self.tokens_consumed = 0
        self.started_at = datetime.now(timezone.utc)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "claude-opus-4-5-20251101"
    turns = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    try:
        tracker = BudgetTracker.from_config(model)
    except FileNotFoundError:
        # Fallback for testing without config files
        tracker = BudgetTracker(
            model=model,
            max_turns=25,
            token_budget=160000,
        )

    # Simulate turns
    for i in range(turns):
        state = tracker.record_turn(tokens_used=5000)
        print(f"Turn {state.current_turn}: {state.phase.value} (ratio: {state.budget_ratio:.2f})")
        if state.should_wrap_up():
            print(f"  -> WRAP-UP TRIGGERED at turn {state.current_turn}")
            break
