"""Chain Detector - Determines if a prompt extends existing work or starts new.

schema: N/A (core library)
depends_on:
  - lib/prompt_adapter.py
  - lib/frontmatter.py
depended_by:
  - agents/vp-product.md
semver: minor
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


class ChainDecision(str, Enum):
    """Decision on how to handle the prompt."""
    NEW_EPIC = "new_epic"           # Start a new org-level epic
    EXTEND_EPIC = "extend_epic"     # Add to existing epic
    NEW_SPRINT = "new_sprint"       # Start a new repo sprint
    EXTEND_SPRINT = "extend_sprint" # Add to existing sprint
    NEW_TASK = "new_task"           # Create standalone task
    SUBTASK = "subtask"             # Add subtask to existing task


@dataclass
class ChainContext:
    """Context about the current work chain."""
    decision: ChainDecision
    active_epic_id: Optional[str]
    active_sprint_id: Optional[str]
    active_task_id: Optional[str]
    related_entities: list[str]
    confidence: float
    reasoning: str


# Keywords that suggest new work vs continuation
NEW_WORK_PATTERNS = [
    r'\b(new|start|begin|create|initiate|fresh|from scratch)\b',
    r'\b(different|separate|another|unrelated)\b',
]

CONTINUE_WORK_PATTERNS = [
    r'\b(continue|extend|add to|also|additionally|furthermore)\b',
    r'\b(related|same|similar|building on|following up)\b',
    r'\b(next|then|after that|now)\b',
]

# Entity ID patterns
ENTITY_ID_PATTERN = r'(EPIC|STORY|TASK|SUBTASK|SPRINT)-\d{3,4}'


def find_active_entities(entities_dir: Path) -> dict[str, list[dict]]:
    """Find all in-progress entities grouped by type."""
    active = {
        'epic': [],
        'story': [],
        'task': [],
        'subtask': [],
        'sprint': [],
    }

    if not entities_dir.exists():
        return active

    for entity_file in entities_dir.rglob('*.md'):
        try:
            content = entity_file.read_text()
            # Extract frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    # Simple YAML parsing for status and id
                    frontmatter = parts[1]
                    status_match = re.search(r'^status:\s*["\']?(\w+)', frontmatter, re.MULTILINE)
                    id_match = re.search(r'^id:\s*["\']?([\w-]+)', frontmatter, re.MULTILINE)
                    type_match = re.search(r'^type:\s*["\']?(\w+)', frontmatter, re.MULTILINE)

                    if status_match and id_match and type_match:
                        status = status_match.group(1)
                        entity_id = id_match.group(1)
                        entity_type = type_match.group(1)

                        if status in ('in_progress', 'pending', 'blocked'):
                            if entity_type in active:
                                active[entity_type].append({
                                    'id': entity_id,
                                    'status': status,
                                    'file': str(entity_file),
                                })
        except Exception:
            pass  # Skip files we can't parse

    return active


def extract_referenced_entities(text: str) -> list[str]:
    """Extract entity IDs referenced in the text."""
    return re.findall(ENTITY_ID_PATTERN, text)


def calculate_recency_score(entities_dir: Path) -> float:
    """Calculate how recently work was done (0-1 scale)."""
    now = datetime.now()
    newest_mtime = None

    if entities_dir.exists():
        for entity_file in entities_dir.rglob('*.md'):
            mtime = datetime.fromtimestamp(entity_file.stat().st_mtime)
            if newest_mtime is None or mtime > newest_mtime:
                newest_mtime = mtime

    if newest_mtime is None:
        return 0.0

    age = now - newest_mtime

    # Within 1 hour = 1.0, within 24 hours = 0.5, older = decreasing
    if age < timedelta(hours=1):
        return 1.0
    elif age < timedelta(hours=24):
        return 0.5
    elif age < timedelta(days=7):
        return 0.3
    else:
        return 0.1


def detect_chain(
    raw_input: str,
    entities_dir: Path,
    recent_context: Optional[str] = None,
) -> ChainContext:
    """
    Detect whether a prompt extends existing work or starts new.

    Args:
        raw_input: The developer's raw input
        entities_dir: Path to entities directory
        recent_context: Recent conversation context if available

    Returns:
        ChainContext with decision and confidence
    """
    text_lower = raw_input.lower()

    # Find active entities
    active = find_active_entities(entities_dir)

    # Check for explicit entity references
    referenced = extract_referenced_entities(raw_input)

    # Check for new work vs continue patterns
    new_score = sum(1 for p in NEW_WORK_PATTERNS if re.search(p, text_lower))
    continue_score = sum(1 for p in CONTINUE_WORK_PATTERNS if re.search(p, text_lower))

    # Calculate recency (work done recently = more likely to continue)
    recency = calculate_recency_score(entities_dir)

    # Determine decision
    decision: ChainDecision
    active_epic_id: Optional[str] = None
    active_sprint_id: Optional[str] = None
    active_task_id: Optional[str] = None
    confidence: float
    reasoning: str

    # If explicit entity reference, that's definitive
    if referenced:
        ref_id = referenced[0]
        if ref_id.startswith('EPIC'):
            decision = ChainDecision.EXTEND_EPIC
            active_epic_id = ref_id
            confidence = 0.95
            reasoning = f"Explicit reference to {ref_id}"
        elif ref_id.startswith('SPRINT'):
            decision = ChainDecision.EXTEND_SPRINT
            active_sprint_id = ref_id
            confidence = 0.95
            reasoning = f"Explicit reference to {ref_id}"
        elif ref_id.startswith('TASK'):
            decision = ChainDecision.SUBTASK
            active_task_id = ref_id
            confidence = 0.95
            reasoning = f"Explicit reference to {ref_id}"
        else:
            decision = ChainDecision.NEW_TASK
            confidence = 0.8
            reasoning = f"Referenced {ref_id}"

    # If strong "new" language
    elif new_score > continue_score + 1:
        decision = ChainDecision.NEW_EPIC
        confidence = 0.7 + (new_score * 0.1)
        reasoning = f"Strong 'new work' language detected (score: {new_score})"

    # If active in-progress work and continue language or recent activity
    elif active['epic'] and (continue_score > 0 or recency > 0.5):
        decision = ChainDecision.EXTEND_EPIC
        active_epic_id = active['epic'][0]['id']
        confidence = 0.6 + recency * 0.3
        reasoning = f"Active epic {active_epic_id} with recent activity"

    elif active['sprint'] and (continue_score > 0 or recency > 0.5):
        decision = ChainDecision.EXTEND_SPRINT
        active_sprint_id = active['sprint'][0]['id']
        confidence = 0.6 + recency * 0.3
        reasoning = f"Active sprint {active_sprint_id} with recent activity"

    elif active['task'] and recency > 0.7:
        decision = ChainDecision.SUBTASK
        active_task_id = active['task'][0]['id']
        confidence = 0.5 + recency * 0.3
        reasoning = f"Very recent work on task {active_task_id}"

    # Default to new task
    else:
        if active['epic']:
            decision = ChainDecision.NEW_TASK
            active_epic_id = active['epic'][0]['id']
            confidence = 0.5
            reasoning = "Creating new task under active epic"
        else:
            decision = ChainDecision.NEW_EPIC
            confidence = 0.4
            reasoning = "No active work found, starting fresh"

    return ChainContext(
        decision=decision,
        active_epic_id=active_epic_id,
        active_sprint_id=active_sprint_id,
        active_task_id=active_task_id,
        related_entities=referenced,
        confidence=min(confidence, 1.0),
        reasoning=reasoning,
    )


def generate_chain_xml(context: ChainContext) -> str:
    """Generate XML representation of chain context."""
    related_xml = '\n    '.join(f'<entity>{e}</entity>' for e in context.related_entities)

    xml = f'''<chain_analysis>
  <decision>{context.decision.value}</decision>
  <confidence>{context.confidence:.2f}</confidence>
  <reasoning>{context.reasoning}</reasoning>

  <active_context>
    <epic_id>{context.active_epic_id or 'none'}</epic_id>
    <sprint_id>{context.active_sprint_id or 'none'}</sprint_id>
    <task_id>{context.active_task_id or 'none'}</task_id>
  </active_context>

  <related_entities>
    {related_xml if related_xml else '<entity>none</entity>'}
  </related_entities>
</chain_analysis>'''

    return xml


# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python chain_detector.py '<raw prompt>'")
        sys.exit(1)

    raw = ' '.join(sys.argv[1:])
    entities_path = Path(__file__).parent.parent / 'entities'

    result = detect_chain(raw, entities_path)

    print(f"Decision: {result.decision.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Active Epic: {result.active_epic_id or 'none'}")
    print(f"Active Sprint: {result.active_sprint_id or 'none'}")
    print(f"Active Task: {result.active_task_id or 'none'}")
    print()
    print("XML Output:")
    print(generate_chain_xml(result))
