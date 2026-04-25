# Task 1.3 - Single-Tool Agent

Task 1.3 builds a simple agent that can use exactly one tool: `calculate`.

The project does not use an agent framework. It calls the Gemini API directly, provides one tool schema, executes the tool locally, then sends the tool result back to the model so the model can produce the final answer.

## Goal

- Understand the basic tool-calling loop
- Build a minimal agent with one tool
- Keep the implementation small and easy to inspect

## Tool

The only tool is:

- `calculate(expression: str) -> dict`

Example input:

```json
{
  "expression": "4 + 99 / 5"
}
```

Example output:

```json
{
  "expression": "4 + 99 / 5",
  "result": "23.8"
}
```

## How It Works

The agent loop in [main.py](/abs/c:/Tailieu/HK252/vng/agent_foundation/task_1_3/main.py) works like this:

1. Send the user prompt and tool declarations to Gemini.
2. If Gemini returns a function call, execute the local Python function.
3. Convert the tool result into a `function_response`.
4. Append that tool response back into the conversation history.
5. Call Gemini again so it can generate the final natural-language answer.

This is the basic pattern:

`user -> model -> tool call -> local tool execution -> tool response -> model -> final answer`

## Files

- [main.py](/abs/c:/Tailieu/HK252/vng/agent_foundation/task_1_3/main.py): Gemini client setup, tool registration, agent loop
- [calculator.py](/abs/c:/Tailieu/HK252/vng/agent_foundation/task_1_3/calculator.py): safe calculator implementation using a lexer and parser
- [.env.example](/abs/c:/Tailieu/HK252/vng/agent_foundation/task_1_3/.env.example): example environment variables
- [requirements.txt](/abs/c:/Tailieu/HK252/vng/agent_foundation/task_1_3/requirements.txt): Python dependencies

## Why The Calculator Is Implemented Locally

This task avoids `eval` and instead parses expressions manually in [calculator.py](/abs/c:/Tailieu/HK252/vng/agent_foundation/task_1_3/calculator.py). That keeps the tool safer and also makes the tool behavior easier to explain.

Supported operators:

- `+`
- `-`
- `*`
- `/`
- parentheses `()`

## Setup

Install dependencies:

```powershell
pip install -r task_1_3\requirements.txt
```

Create `task_1_3/.env`:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## Run

```powershell
python task_1_3\main.py
```

## Notes

- A tool call usually needs at least 2 model turns:
  - one turn for the model to request the tool
  - one turn after the tool response to produce the final answer
- If `max_steps=1`, the agent may call the tool correctly but still stop before generating the final natural-language answer.
- Tool arguments are described with Pydantic and converted into JSON Schema for Gemini function declarations.

## Learning Outcome

After finishing this task, you should be comfortable with:

- defining a tool schema
- letting the model decide when to call a tool
- executing the tool locally
- returning tool results back to the model
- understanding the minimal agent loop without a framework
