# Repository Guidelines

## Scope

This folder contains the Task 1.3 calculator agent. Keep changes focused on the local agent, its browser demo, and its tests. Do not introduce a framework agent unless the task explicitly asks for that comparison.

## Project Structure

- `backend/agent.py`: agent class with tool-calling loop and history reconstruction.
- `backend/llm_wrapper.py`: provider-specific LLM request/response adapter.
- `backend/server.py`: FastAPI server for the browser demo.
- `backend/tools/calculator.py`: arithmetic lexer/parser and evaluator.
- `backend/tools/registry.py`: centralized tool registration.
- `backend/.env.example`: placeholder runtime configuration.
- `frontend/src/`: Minimalist React/Vite chat UI.
- `unittest/run_tests.py`: colorized local test runner.
- `unittest/test_calculator.py`: calculator and tool-wrapper tests.
- `unittest/test_history.py`: session history reconstruction tests.

## Development Commands

Install backend dependencies:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the CLI agent:

```powershell
cd backend
python main.py
```

Run the browser API (FastAPI):

```powershell
cd backend
python server.py
```

Run the React frontend:

```powershell
cd frontend
npm install
npm run dev
```

Run tests:

```powershell
python unittest\run_tests.py
```

Use this smoke check when changing calculator behavior:

```powershell
python -c "import sys; sys.path.append('backend'); from tools.calculator import calculator; print(calculator('4 + 99 / 5'))"
```

## Coding Guidelines

- Use Python with 4-space indentation and PEP 8-style naming.
- Use `snake_case` for functions and variables, `PascalCase` for classes, and uppercase names for constants.
- Keep orchestration in `backend/agent.py` and `backend/server.py`.
- Keep model/provider conversion in `backend/llm_wrapper.py`.
- Keep arithmetic tokenization, parsing, validation, and evaluation in `backend/tools/calculator.py`.
- Do not replace the calculator parser with `eval`.
- Keep frontend changes inside `frontend/` unless backend API shape changes.
- Adhere to the "Minimalist Interface" design language: high contrast, sharp typography, no unnecessary borders.

## Testing Guidelines

Add focused tests when changing parser behavior, tool response shape, or agent-loop contracts. Prefer direct unit tests for calculator edge cases before adding LLM-dependent checks.

Important cases:

- valid arithmetic with operator precedence
- parentheses and whitespace
- invalid characters
- malformed numbers
- unmatched parentheses
- division by zero
- `calculate()` success and error payloads

## Configuration And Security

- Do not commit `.env`, API keys, `venv/`, `node_modules/`, `__pycache__/`, or `*.pyc`.
- Keep `.env.example` free of secrets.
- Treat model names and API keys as runtime configuration.
- If a secret is accidentally tracked, remove it from Git with `git rm --cached` and rotate the key if it was pushed.

## Commit And PR Notes

Recent commit messages use short prefixes such as `feat:` and `chore:`. Keep messages concise and action-oriented. PRs should mention behavior changes, commands run, dependency changes, and any required `.env` updates.
