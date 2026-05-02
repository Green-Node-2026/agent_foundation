# Repository Guidelines

## Project Structure & Module Organization

This repository contains a minimal single-tool agent for Task 1.3. The main entry point is `main.py`, which configures the Gemini client, registers the `calculate` tool, and runs the tool-calling loop. Calculator parsing and evaluation live in `calculator.py`; keep expression parsing concerns there rather than in the agent loop. Runtime configuration is loaded from `.env`, with expected variables documented by `.env.example`. Python dependencies are listed in `requirements.txt`. There is currently no committed test directory.

## Build, Test, and Development Commands

Create and activate a virtual environment before installing dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the demo agent locally:

```powershell
python main.py
```

Use a direct calculator smoke check when changing parser behavior:

```powershell
python -c "from calculator import calculator; print(calculator('4 + 99 / 5'))"
```

## Coding Style & Naming Conventions

Use Python with 4-space indentation and PEP 8-style formatting. Prefer `snake_case` for new functions and variables, `PascalCase` for classes such as `Lexer` and `Parser`, and uppercase names for module-level constants such as `API_KEY` and `MODEL`. Keep agent orchestration in `main.py`; keep arithmetic tokenization, parsing, and validation in `calculator.py`. Do not replace the parser with `eval`.

## Testing Guidelines

No formal testing framework or coverage threshold is currently committed. For new behavior, add focused `pytest` tests under `tests/`, using names like `tests/test_calculator.py` and `test_division_by_zero()`. Prioritize parser edge cases, invalid input, and tool response shape. If `pytest` is added, document it in `requirements.txt` or a separate development requirements file and run:

```powershell
python -m pytest
```

## Commit & Pull Request Guidelines

Recent history uses short messages with prefixes such as `feat:` and `chore:` plus occasional task labels, for example `feat: [task_1.3] agent with 1 tool`. Keep commits concise and action-oriented. Pull requests should describe the behavior change, list manual or automated checks run, mention `.env` or dependency changes, and link the relevant task or issue when available.

## Security & Configuration Tips

Do not commit `.env`, API keys, or generated cache files. Keep `.env.example` free of secrets and update it when required configuration changes. Treat Gemini model names and API keys as runtime configuration, not hardcoded project policy.
