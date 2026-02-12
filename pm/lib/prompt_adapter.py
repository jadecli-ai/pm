"""Prompt Adapter - Converts unstructured developer input to structured XML prompts.

schema: N/A (core library)
depends_on:
  - lib/frontmatter.py
depended_by:
  - agents/vp-product.md
  - .claude/commands/ask.md
semver: minor
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConventionalCommitType(str, Enum):
    """Conventional commit types aligned with semantic versioning."""
    FEAT = "feat"           # New feature → MINOR bump
    FIX = "fix"             # Bug fix → PATCH bump
    DOCS = "docs"           # Documentation only
    STYLE = "style"         # Formatting, no logic change
    REFACTOR = "refactor"   # Code restructure, no behavior change
    PERF = "perf"           # Performance improvement
    TEST = "test"           # Adding/fixing tests
    BUILD = "build"         # Build system, dependencies
    CI = "ci"               # CI/CD changes
    CHORE = "chore"         # Maintenance tasks
    REVERT = "revert"       # Revert previous commit
    REVIEW = "review"       # Code review (custom)
    SPIKE = "spike"         # Research/exploration (custom)


class PromptIntent(str, Enum):
    """High-level intent categories for routing."""
    IMPLEMENT = "implement"   # Write new code
    FIX = "fix"               # Fix existing code
    REVIEW = "review"         # Analyze/review code
    REFACTOR = "refactor"     # Restructure code
    RESEARCH = "research"     # Explore/investigate
    PLAN = "plan"             # Strategic planning
    TEST = "test"             # Add/fix tests
    DOCUMENT = "document"     # Documentation


@dataclass
class StructuredPrompt:
    """Structured prompt output from the adapter."""
    raw_input: str
    intent: PromptIntent
    commit_type: ConventionalCommitType
    repos: list[str]
    scope: Optional[str]
    title: str
    description: str
    acceptance_criteria: list[str]
    is_chain_extension: bool
    chain_context: Optional[str]
    xml_output: str


# Intent detection patterns (order matters - first match wins)
INTENT_PATTERNS = [
    # Fix patterns
    (r'\b(fix|bug|error|broken|crash|fail|issue|wrong|incorrect)\b', PromptIntent.FIX, ConventionalCommitType.FIX),
    # Review patterns
    (r'\b(review|check|analyze|audit|assess|evaluate|look at|examine)\b', PromptIntent.REVIEW, ConventionalCommitType.REVIEW),
    # Test patterns
    (r'\b(test|spec|coverage|unit test|integration test|e2e)\b', PromptIntent.TEST, ConventionalCommitType.TEST),
    # Refactor patterns
    (r'\b(refactor|restructure|reorganize|clean up|improve|optimize)\b', PromptIntent.REFACTOR, ConventionalCommitType.REFACTOR),
    # Research patterns
    (r'\b(research|explore|investigate|spike|prototype|poc|proof of concept)\b', PromptIntent.RESEARCH, ConventionalCommitType.SPIKE),
    # Plan patterns
    (r'\b(plan|design|architect|roadmap|strategy|prioritize)\b', PromptIntent.PLAN, ConventionalCommitType.DOCS),
    # Document patterns
    (r'\b(document|docs|readme|guide|tutorial|explain)\b', PromptIntent.DOCUMENT, ConventionalCommitType.DOCS),
    # Default: implement (new feature)
    (r'\b(add|create|implement|build|make|new|feature|enable)\b', PromptIntent.IMPLEMENT, ConventionalCommitType.FEAT),
]

# Repo detection patterns for jadecli-ai org
REPO_PATTERNS = {
    'team-agents-sdk': [
        r'\b(sdk|agent sdk|team agent|neon|mlflow|tracing|hooks?|crud|models?)\b',
        r'\b(dashboard|vercel|next\.?js|drizzle)\b',
    ],
    'pm': [
        r'\b(pm|product management|epic|story|task|sprint|iteration)\b',
        r'\b(vp product|sdm|staff engineer|sprint master)\b',
    ],
}

# Scope detection patterns
SCOPE_PATTERNS = {
    'frontend': r'\b(ui|frontend|component|page|layout|css|style|react|next)\b',
    'backend': r'\b(api|backend|server|endpoint|route|handler|service)\b',
    'db': r'\b(database|db|table|schema|migration|query|neon|postgres)\b',
    'hooks': r'\b(hook|event|callback|trigger|activity)\b',
    'models': r'\b(model|pydantic|validator|enum|type)\b',
    'infra': r'\b(infra|ci|cd|deploy|docker|k8s|pipeline)\b',
    'agents': r'\b(agent|subagent|teammate|team|spawn)\b',
    'entities': r'\b(entity|epic|story|task|subtask|frontmatter)\b',
}


def detect_intent(text: str) -> tuple[PromptIntent, ConventionalCommitType]:
    """Detect intent and commit type from raw input."""
    text_lower = text.lower()

    for pattern, intent, commit_type in INTENT_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return intent, commit_type

    # Default to implement/feat
    return PromptIntent.IMPLEMENT, ConventionalCommitType.FEAT


def detect_repos(text: str) -> list[str]:
    """Detect which repos are involved from raw input."""
    text_lower = text.lower()
    repos = []

    for repo, patterns in REPO_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if repo not in repos:
                    repos.append(repo)
                break

    # Default to pm if no repo detected and we're in pm context
    if not repos:
        repos = ['pm']

    return repos


def detect_scope(text: str) -> Optional[str]:
    """Detect conventional commit scope from raw input."""
    text_lower = text.lower()

    for scope, pattern in SCOPE_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            return scope

    return None


def extract_title(text: str) -> str:
    """Extract a concise title from raw input."""
    # Take first sentence or first 80 chars
    sentences = re.split(r'[.!?]', text)
    title = sentences[0].strip() if sentences else text[:80]

    # Capitalize and clean
    title = title.strip().capitalize()
    if len(title) > 70:
        title = title[:67] + '...'

    return title


def extract_acceptance_criteria(text: str) -> list[str]:
    """Extract acceptance criteria from raw input."""
    criteria = []

    # Look for explicit criteria markers
    ac_patterns = [
        r'(?:acceptance criteria|ac|requirements?|must|should|needs? to)[:\s]+(.+)',
        r'[-*]\s*(.+)',  # Bullet points
        r'\d+\.\s*(.+)',  # Numbered items
    ]

    for pattern in ac_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        criteria.extend(m.strip() for m in matches if len(m.strip()) > 10)

    # Remove duplicates while preserving order
    seen = set()
    unique_criteria = []
    for c in criteria:
        if c not in seen:
            seen.add(c)
            unique_criteria.append(c)

    return unique_criteria[:5]  # Max 5 criteria


def generate_xml_prompt(prompt: StructuredPrompt) -> str:
    """Generate structured XML prompt from StructuredPrompt."""
    repos_xml = '\n    '.join(f'<repo>{r}</repo>' for r in prompt.repos)
    criteria_xml = '\n    '.join(f'<criterion>{c}</criterion>' for c in prompt.acceptance_criteria)

    chain_context_xml = ''
    if prompt.is_chain_extension and prompt.chain_context:
        chain_context_xml = f'''
  <chain_context>
    <extends>true</extends>
    <previous>{prompt.chain_context}</previous>
  </chain_context>'''

    xml = f'''<request>
  <metadata>
    <intent>{prompt.intent.value}</intent>
    <commit_type>{prompt.commit_type.value}</commit_type>
    <scope>{prompt.scope or 'general'}</scope>
    <repos>
    {repos_xml}
    </repos>
  </metadata>

  <content>
    <title>{prompt.title}</title>
    <description>{prompt.description}</description>
  </content>

  <acceptance_criteria>
    {criteria_xml if criteria_xml else '<criterion>Complete the requested work</criterion>'}
  </acceptance_criteria>{chain_context_xml}
</request>'''

    return xml


def adapt_prompt(
    raw_input: str,
    chain_context: Optional[str] = None,
    force_intent: Optional[PromptIntent] = None,
    force_commit_type: Optional[ConventionalCommitType] = None,
) -> StructuredPrompt:
    """
    Convert unstructured developer input to a structured XML prompt.

    Args:
        raw_input: Unstructured text from developer
        chain_context: Previous context if extending a chain
        force_intent: Override detected intent
        force_commit_type: Override detected commit type

    Returns:
        StructuredPrompt with all fields populated
    """
    # Detect intent and commit type
    intent, commit_type = detect_intent(raw_input)
    if force_intent:
        intent = force_intent
    if force_commit_type:
        commit_type = force_commit_type

    # Detect repos and scope
    repos = detect_repos(raw_input)
    scope = detect_scope(raw_input)

    # Extract title and criteria
    title = extract_title(raw_input)
    criteria = extract_acceptance_criteria(raw_input)

    # Determine if chain extension
    is_chain_extension = bool(chain_context)

    # Create structured prompt
    prompt = StructuredPrompt(
        raw_input=raw_input,
        intent=intent,
        commit_type=commit_type,
        repos=repos,
        scope=scope,
        title=title,
        description=raw_input,
        acceptance_criteria=criteria,
        is_chain_extension=is_chain_extension,
        chain_context=chain_context,
        xml_output='',  # Will be set below
    )

    # Generate XML output
    prompt.xml_output = generate_xml_prompt(prompt)

    return prompt


# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt_adapter.py '<raw prompt>'")
        sys.exit(1)

    raw = ' '.join(sys.argv[1:])
    result = adapt_prompt(raw)

    print(f"Intent: {result.intent.value}")
    print(f"Commit Type: {result.commit_type.value}")
    print(f"Repos: {', '.join(result.repos)}")
    print(f"Scope: {result.scope or 'general'}")
    print(f"Title: {result.title}")
    print(f"Chain Extension: {result.is_chain_extension}")
    print()
    print("XML Output:")
    print(result.xml_output)
