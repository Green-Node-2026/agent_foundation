from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Callable
from calculator import calculator
from llm_wrapper import LLMWrapper

load_dotenv(Path(__file__).with_name(".env"))

class CalculatorInput(BaseModel):
    # metadata for LLM
    expression: str = Field(
        ...,
        description="A math expression such as '2+2' or '(15*3)/5'"
    )

TOOL_REGISTRY: dict[str, Callable[..., dict]] = {}
TOOL_DEFINITIONS: list[dict] = []

def toolCall(args_schema: type[BaseModel]):
    def decorator(func: Callable[..., dict]):
        name = func.__name__
        description = func.__doc__ or "No description provided."

        TOOL_REGISTRY[name] = func

        TOOL_DEFINITIONS.append(
            {
                "name": name,
                "description": description,
                "parameters_json_schema": args_schema.model_json_schema(),
            }
        )

        return func

    return decorator

@toolCall(args_schema=CalculatorInput)
def calculate(expression: str) -> dict:
    "Calculate a basic math expression."
    try:
        result = str(calculator(expression))
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "expression": expression,
            "result": str(e)
        }


def execute_tool(functionCall):
    name = functionCall.name
    args = functionCall.args

    return TOOL_REGISTRY[name](**args)


def agent_loop(prompt: str, max_steps: int = 5):
    llm = LLMWrapper()

    contents = [
        llm.create_user_content(prompt)
    ]

    for _ in range(max_steps):
        response = llm.generate(
            contents=contents,
            tool_definitions=TOOL_DEFINITIONS,
        )

        contents.append(response.content)

        function_calls = response.function_calls
        if not function_calls:
            return contents

        tool_response_parts = []

        for function_call in function_calls:
            tool_result = execute_tool(function_call)

            tool_response_part = llm.create_tool_response_part(
                function_call=function_call,
                response=tool_result,
            )

            tool_response_parts.append(tool_response_part)

        contents.append(
            llm.create_tool_response_content(tool_response_parts)
        )

    return contents


def main():
    prompt = input("Enter prompt: ")
    history = agent_loop(prompt=prompt, max_steps=2 )
    for content in history:
        print(f"[{content.role}]")
        for part in content.parts:
            if part.text:
                print(f"Text: {part.text}")
            if part.function_call:
                print(f"Tool Call: {part.function_call.name}({part.function_call.args})")
            if part.function_response:
                print(f"Tool Response: {part.function_response.response}")
        print("-" * 20)

if __name__ == "__main__":
    main()

