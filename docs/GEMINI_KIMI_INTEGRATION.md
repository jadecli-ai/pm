# Gemini & Kimi Agent Integration

> Integration of Google Gemini and Moonshot Kimi AI agents with Claude Code multi-agent system

## Overview

This integration provides **12 specialized AI agents** (6 Gemini + 6 Kimi) that Claude Code agents can delegate work to:

### Gemini Agents (6)
1. **gemini-multimodal** - Image/video/document analysis
2. **gemini-code-interpreter** - Python code execution in sandbox
3. **gemini-function-composer** - Parallel function calling orchestration
4. **gemini-cached-researcher** - Context caching for performance
5. **gemini-structured-json** - JSON schema extraction
6. **gemini-embeddings** - Semantic search and embeddings

### Kimi Agents (6)
1. **kimi-long-context** - 256K token window analysis
2. **kimi-thinking-mode** - Extended reasoning (temp=1.0)
3. **kimi-instant-mode** - Fast responses (temp=0.6)
4. **kimi-swarm-coordinator** - Multi-agent parallel execution
5. **kimi-vibe-coder** - Screenshot → Code generation
6. **kimi-terminal-expert** - Shell command expertise

---

## Setup

### 1. Install Dependencies

```bash
cd /home/org-jadecli/projects/pm
pip install -r requirements.txt
```

### 2. Set API Keys

Create `.env` file in project root:

```bash
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Kimi API Key
KIMI_API_KEY_v3=sk-kimi-your_key_here
```

Or export as environment variables:

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export KIMI_API_KEY_v3="sk-kimi-your_key"
```

### 3. Verify Installation

```bash
python experiments/test_setup.py
```

---

## Usage

### Using Agents in Claude Code

Agents are defined in `agents/gemini/` and `agents/kimi/`. Claude Code automatically discovers them.

#### Example: Analyze an Image

```bash
# In Claude Code session
> Use the gemini-multimodal agent to analyze screenshot.png

# Claude will:
# 1. Spawn gemini-multimodal agent
# 2. Agent calls gemini_analyze_image tool
# 3. Returns analysis
```

#### Example: Load Entire Codebase

```bash
> Use kimi-long-context to analyze all Python files in src/

# Kimi loads ~200K lines into single 256K context
# Performs global analysis without chunking
```

### Direct Tool Usage (Python)

```python
from lib.agent_registry import get_registry
from lib.mlflow_tracing import trace_agent_call

# Get registry
registry = get_registry()

# Execute tool with MLflow tracing
with trace_agent_call("gemini-multimodal", "analyze_image", image="test.png"):
    result = registry.execute_tool(
        "gemini_analyze_image",
        image_path="test.png",
        query="Describe this UI"
    )

    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")
    print(f"Tokens: {result['tokens']}")
```

---

## Agent Capabilities

### Gemini Strengths
- ✅ **Multimodal**: Native image/video/audio understanding
- ✅ **Code Execution**: Sandboxed Python with matplotlib
- ✅ **Function Calling**: Parallel and compositional
- ✅ **Structured Output**: JSON schema validation
- ✅ **Embeddings**: High-quality semantic search
- ✅ **Context Caching**: Cost optimization

### Kimi Strengths
- ✅ **256K Context**: Largest window available (28% > Claude)
- ✅ **Cost**: ~9x cheaper than Claude
- ✅ **Agent Swarm**: Unique multi-agent coordination
- ✅ **Vibe Coding**: Screenshot → Production UI code
- ✅ **LiveCodeBench**: 83.1% (vs Claude 64.0%)
- ✅ **Thinking Mode**: Extended reasoning like OpenAI o1

---

## Performance Tracking

### MLflow Integration

All agent calls are automatically traced with MLflow:

```python
from lib.mlflow_tracing import trace_agent_call, log_comparison

# Trace single agent
with trace_agent_call("gemini-multimodal", "analyze_image"):
    result = gemini.analyze_image("test.png", "Describe")
    mlflow.log_metrics({
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms
    })

# Compare Gemini vs Kimi
gemini_result = gemini.analyze(...)
kimi_result = kimi.analyze(...)

log_comparison(gemini_result, kimi_result, "codebase_analysis")
```

### View MLflow UI

```bash
mlflow ui
# Open http://localhost:5000
```

Experiments are organized as:
- `agents/gemini-multimodal`
- `agents/kimi-long-context`
- `agent_comparison` (Gemini vs Kimi comparisons)

---

## Testing

### Run All Tests

```bash
# Test Gemini agents
python experiments/gemini_variations/test_multimodal.py
python experiments/gemini_variations/test_code_exec.py

# Test Kimi agents
python experiments/kimi_variations/test_long_context.py

# Compare performance
python scripts/compare_performance.py
```

### Test Individual Agents

```python
# Test Gemini multimodal
from lib.gemini.multimodal import GeminiMultimodal

tool = GeminiMultimodal()
result = tool.analyze_image("screenshot.png", "Describe this UI")
print(result.output)
```

---

## Coordination Patterns

Three patterns for agent coordination:

### 1. File-Based (Async, Simple)
```python
# Claude writes task
Path("tasks/task-001.json").write_text(json.dumps({
    "type": "analyze",
    "files": ["src/**/*.py"]
}))

# Gemini/Kimi reads, processes, writes result
# Claude reads result
```

### 2. Redis (Real-time, Stateful)
```python
import redis
r = redis.Redis()

# Claude publishes
r.hset("tasks", "task-001", json.dumps(task))

# Agents subscribe, process
# Claude aggregates from Redis
```

### 3. Stdio (Fast, Synchronous)
```python
# Claude pipes to Gemini CLI
result = subprocess.run(
    ["python", "lib/gemini_cli.py"],
    input=json.dumps(task),
    capture_output=True
)
```

---

## Architecture

```
Claude Code Agent (team-lead.md)
    │
    ├─ Gemini Agents
    │   ├─ gemini-multimodal.md → lib/gemini/multimodal.py
    │   ├─ gemini-code-interpreter.md → lib/gemini/code_execution.py
    │   ├─ gemini-function-composer.md → lib/gemini/function_calling.py
    │   ├─ gemini-cached-researcher.md → lib/gemini/caching.py
    │   ├─ gemini-structured-json.md → lib/gemini/structured_output.py
    │   └─ gemini-embeddings.md → lib/gemini/embeddings.py
    │
    └─ Kimi Agents
        ├─ kimi-long-context.md → lib/kimi/long_context.py
        ├─ kimi-thinking-mode.md → lib/kimi/thinking_mode.py
        ├─ kimi-instant-mode.md → lib/kimi/instant_mode.py
        ├─ kimi-swarm-coordinator.md → lib/kimi/swarm.py
        ├─ kimi-vibe-coder.md → lib/kimi/vibe_coding.py
        └─ kimi-terminal-expert.md → lib/kimi/terminal.py

lib/agent_registry.py - Tool registration
lib/mlflow_tracing.py - Performance tracking
```

---

## Expanding Agents

### Add New Gemini Tool

1. Create module in `lib/gemini/my_tool.py`:
```python
from dataclasses import dataclass

@dataclass
class ToolResult:
    success: bool
    output: str
    tokens_used: int
    model: str
    latency_ms: float

class MyGeminiTool:
    def my_function(self, param: str) -> ToolResult:
        # Implementation
        pass

MY_TOOLS = [{
    "name": "gemini_my_function",
    "description": "Does X. ~Y tokens.",
    "input_schema": {...}
}]

def gemini_my_function(param: str) -> dict:
    tool = MyGeminiTool()
    result = tool.my_function(param)
    return {"success": result.success, ...}
```

2. Register in `lib/gemini/__init__.py`
3. Create agent definition in `agents/gemini/my-agent.md`

### Add New Kimi Tool

Same pattern in `lib/kimi/` and `agents/kimi/`

---

## Troubleshooting

### API Key Issues
```bash
# Verify keys are set
echo $GEMINI_API_KEY
echo $KIMI_API_KEY_v3

# Test Gemini connection
python -c "from google import genai; client = genai.Client(api_key='YOUR_KEY'); print('OK')"
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### MLflow Not Working
```bash
# MLflow is optional - agents work without it
# To fix: pip install mlflow
```

---

## Performance Benchmarks

### Gemini
- **Multimodal**: Strong vision capabilities
- **Code Execution**: Fast, accurate
- **Function Calling**: Automatic schema generation

### Kimi
- **LiveCodeBench**: 83.1% (vs Claude 64.0% - **major advantage**)
- **AIME 2025**: 96.1% (math reasoning)
- **Context**: 256K tokens (28% > Claude)
- **Cost**: ~9x cheaper than Claude

---

## Next Steps

1. **Test agents** with your specific use cases
2. **Compare performance** via MLflow
3. **Expand implementations** for stub tools
4. **Create more agent variations** (see agents/*.md for templates)
5. **Integrate with CI/CD** for automated testing

---

## Resources

- [Gemini API Docs](https://googleapis.github.io/python-genai/)
- [Kimi CLI Docs](https://moonshotai.github.io/kimi-cli/en/)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
