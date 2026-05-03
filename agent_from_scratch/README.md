# Impeccable Multi-Agent System

This project is a high-end, minimalist multi-agent system built from scratch. It features a robust tool-calling loop, persistent session history, and a premium "Impeccable" interface.

## Key Features

- **Multi-Agent Orchestration:** Designed to coordinate and execute tasks using specialized tools.
- **Session Persistence:** Full history reconstruction on the backend ensures context is preserved across reloads.
- **Minimalist "Impeccable" UI:** A high-contrast, technically polished interface focused on content and clarity.
- **Local Tool Execution:** A secure, locally implemented calculator tool (no `eval`).
- **Provider Agnostic:** Supports both Gemini and OpenAI providers.

## Project Structure

```text
agent_from_scratch/
  backend/
    tools/
      calculator.py       # safe arithmetic lexer/parser
      registry.py         # centralized tool registration
    llm_wrapper.py        # adapter for Gemini/OpenAI
    agent.py              # agent class with history reconstruction
    server.py             # FastAPI server for the multi-agent UI
    requirements.txt      # Python dependencies
    .env.example          # backend config template
  frontend/
    src/                  # Minimalist React chat UI
    package.json          # Vite/React scripts
  unittest/
    run_tests.py          # colorized unittest runner
    test_calculator.py    # calculator tests
    test_history.py       # history reconstruction tests
```

## Tool

The only tool is:

```python
calculate(expression: str) -> dict
```

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

The calculator is implemented locally in `backend/tools/calculator.py`. It supports `+`, `-`, `*`, `/`, and parentheses. It intentionally avoids `eval`.

## How It Works

The agent loop in `backend/agent.py` follows this sequence:

1. Convert the user prompt into LLM conversation content.
2. Send the prompt plus tool schemas (from `tools/registry.py`) to the model.
3. If the model returns a function call, execute the local Python tool.
4. Convert the local result into a tool response.
5. Append that response to the conversation history.
6. Call the model again so it can produce the final natural-language answer.

Pattern:

```text
user -> model -> tool call -> local tool execution -> tool response -> model -> final answer
```

## Backend Setup

From the repository root:

```powershell
cd agent_from_scratch\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `agent_from_scratch\backend\.env` from `.env.example`.

Gemini example:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

OpenAI example:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-nano-2026-03-17
```

## Run The CLI Agent

From `agent_from_scratch\backend`:

```powershell
python main.py
```

Enter a prompt such as:

```text
Calculate (45 * 2) / 5
```

## Run The Browser Demo

Terminal 1, start the FastAPI server:

```powershell
cd agent_from_scratch\backend
python server.py
```

Or with uvicorn directly:

```powershell
cd agent_from_scratch\backend
uvicorn server:app --host 127.0.0.1 --port 5000 --reload
```

Terminal 2, start the Vite app:

```powershell
cd agent_from_scratch\frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The React app sends prompts to `http://127.0.0.1:5000/api/chat`, displays the final answer, and shows the calculator tool-call trace.

## Tests

From `agent_from_scratch`:

```powershell
python unittest\run_tests.py
```

The current tests cover:

- happy-path arithmetic
- parentheses and whitespace handling
- invalid input and malformed numbers
- division by zero
- the `calculate()` tool wrapper result and error payloads

## Notes

- Tool use usually needs at least two model turns: one for the model to request the tool, and one after the tool response to produce the final answer.
- If `max_steps=1`, the agent may call the tool correctly but stop before generating the final natural-language answer.
- Tool arguments are described with Pydantic and converted into JSON Schema for the LLM function declaration.
- Keep `.env` files local. Only commit `.env.example` templates with placeholder values.
