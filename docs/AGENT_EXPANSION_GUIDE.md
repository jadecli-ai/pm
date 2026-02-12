## Agent Expansion Guide

This guide shows how to expand stub implementations and create new agent variations.

---

## Expanding Stub Implementations

### Pattern to Follow

All implementations follow this pattern (see `lib/gemini/multimodal.py` as reference):

```python
# 1. Imports
import os
import time
from dataclasses import dataclass
from typing import Optional

try:
    from google import genai  # or kimi SDK
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# 2. ToolResult dataclass
@dataclass
class ToolResult:
    success: bool
    output: str
    tokens_used: int
    model: str
    latency_ms: float
    error: Optional[str] = None

# 3. Tool class
class MyTool:
    def __init__(self):
        # Initialize SDK
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY not set")

        self.client = initialize_client(api_key)
        self.model_name = "model-name"

    def my_function(self, param: str) -> ToolResult:
        """Do something."""
        start = time.time()

        try:
            # Call API
            response = self.client.do_something(param)

            latency = (time.time() - start) * 1000
            tokens = estimate_tokens(response)

            return ToolResult(
                success=True,
                output=response.text,
                tokens_used=tokens,
                model=self.model_name,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                tokens_used=0,
                model=self.model_name,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )

# 4. Tool definitions (for agent registry)
MY_TOOLS = [
    {
        "name": "my_function",
        "description": "Does X. ~Y tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            },
            "required": ["param"]
        }
    }
]

# 5. Executor function (for agent registry)
def my_function(param: str) -> dict:
    """Execute my_function tool."""
    tool = MyTool()
    result = tool.my_function(param)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }
```

---

## Priority Expansions (Recommended Order)

### High Priority (Most Useful)

1. **Gemini Embeddings** (`lib/gemini/embeddings.py`)
   - API: `client.models.embed_content()`
   - Use case: Semantic search, code search
   - Complexity: Medium

2. **Gemini Structured JSON** (`lib/gemini/structured_output.py`)
   - API: `response_mime_type: 'application/json'`
   - Use case: Data extraction, API responses
   - Complexity: Low

3. **Kimi Thinking Mode** (`lib/kimi/thinking_mode.py`)
   - API: Kimi API with `temperature: 1.0`
   - Use case: Complex problem solving
   - Complexity: Medium

### Medium Priority

4. **Gemini Function Calling** (`lib/gemini/function_calling.py`)
   - API: `tools` parameter with function declarations
   - Use case: Multi-step workflows
   - Complexity: High

5. **Kimi Swarm** (`lib/kimi/swarm.py`)
   - API: Kimi agent swarm coordination
   - Use case: Parallel task execution
   - Complexity: High

### Lower Priority (Advanced)

6. **Gemini Caching** (`lib/gemini/caching.py`)
   - API: Explicit cache creation with TTL
   - Use case: Cost optimization
   - Complexity: Medium

7. **Kimi Vibe Coding** (`lib/kimi/vibe_coding.py`)
   - API: Kimi multimodal with screenshot input
   - Use case: UI to code generation
   - Complexity: High

---

## Creating New Agent Variations

### 1. Gemini Variations

Based on `gemini-api-dev` skill capabilities, you can create:

- **gemini-researcher** - Web search + summarization
- **gemini-translator** - Multi-language translation
- **gemini-code-reviewer** - Code quality analysis
- **gemini-test-generator** - Generate test cases
- **gemini-doc-writer** - Generate documentation

### 2. Kimi Variations

Based on Kimi CLI features, you can create:

- **kimi-refactorer** - Large-scale code refactoring (256K context)
- **kimi-debugger** - Trace bugs across files
- **kimi-architect** - System architecture analysis
- **kimi-optimizer** - Performance optimization suggestions

### 3. Hybrid Agents (Claude + Gemini + Kimi)

- **hybrid-analyzer** - Claude orchestrates, Gemini handles multimodal, Kimi handles long context
- **hybrid-generator** - Claude plans, Gemini executes code, Kimi validates

---

## Agent Definition Template

Create new agent in `agents/gemini/` or `agents/kimi/`:

```markdown
---
name: my-new-agent
description: Brief description of what this agent does
model: sonnet  # Claude orchestrates
tools:
  - Read
  - Write
  - my_custom_tool_1
  - my_custom_tool_2
memory: project  # Optional: persistent memory
---

# My New Agent

You are a specialized agent that does X.

## Capabilities

- Capability 1
- Capability 2
- Capability 3

## Usage Pattern

When the team lead requests X:

1. Do step 1
2. Do step 2
3. Return results

## Best Practices

- Tip 1
- Tip 2

## Example Tasks

- "Task example 1"
- "Task example 2"
```

---

## Testing New Agents

### 1. Create Test Script

```python
#!/usr/bin/env python3
"""Test my new agent."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.my_module.my_tool import MyTool
from lib.mlflow_tracing import trace_agent_call

def main():
    print("Testing My New Agent")

    tool = MyTool()

    with trace_agent_call("my-agent", "my_function"):
        result = tool.my_function("test")

        assert result.success, f"Failed: {result.error}"
        print(f"✓ Test passed")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Latency: {result.latency_ms:.0f}ms")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

### 2. Register in Agent Registry

Edit `lib/agent_registry.py`:

```python
from .my_module import MY_TOOLS
from .my_module.my_tool import my_function

class AgentRegistry:
    def _register_my_tools(self):
        self.tools.extend(MY_TOOLS)
        self.executors["my_function"] = my_function
```

### 3. Run Tests

```bash
PYTHONPATH=. python3 experiments/my_variations/test_my_agent.py
```

---

## Performance Benchmarking

Use MLflow to compare variations:

```python
from lib.mlflow_tracing import log_comparison

# Test variation 1
result1 = agent1.do_task()

# Test variation 2
result2 = agent2.do_task()

# Compare
log_comparison(result1, result2, "task_name")
```

View results:
```bash
mlflow ui
# Open http://localhost:5000
```

---

## Tips for Expansion

1. **Start Small**: Implement one function at a time
2. **Test Early**: Write tests before full implementation
3. **Follow Patterns**: Use existing implementations as templates
4. **Document**: Add docstrings and usage examples
5. **Trace Everything**: Use MLflow for all agent calls
6. **Handle Errors**: Always return ToolResult with error field
7. **Estimate Tokens**: Approximate token usage for cost tracking

---

## Common Pitfalls

### ❌ Don't

- Don't skip error handling
- Don't forget to trace with MLflow
- Don't hardcode API keys (use environment variables)
- Don't return None (return ToolResult with error)
- Don't forget to register tools in agent_registry.py

### ✅ Do

- Do follow the ToolResult pattern
- Do add comprehensive tests
- Do document usage examples
- Do estimate token costs
- Do add to agent registry

---

## Getting Help

- Review existing implementations: `lib/gemini/multimodal.py`, `lib/kimi/long_context.py`
- Check API docs: Gemini (googleapis.github.io/python-genai/), Kimi (moonshotai.github.io/kimi-cli/)
- Run setup test: `python3 experiments/test_setup.py`
- View integration guide: `docs/GEMINI_KIMI_INTEGRATION.md`

---

## Next Steps

1. Choose a stub to expand (start with embeddings or structured JSON)
2. Read the API documentation
3. Implement following the pattern above
4. Write tests
5. Register in agent_registry.py
6. Run tests and benchmark with MLflow
7. Create agent definition (.md file)
8. Document usage examples
