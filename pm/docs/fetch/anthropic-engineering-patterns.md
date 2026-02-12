# Anthropic Engineering Patterns

> Sources: anthropic.com/engineering, O'Reilly Radar, GitHub

## Organization Structure

Per [Anthropic Engineering](https://www.anthropic.com/engineering):
- **DRI Model**: Directly Responsible Individual for each project
- **10+ people threshold**: Delegate project management, not just execution
- **Complex interdependencies**: Organize with explicit dependency tracking

## Multi-Project Patterns

From [Nick Tune's Architecture Reverse Engineering](https://www.oreilly.com/radar/reverse-engineering-your-software-architecture-with-claude-code-to-help-claude-code/):

### Documentation Strategy
- Lightweight requirements files containing:
  - System overview and repository relationships
  - Domain concept explanations
  - Specific guidance on where to find information

### Visualization Approach
- Horizontal flow diagrams using Mermaid swimlanes
- Each repository becomes a container
- Flow steps categorized by type:
  - HTTP endpoints
  - Aggregate method calls
  - Database operations
  - Event publications
  - Workflow triggers

### Key Insight
> "The more [Claude] understands about the functionality of the system (the domain, the use cases, the end-to-end flows), the more it can help."

## Code Reuse Patterns

### Single Source of Truth
- Each concept defined once, imported everywhere
- Shared `lib/` directory for common code
- Explicit frontmatter dependencies

### Architecture-First Development
1. Map architecture before coding
2. Document flows and dependencies
3. Use AI to maintain architecture docs
4. Test AI understanding with support tickets

## Repository Organization

Anthropic maintains 67+ public repositories on GitHub.

### Recommended Structure
```
org/
├── shared-lib/          # Common utilities
├── project-a/
│   └── uses shared-lib
├── project-b/
│   └── uses shared-lib
└── docs/                # Organization-wide docs
```

## Automation Recommendations

### EventCatalog-style Approach
> "Platform engineering should shift toward exposing system dependencies transparently rather than requiring AI agents to reverse engineer them."

### Auto-Generated Docs
- Architecture diagrams on every PR
- Dependency graphs from code analysis
- Flow documentation from runtime traces

## Accuracy Considerations

Nick Tune acknowledges:
> "Significant inaccuracies required correction"

**Mitigation:**
- Review AI-generated architecture
- Validate against actual runtime behavior
- Update requirements docs based on learnings
