# Simple Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the simplest AI agent from scratch: one `Agent` class that lets the LLM reason about which tool to use, observes the tool results, and keeps conversation history in SQLite `:memory:`.

**Architecture:** Single `Agent` class in `backend/agent.py` handles system prompt, LLM calls, tool selection, tool execution, and SQLite conversation memory. Tools live in `backend/agent_tools/` with simple metadata.

**Tech Stack:** Python 3.13, SQLite `:memory:`, existing `LLMWrapper`, unittest

---

## File Structure

**New files:**
- `agent_from_scratch/backend/agent_tools/__init__.py` — Tool class + registry with metadata
- `agent_from_scratch/tests/test_agent.py` — Agent tests

**Modified files:**
- `agent_from_scratch/backend/agent.py` — Full Agent implementation
- `agent_from_scratch/backend/main.py` — Use Agent class

**Renamed directories:**
- `unittest/` → `tests/`
- `backend/tools/` → `backend/agent_tools/`

---

## Task 1: Rename Folders

**Files:**
- Rename: `agent_from_scratch/unittest/` → `agent_from_scratch/tests/`
- Rename: `agent_from_scratch/backend/tools/` → `agent_from_scratch/backend/agent_tools/`

- [ ] **Step 1: Rename unittest to tests**

```bash
cd agent_from_scratch
git mv unittest tests
```

- [ ] **Step 2: Rename tools to agent_tools**

```bash
git mv backend/tools backend/agent_tools
```

- [ ] **Step 3: Update imports in test_calculator.py**

File: `agent_from_scratch/tests/test_calculator.py`

Change line 3 from:
```python
from calculator import calculator
```
To:
```python
from agent_tools.calculator import calculator
```

- [ ] **Step 4: Update test runner path**

File: `agent_from_scratch/tests/run_tests.py`

Change line 37 from:
```python
suite = loader.discover("unittest")
```
To:
```python
suite = loader.discover("tests")
```

- [ ] **Step 5: Run tests to verify**

```bash
cd agent_from_scratch
python tests/run_tests.py
```
Expected: All calculator tests pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: rename unittest to tests and tools to agent_tools"
```

---

## Task 2: Create Simple Tool Registry

**Files:**
- Create: `agent_from_scratch/backend/agent_tools/__init__.py`

- [ ] **Step 1: Create tool registry with metadata**

File: `agent_from_scratch/backend/agent_tools/__init__.py`

```python
from typing import Callable, Any
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    func: Callable
    description: str
    parameters: dict[str, Any]


from .calculator import calculator

# Tool registry — metadata lives here, not inside each tool
TOOLS = [
    Tool(
        name="calculator",
        func=calculator,
        description="Evaluates mathematical expressions like '2+2' or '(15*3)/5'",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A math expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    )
]


def get_tool_definitions() -> list[dict]:
    """Convert Tool objects to LLM tool definitions."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters_json_schema": tool.parameters
        }
        for tool in TOOLS
    ]


def execute_tool(name: str, args: dict) -> dict:
    """Execute a tool by name with given args."""
    tool = next((t for t in TOOLS if t.name == name), None)
    if not tool:
        raise ValueError(f"Tool '{name}' not found")

    try:
        result = tool.func(**args)
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}
```

- [ ] **Step 2: Run a quick test**

```bash
cd agent_from_scratch/backend
python -c "from agent_tools import TOOLS; print(f'Tools: {[t.name for t in TOOLS]}')"
```
Expected: `Tools: ['calculator']`

- [ ] **Step 3: Commit tool registry**

```bash
git add backend/agent_tools/__init__.py
git commit -m "feat: add simple tool registry with metadata"
```

---

## Task 3: Implement Agent Class

**Files:**
- Modify: `agent_from_scratch/backend/agent.py`

- [ ] **Step 1: Write test for Agent**

File: `agent_from_scratch/tests/test_agent.py`

```python
import unittest
import sqlite3
from agent import Agent
from llm_wrapper import LLMWrapper


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.llm = LLMWrapper()
        self.agent = Agent(
            system_prompt="You are a math assistant. Use the calculator tool when needed.",
            llm=self.llm,
            session_id="test"
        )

    def test_agent_initialization(self):
        self.assertEqual(self.agent.system_prompt, "You are a math assistant. Use the calculator tool when needed.")
        self.assertEqual(self.agent.session_id, "test")

    def test_agent_creates_sqlite_table(self):
        cursor = self.agent.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        self.assertIsNotNone(cursor.fetchone())

    def test_agent_saves_and_loads_messages(self):
        self.agent._save_message("user", "Hello", "text")
        history = self.agent._load_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "user")

    def test_agent_run_returns_text(self):
        response = self.agent.run("What is 2 + 2?", max_steps=3)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_agent_uses_calculator_tool(self):
        response = self.agent.run("Calculate 15 * 3", max_steps=3)
        self.assertIn("45", response)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd agent_from_scratch
python -m unittest tests.test_agent -v
```
Expected: FAIL (Agent class incomplete)

- [ ] **Step 3: Implement Agent class**

File: `agent_from_scratch/backend/agent.py`

```python
import sqlite3
import json
from typing import Any
from llm_wrapper import LLMWrapper
from agent_tools import get_tool_definitions, execute_tool


class Agent:
    def __init__(
        self,
        system_prompt: str,
        llm: LLMWrapper,
        session_id: str = "default"
    ):
        self.system_prompt = system_prompt
        self.llm = llm
        self.session_id = session_id
        self.conn = sqlite3.connect(":memory:")
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _save_message(self, role: str, content: Any, message_type: str = "text"):
        cursor = self.conn.cursor()
        content_str = content if isinstance(content, str) else json.dumps(content)
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, message_type) VALUES (?, ?, ?, ?)",
            (self.session_id, role, content_str, message_type)
        )
        self.conn.commit()

    def _load_history(self, limit: int = 20) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content, message_type FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (self.session_id, limit)
        )
        return [
            {"role": row[0], "content": row[1], "message_type": row[2]}
            for row in cursor.fetchall()
        ]

    def run(self, user_input: str, max_steps: int = 5) -> str:
        """Run agent loop: LLM reasons, picks tool, observes result, responds."""
        # Save user message
        self._save_message("user", user_input, "text")

        # Build context from history
        history = self._load_history()
        contents = []
        for msg in history:
            if msg["message_type"] == "text":
                if msg["role"] == "user":
                    contents.append(self.llm.create_user_content(msg["content"]))
                elif msg["role"] == "assistant":
                    contents.append(self.llm.create_user_content("[Assistant]: " + msg["content"]))

        # Add current user input
        contents.append(self.llm.create_user_content(user_input))

        # Get tool definitions
        tool_definitions = get_tool_definitions()

        # Agent loop: LLM reasons and may call tools
        final_text = ""
        for _ in range(max_steps):
            response = self.llm.generate(contents=contents, tool_definitions=tool_definitions)

            # Save assistant response
            if response.text:
                final_text = response.text
                self._save_message("assistant", response.text, "text")

            # If no function calls, return the text response
            if not response.function_calls:
                return final_text

            # Execute tools and collect results
            tool_response_parts = []
            for function_call in response.function_calls:
                # Execute the tool
                result = execute_tool(function_call.name, function_call.args)

                # Save tool call to memory
                self._save_message(
                    "tool",
                    {"name": function_call.name, "args": function_call.args, "result": result},
                    "function_call"
                )

                # Create response part for LLM
                tool_response_part = self.llm.create_tool_response_part(
                    function_call=function_call,
                    response=result
                )
                tool_response_parts.append(tool_response_part)

            # Add tool responses to conversation
            contents.append(response.content)
            contents.append(self.llm.create_tool_response_content(tool_response_parts))

        return final_text
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd agent_from_scratch
python -m unittest tests.test_agent -v
```
Expected: All tests pass

- [ ] **Step 5: Commit Agent implementation**

```bash
git add backend/agent.py tests/test_agent.py
git commit -m "feat: implement simple Agent class with SQLite memory and tool use"
```

---

## Task 4: Update main.py to Use Agent

**Files:**
- Modify: `agent_from_scratch/backend/main.py`

- [ ] **Step 1: Update main.py**

File: `agent_from_scratch/backend/main.py`

```python
from pathlib import Path
from dotenv import load_dotenv
from agent import Agent
from llm_wrapper import LLMWrapper

load_dotenv(Path(__file__).with_name(".env"))


def main():
    llm = LLMWrapper()
    agent = Agent(
        system_prompt="You are a helpful math assistant. When the user asks about math, use the calculator tool.",
        llm=llm,
        session_id="cli"
    )

    print("Math Agent (type 'exit' to quit)")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = agent.run(user_input, max_steps=5)
            print(f"\nAgent: {response}")
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the CLI manually**

```bash
cd agent_from_scratch/backend
python main.py
```

Test inputs:
- "What is 2 + 2?"
- "Calculate (15 * 3) / 5"
- "What is 100 / 4 + 7?"
- "exit"

Expected: Agent uses calculator tool and responds with correct results

- [ ] **Step 3: Run all tests**

```bash
cd agent_from_scratch
python tests/run_tests.py
```
Expected: All tests pass

- [ ] **Step 4: Commit main.py update**

```bash
git add backend/main.py
git commit -m "feat: update main.py to use Agent class"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✓ Agent class with system prompt, LLM, session_id
- ✓ SQLite `:memory:` for conversation history
- ✓ Tool registry with metadata (Tool class)
- ✓ Agent loop: LLM reasons → picks tool → observes result → responds
- ✓ Simple, beginner-friendly design

**Placeholder scan:**
- ✓ No TBD, TODO, or "implement later"
- ✓ All code blocks are complete
- ✓ Actual test assertions included

**Type consistency:**
- ✓ `Agent.run()` returns `str`
- ✓ `_save_message()` and `_load_history()` signatures match
- ✓ Tool registry uses `Tool` dataclass

**Scope check:**
- ✓ Single focused plan
- ✓ No long-term memory (out of scope)
- ✓ No vector search (out of scope)
- ✓ Simple enough for learning goal
