import os
from pathlib import Path

from google import genai
from google.genai import types


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")

        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(Path(__file__).with_name(".env"))


TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_weather",
        description="Get the current weather in a city",
        parameters_json_schema={
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    ),
    types.FunctionDeclaration(
        name="get_climate",
        description="Get general climate information about a city or region",
        parameters_json_schema={
            "type": "object",
            "properties": {"place": {"type": "string"}},
            "required": ["place"],
        },
    ),
    types.FunctionDeclaration(
        name="search_web",
        description="Search the web for recent information",
        parameters_json_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
]


def get_language_model() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing Google GenAI credentials. Set GEMINI_API_KEY in task_1_2/.env "
            "or export it before running the script."
        )

    return genai.Client(api_key=api_key)


def test_tool_selection(user_request: str) -> None:
    client = get_language_model()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    response = client.models.generate_content(
        model=model_name,
        contents=user_request,
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            ),
        ),
    )

    print(f"User request: {user_request}")

    function_calls = response.function_calls or []
    if function_calls:
        for function_call in function_calls:
            print(f"Tool selected: {function_call.name}")
            print(f"Tool input: {dict(function_call.args)}")
        return

    print("Model did not choose any tool.")
    print(f"Model response: {response.text or ''}")


if __name__ == "__main__":
    sample_request = (
        "For my trip planning, do all three tasks: get the current weather in "
        "Ho Chi Minh City, get general climate information for Bangkok, and "
        "search the web for recent travel advisories for Thailand."
    )
    test_tool_selection(sample_request)
