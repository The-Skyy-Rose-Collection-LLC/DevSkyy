# DevSkyy Coding Architect Agent

A full-featured coding architect agent built with the **Claude Agent SDK**, specialized in TypeScript and Python development with 17 prompt engineering techniques.

## Features

- **17 Prompt Engineering Techniques** - Chain-of-Thought, Tree of Thoughts, ReAct, Few-Shot, Constitutional AI, and more
- **Dual Language Support** - Both TypeScript and Python implementations
- **MCP Tools** - Custom TypeScript and Python analysis tools
- **Cost Tracking** - Real-time cost and duration tracking
- **Streaming Support** - Real-time message callbacks

## Quick Start

### TypeScript

```bash
# Install dependencies
npm install

# Run with a prompt
npm start "Review the code in src/index.ts"

# Or build and run
npm run build
node dist/index.js "Design a REST API architecture"
```

### Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run with a prompt
python python/main.py "Analyze this Python codebase"
```

## Environment Variables

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### TypeScript API

```typescript
import { createCodingArchitectAgent } from './index.js';

const agent = createCodingArchitectAgent({
  verbose: true,
  workingDirectory: process.cwd(),
});

// Generic query
const result = await agent.query("Review this code for best practices");

// Specialized methods
await agent.reviewCode("src/index.ts");        // Chain-of-Thought
await agent.designArchitecture("REST API");    // Tree of Thoughts
await agent.debugIssue("TypeError in line 42"); // ReAct pattern
await agent.refactorCode("src/utils.ts");      // Constitutional AI
await agent.analyzeTypeScript("./src");        // TypeScript analysis
await agent.analyzePython("./python");         // Python analysis
```

### Python API

```python
from main import CodingArchitectAgent

agent = CodingArchitectAgent(verbose=True)

# Generic query
result = await agent.query("Review this code")

# Specialized methods
await agent.review_code("main.py")
await agent.design_architecture("microservices")
await agent.debug_issue("Connection error", context="database.py")
await agent.refactor_code("utils.py", goals="improve readability")
```

## 17 Prompt Engineering Techniques

| Technique | Use Case | Reference |
|-----------|----------|-----------|
| Chain-of-Thought | Step-by-step reasoning | Wei et al., 2022 |
| Few-Shot Learning | Example-based guidance | Brown et al., 2020 |
| Self-Consistency | Multiple reasoning paths | Wang et al., 2022 |
| Tree of Thoughts | Branching exploration | Yao et al., 2023 |
| ReAct | Reasoning + Acting | Yao et al., 2022 |
| RAG | Retrieval-Augmented | Lewis et al., 2020 |
| Prompt Chaining | Multi-step workflows | - |
| Generated Knowledge | Self-generated context | - |
| Negative Prompting | Constraint specification | - |
| Constitutional AI | Self-critique & revision | Bai et al., 2022 |
| COSTARD | Context-sensitive | - |
| Meta-Prompting | Prompt optimization | - |
| Recursive Prompting | Iterative refinement | - |
| Structured Output | Format-specific output | - |
| Temperature Scheduling | Dynamic temperature | - |
| Ensemble Prompting | Multi-technique combination | - |
| Role-Based Constraint | Persona establishment | - |

## Project Structure

```
dev/
├── src/                          # TypeScript implementation
│   ├── index.ts                  # Main agent
│   ├── prompts/system-prompt.ts  # System prompts & techniques
│   ├── tools/
│   │   ├── typescript-tools.ts   # TS analysis MCP tools
│   │   └── python-tools.ts       # Python analysis MCP tools
│   └── types/index.ts            # Type definitions
│
├── python/                       # Python implementation
│   ├── main.py                   # Main agent
│   ├── prompts/system_prompt.py  # System prompts
│   └── tools/
│       ├── typescript_tools.py
│       └── python_tools.py
│
├── package.json
├── tsconfig.json
└── requirements.txt
```

## MCP Tools

### TypeScript Tools
- `ts_type_check` - Run TypeScript type checking
- `ts_analyze_config` - Analyze tsconfig.json
- `ts_dependency_audit` - Audit npm dependencies
- `ts_analyze_complexity` - Analyze code complexity
- `ts_lint_check` - Run ESLint
- `ts_generate_types` - Generate type definitions

### Python Tools
- `py_type_check` - Run mypy/pyright
- `py_lint` - Run ruff/flake8
- `py_format` - Run black/isort
- `py_dependency_audit` - Audit pip dependencies
- `py_venv_info` - Get virtual environment info
- `py_analyze_complexity` - Analyze code complexity
- `py_test_runner` - Run pytest
- `py_generate_stubs` - Generate type stubs

## License

MIT

## Related

- [DevSkyy Platform](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy) - Full platform with 6 SuperAgents
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) - Anthropic's agent framework
