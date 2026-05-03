from typing import Callable, Any 
from pydantic import BaseModel, Field

class Agent:
    def __init__(self, system_prompt: str, client: Any, model: str = "gpt-4o"):
        self.system_prompt = system_prompt
        self.client = client
        self.model = model
        self.messages = []
        self.tool_registry: dict[str, Callable[..., dict]] = {}
        self.tool_definition: list[dict] = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def toolCall(self, args_schema: type[BaseModel]):
            def decorator(func: Callable[..., dict]):
                name = func.__name__
                description = func.__doc__ or "No description provided."

                self.tool_registry[name] = func
                self.tool_definition.append({
                    "name": name,
                    "description": description,
                    "parameters_json_schema": args_schema.model_json_schema(),                    
                })
                return func
            return decorator

    def execute_tool(self, functionCall):
        name = functionCall.name
        args = functionCall.args

        return self.tool_registry[name](**args)

    def run(self, prompt: str, history: list[dict] | None = None, max_steps: int = 5):
        contents = []

        # Add system prompt
        if self.system_prompt:
            contents.append(self.client.create_system_content(self.system_prompt))

        # Reconstruct history, skip system messages (already added above)
        if history:
            for item in history:
                if item.get("role") != "system":
                    contents.append(self.client.reconstruct_content(item))

        # Add new user prompt
        contents.append(
            self.client.create_user_content(prompt)
        )

        for _ in range(max_steps):
            response = self.client.generate(
                contents=contents,
                tool_definitions=self.tool_definition,
            )

            contents.append(response.content)

            # Yield model response
            yield {'type': 'model', 'content': response.content}

            function_calls = response.function_calls
            if not function_calls:
                yield {'type': 'done', 'history': contents}
                return

            tool_response_parts = []

            for function_call in function_calls:
                # Yield tool call
                yield {
                    'type': 'tool_call',
                    'name': function_call.name,
                    'args': function_call.args
                }

                tool_result = self.execute_tool(function_call)

                # Yield tool result
                yield {
                    'type': 'tool_result',
                    'name': function_call.name,
                    'result': tool_result
                }

                tool_response_part = self.client.create_tool_response_part(
                    function_call=function_call,
                    response=tool_result,
                )

                tool_response_parts.append(tool_response_part)

            contents.append(
                self.client.create_tool_response_content(tool_response_parts)
            )

        yield {'type': 'done', 'history': contents}
