# Folder Reorganization Design

## Goal
Apply a minimal-churn cleanup to `agent_from_scratch` so the project structure is clearer and more standard, while keeping the current learning-oriented layout easy to understand.

## Target Structure

```text
agent_from_scratch/
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   ├── main.py
│   ├── server.py
│   ├── agent.py
│   ├── llm_wrapper.py
│   └── agent_tools/
│       ├── __init__.py
│       └── calculator.py
├── frontend/
├── tests/
│   ├── run_tests.py
│   └── test_calculator.py
├── README.md
└── AGENTS.md
```

## Changes

### Rename `unittest/` to `tests/`
This follows standard Python naming conventions and makes the purpose of the directory immediately obvious.

### Rename `backend/tools/` to `backend/agent_tools/`
This makes it clear these files are agent-callable tools, not generic utilities.

### Add `backend/agent_tools/__init__.py`
This file becomes the central tool registry. It should hold general tool metadata such as tool name, description, function reference, and parameter schema.

## File Responsibilities

### `backend/main.py`
CLI or local runner entry point.

### `backend/server.py`
HTTP server entry point.

### `backend/agent.py`
Agent orchestration logic, including calling the tool registry.

### `backend/llm_wrapper.py`
Wrapper for model calls.

### `backend/agent_tools/calculator.py`
Contains only calculator logic and tool implementation.

### `backend/agent_tools/__init__.py`
Contains the `Tool` class and the list or registry of available tools.

## Recommended Metadata Pattern
Use a registry-based pattern so metadata is attached at the tool-definition level rather than inside each tool implementation.

Example structure:

```python
from typing import Callable, Any

class Tool:
    def __init__(self, name: str, func: Callable, description: str, parameters: dict[str, Any]):
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters
```

This keeps each tool implementation focused on behavior, while general metadata lives in one place.

## Why This Design
- Minimal churn: only two folder renames and one new file.
- Better naming: `tests` and `agent_tools` are clearer than `unittest` and `tools`.
- Better separation: implementation stays in tool files, while metadata is centralized.
- Beginner-friendly: the layout remains easy to navigate without introducing a heavy package structure.

## Out of Scope
- Renaming `backend/` or `frontend/`
- Moving to a `src/` layout
- Splitting backend into many subpackages
- Refactoring unrelated logic

## Success Criteria
- The project structure is clearer without major import churn.
- Tool metadata is centralized in one place.
- Tests still work after updating import paths.
