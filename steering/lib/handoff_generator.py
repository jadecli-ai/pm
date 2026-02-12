"""Handoff Generator - Creates structured handoff documents for agent transitions.

schema: N/A (core library)
depends_on:
  - steering/lib/budget_tracker.py
  - steering/config/thresholds.yaml
depended_by:
  - steering/hooks/task_completed.py
  - agents/steering-orchestrator.md
semver: minor
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import yaml


class HandoffReason(str, Enum):
    """Reason for triggering handoff."""
    BUDGET_WARNING = "budget_warning_70_percent"
    BUDGET_WRAP_UP = "budget_wrap_up_80_percent"
    BUDGET_CRITICAL = "budget_critical_90_percent"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    EXPLICIT_REQUEST = "explicit_request"
    ERROR_STATE = "error_state"


@dataclass
class ActiveContext:
    """Context about active work items."""
    epic_id: Optional[str] = None
    sprint_id: Optional[str] = None
    task_id: Optional[str] = None
    subtask_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "epic": self.epic_id or "none",
            "sprint": self.sprint_id or "none",
            "task": self.task_id or "none",
            "subtask": self.subtask_id or "none",
        }


@dataclass
class SuccessorInfo:
    """Information about the recommended successor agent."""
    agent: str
    prompt_hint: str
    priority: str = "normal"  # low, normal, high, critical

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "prompt_hint": self.prompt_hint,
            "priority": self.priority,
        }


@dataclass
class BudgetMetrics:
    """Metrics about budget consumption."""
    turns_used: int
    max_turns: int
    tokens_consumed: int
    token_budget: int
    budget_ratio: float
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "turns_used": self.turns_used,
            "max_turns": self.max_turns,
            "tokens_consumed": self.tokens_consumed,
            "token_budget": self.token_budget,
            "budget_ratio": round(self.budget_ratio, 3),
            "duration_seconds": round(self.duration_seconds, 1),
        }


@dataclass
class HandoffDocument:
    """Structured handoff document for agent transitions."""
    reason: HandoffReason
    completed: list[str]
    incomplete: list[str]
    context: ActiveContext
    key_files: list[str]
    decisions: list[str]
    successor: SuccessorInfo
    metrics: BudgetMetrics
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_yaml(self) -> str:
        """Generate YAML representation of handoff document."""
        doc = {
            "reason": self.reason.value,
            "completed": self.completed,
            "incomplete": self.incomplete,
            "context": {
                "active_entities": self.context.to_dict(),
                "key_files": self.key_files,
                "decisions": self.decisions,
            },
            "successor": self.successor.to_dict(),
            "metrics": self.metrics.to_dict(),
        }

        if self.warnings:
            doc["warnings"] = self.warnings
        if self.blockers:
            doc["blockers"] = self.blockers
        if self.artifacts:
            doc["artifacts"] = self.artifacts

        return yaml.dump(doc, default_flow_style=False, sort_keys=False)

    def to_xml(self) -> str:
        """Generate XML representation of handoff document."""
        completed_xml = "\n    ".join(f"<item>{c}</item>" for c in self.completed)
        incomplete_xml = "\n    ".join(f"<item>{i}</item>" for i in self.incomplete)
        key_files_xml = "\n      ".join(f"<file>{f}</file>" for f in self.key_files)
        decisions_xml = "\n      ".join(f"<decision>{d}</decision>" for d in self.decisions)

        warnings_section = ""
        if self.warnings:
            warnings_xml = "\n    ".join(f"<warning>{w}</warning>" for w in self.warnings)
            warnings_section = f"""
  <warnings>
    {warnings_xml}
  </warnings>"""

        blockers_section = ""
        if self.blockers:
            blockers_xml = "\n    ".join(f"<blocker>{b}</blocker>" for b in self.blockers)
            blockers_section = f"""
  <blockers>
    {blockers_xml}
  </blockers>"""

        xml = f"""<handoff>
  <reason>{self.reason.value}</reason>

  <completed>
    {completed_xml or "<item>none</item>"}
  </completed>

  <incomplete>
    {incomplete_xml or "<item>none</item>"}
  </incomplete>

  <context>
    <active_entities>
      <epic>{self.context.epic_id or "none"}</epic>
      <sprint>{self.context.sprint_id or "none"}</sprint>
      <task>{self.context.task_id or "none"}</task>
    </active_entities>
    <key_files>
      {key_files_xml or "<file>none</file>"}
    </key_files>
    <decisions>
      {decisions_xml or "<decision>none</decision>"}
    </decisions>
  </context>

  <successor>
    <agent>{self.successor.agent}</agent>
    <prompt_hint>{self.successor.prompt_hint}</prompt_hint>
    <priority>{self.successor.priority}</priority>
  </successor>

  <metrics>
    <turns_used>{self.metrics.turns_used}</turns_used>
    <max_turns>{self.metrics.max_turns}</max_turns>
    <budget_ratio>{self.metrics.budget_ratio:.2f}</budget_ratio>
  </metrics>{warnings_section}{blockers_section}
</handoff>"""

        return xml


class HandoffGenerator:
    """Generates handoff documents from agent state."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.completed: list[str] = []
        self.incomplete: list[str] = []
        self.key_files: list[str] = []
        self.decisions: list[str] = []
        self.warnings: list[str] = []
        self.blockers: list[str] = []
        self.artifacts: list[str] = []
        self.context = ActiveContext()

    def add_completed(self, item: str) -> "HandoffGenerator":
        """Add a completed item."""
        self.completed.append(item)
        return self

    def add_incomplete(self, item: str) -> "HandoffGenerator":
        """Add an incomplete item."""
        self.incomplete.append(item)
        return self

    def add_key_file(self, path: str) -> "HandoffGenerator":
        """Add a key file to context."""
        self.key_files.append(path)
        return self

    def add_decision(self, decision: str) -> "HandoffGenerator":
        """Add an architectural decision."""
        self.decisions.append(decision)
        return self

    def add_warning(self, warning: str) -> "HandoffGenerator":
        """Add a warning for successor."""
        self.warnings.append(warning)
        return self

    def add_blocker(self, blocker: str) -> "HandoffGenerator":
        """Add a blocker."""
        self.blockers.append(blocker)
        return self

    def add_artifact(self, artifact: str) -> "HandoffGenerator":
        """Add an artifact (file created/modified)."""
        self.artifacts.append(artifact)
        return self

    def set_context(
        self,
        epic_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        task_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
    ) -> "HandoffGenerator":
        """Set active context."""
        self.context = ActiveContext(
            epic_id=epic_id,
            sprint_id=sprint_id,
            task_id=task_id,
            subtask_id=subtask_id,
        )
        return self

    def generate(
        self,
        reason: HandoffReason,
        successor_agent: str,
        prompt_hint: str,
        metrics: BudgetMetrics,
        priority: str = "normal",
    ) -> HandoffDocument:
        """Generate the handoff document."""
        return HandoffDocument(
            reason=reason,
            completed=self.completed.copy(),
            incomplete=self.incomplete.copy(),
            context=self.context,
            key_files=self.key_files.copy(),
            decisions=self.decisions.copy(),
            successor=SuccessorInfo(
                agent=successor_agent,
                prompt_hint=prompt_hint,
                priority=priority,
            ),
            metrics=metrics,
            warnings=self.warnings.copy(),
            blockers=self.blockers.copy(),
            artifacts=self.artifacts.copy(),
        )


# CLI interface for testing
if __name__ == "__main__":
    # Create example handoff
    generator = HandoffGenerator("steering-orchestrator")

    generator.add_completed("Researched topic A")
    generator.add_completed("Created initial structure")
    generator.add_incomplete("Topic B research")
    generator.add_incomplete("Integration testing")
    generator.add_key_file("/home/org-jadecli/projects/.claude-org/steering/lib/budget_tracker.py")
    generator.add_decision("Use YAML for handoff format")
    generator.set_context(epic_id="ORG-EPIC-001", task_id="TASK-001")

    metrics = BudgetMetrics(
        turns_used=20,
        max_turns=25,
        tokens_consumed=128000,
        token_budget=160000,
        budget_ratio=0.80,
        duration_seconds=1800.0,
    )

    handoff = generator.generate(
        reason=HandoffReason.BUDGET_WRAP_UP,
        successor_agent="staff-engineer",
        prompt_hint="Continue with Topic B research, then proceed to integration testing",
        metrics=metrics,
    )

    print("=== YAML Format ===")
    print(handoff.to_yaml())
    print("\n=== XML Format ===")
    print(handoff.to_xml())
