import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from typing import Callable
from calculator import calculator
from google.genai import types

load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

class CalculatorInput(BaseModel):
    # metadata for LLM 
    expression: str = Field(
        ...,
        description="A math expression such as '2+2' or '(15*3)/5'"
    )

TOOL_REGISTRY: dict[str, Callable[..., dict]] = {}
TOOL_DECLARATIONS: list[types.FunctionDeclaration] = []

def getClient():
    if not API_KEY:
        raise ValueError("Missing GEMINI_API_KEY in task_1_3/.env")

    client = genai.Client(api_key=API_KEY)
    return client 

def toolCall(
    args_schema: type[BaseModel],
):
    def decorator(func: Callable[..., dict]):
        name = func.__name__
        description = func.__doc__ or "No description provided."
        
        TOOL_REGISTRY[name] = func

        declaration = types.FunctionDeclaration(
            name=name,
            description=description,
            parameters_json_schema=args_schema.model_json_schema(),
        )

        TOOL_DECLARATIONS.append(declaration)

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
    client = getClient()
    
    tools = [
        types.Tool(function_declarations=TOOL_DECLARATIONS)
    ] 
    
    config = types.GenerateContentConfig(
        tools=tools,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="AUTO"
            )
        ),
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        )
    ]
    # print(contents)
    for _ in range(max_steps):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        model_content = response.candidates[0].content
        contents.append(model_content)
        
        # print(contents)

        function_calls = response.function_calls
        
        if not function_calls:
            return response.text or ""

        tool_response_parts = []

        # implement tool-chain
        for function_call in function_calls:
            tool_result = execute_tool(function_call)

            tool_response_part = types.Part.from_function_response(
                name=function_call.name,
                response=tool_result,
            )

            tool_response_parts.append(tool_response_part)

        contents.append(
            types.Content(
                role="tool",
                parts=tool_response_parts,
            )
        )

    return "The agent reached the maximum number of tool-calling steps."
        
    
def main():
    ans = agent_loop(prompt="what is the result of expression: 4 + 99 / 5", max_steps=2)
    print(ans)
    
if __name__ == "__main__":
    main()

