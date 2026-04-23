### set of sample tool descriptions

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a city",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
    {
        "name": "get_climate",
        "description": "Get general climate information about a city or region",
        "input_schema": {
            "type": "object",
            "properties": {"place": {"type": "string"}},
            "required": ["place"],
        },
    },
    {
        "name": "search_web",
        "description": "Search the web for recent information",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

import os
from anthropic import Anthropic

def getLanguageModel():
    try:
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")
        base_url = os.getenv("ANTHROPIC_BASE_URL")

        client = Anthropic(
            api_key=api_key,
            base_url=base_url,
        )
        return client

    except Exception as e:
        print(f"Error: {e}")
        return None
import os
from anthropic import Anthropic

### set of sample tool descriptions

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a city",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
    {
        "name": "get_climate",
        "description": "Get general climate information about a city or region",
        "input_schema": {
            "type": "object",
            "properties": {"place": {"type": "string"}},
            "required": ["place"],
        },
    },
    {
        "name": "search_web",
        "description": "Search the web for recent information",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]


def getLanguageModel():
    try:
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")
        base_url = os.getenv("ANTHROPIC_BASE_URL")

        client = Anthropic(
            api_key=api_key,
            base_url=base_url,
        )
        return client

    except Exception as e:
        print(f"Error: {e}")
        return None


def test_tool_selection(user_request):
    client = getLanguageModel()
    if client is None:
        return

    model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    response = client.messages.create(
        model=model_name,
        max_tokens=256,
        tools=tools,
        messages=[{"role": "user", "content": user_request}],
    )

    print(f"User request: {user_request}")
    print(f"Stop reason: {response.stop_reason}")

    tool_used = False
    for block in response.content:
        if block.type == "tool_use":
            tool_used = True
            print(f"Tool selected: {block.name}")
            print(f"Tool input: {block.input}")

    if not tool_used:
        print("Model did not choose any tool.")
        for block in response.content:
            if block.type == "text":
                print(f"Model response: {block.text}")


if __name__ == "__main__":
    sample_request = "Thời tiết ở Hồ Chí Minh hôm nay như thế nào?"
    test_tool_selection(sample_request)