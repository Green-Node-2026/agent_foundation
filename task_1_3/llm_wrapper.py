import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types


@dataclass
class LLMResponse:
    content: Any
    function_calls: list[Any]
    text: str


@dataclass
class SimpleFunctionCall:
    name: str
    args: dict
    call_id: str | None = None


@dataclass
class SimpleFunctionResponse:
    name: str
    response: dict
    call_id: str | None = None


@dataclass
class SimplePart:
    text: str | None = None
    function_call: SimpleFunctionCall | None = None
    function_response: SimpleFunctionResponse | None = None


@dataclass
class SimpleContent:
    role: str
    parts: list[SimplePart]


class LLMProvider(ABC):
    @abstractmethod
    def create_user_content(self, prompt: str) -> Any:
        pass

    @abstractmethod
    def create_tool_response_content(self, tool_response_parts: list[Any]) -> Any:
        pass

    @abstractmethod
    def create_tool_response_part(self, function_call: Any, response: dict) -> Any:
        pass

    @abstractmethod
    def generate(self, contents: list[Any], tool_definitions: list[dict]) -> LLMResponse:
        pass


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def create_user_content(self, prompt: str) -> types.Content:
        return types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )

    def create_tool_response_content(
        self, tool_response_parts: list[types.Part]
    ) -> types.Content:
        return types.Content(role="tool", parts=tool_response_parts)

    def create_tool_response_part(self, function_call: Any, response: dict) -> types.Part:
        return types.Part.from_function_response(
            name=function_call.name,
            response=response,
        )

    def generate(
        self,
        contents: list[types.Content],
        tool_definitions: list[dict],
    ) -> LLMResponse:
        tool_declarations = [
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters_json_schema=tool["parameters_json_schema"],
            )
            for tool in tool_definitions
        ]
        config = types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=tool_declarations)],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            ),
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        return LLMResponse(
            content=response.candidates[0].content,
            function_calls=response.function_calls or [],
            text=response.text or "",
        )


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.previous_response_id: str | None = None

    def create_user_content(self, prompt: str) -> SimpleContent:
        return SimpleContent(role="user", parts=[SimplePart(text=prompt)])

    def create_tool_response_content(
        self, tool_response_parts: list[SimplePart]
    ) -> SimpleContent:
        return SimpleContent(role="tool", parts=tool_response_parts)

    def create_tool_response_part(
        self, function_call: SimpleFunctionCall, response: dict
    ) -> SimplePart:
        return SimplePart(
            function_response=SimpleFunctionResponse(
                name=function_call.name,
                response=response,
                call_id=function_call.call_id,
            )
        )

    def generate(self, contents: list[Any], tool_definitions: list[dict]) -> LLMResponse:
        response = self.client.responses.create(
            model=self.model,
            input=self._to_openai_input(contents),
            tools=self._to_openai_tools(tool_definitions),
            previous_response_id=self.previous_response_id,
        )
        self.previous_response_id = response.id

        function_calls = []
        text_parts = []
        for item in response.output:
            if item.type == "function_call":
                function_calls.append(
                    SimpleFunctionCall(
                        name=item.name,
                        args=json.loads(item.arguments or "{}"),
                        call_id=item.call_id,
                    )
                )
            elif item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        text_parts.append(content.text)

        parts = [
            SimplePart(text=text)
            for text in text_parts
        ] + [
            SimplePart(function_call=function_call)
            for function_call in function_calls
        ]

        return LLMResponse(
            content=SimpleContent(role="model", parts=parts),
            function_calls=function_calls,
            text="\n".join(text_parts),
        )

    def _to_openai_input(self, contents: list[Any]) -> list[dict]:
        if self.previous_response_id:
            latest_content = contents[-1] if contents else None
            return self._content_to_openai_items(latest_content)

        input_items = []
        for content in contents:
            input_items.extend(self._content_to_openai_items(content))
        return input_items

    def _content_to_openai_items(self, content: Any) -> list[dict]:
        if not content:
            return []

        items = []
        for part in getattr(content, "parts", []):
            if getattr(part, "text", None):
                items.append({"role": "user", "content": part.text})

            function_response = getattr(part, "function_response", None)
            if function_response:
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": function_response.call_id,
                        "output": json.dumps(function_response.response),
                    }
                )
        return items

    def _to_openai_tools(self, tool_definitions: list[dict]) -> list[dict]:
        return [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters_json_schema"],
            }
            for tool in tool_definitions
        ]


class LLMWrapper:
    def __init__(self, provider: str | None = None):
        provider_name = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

        if provider_name == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Missing GEMINI_API_KEY in task_1_3/.env")

            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.provider = GeminiProvider(api_key=api_key, model=model)
            return

        if provider_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in task_1_3/.env")

            model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
            self.provider = OpenAIProvider(api_key=api_key, model=model)
            return

        raise ValueError(f"Unsupported LLM provider: {provider_name}")

    def create_user_content(self, prompt: str) -> Any:
        return self.provider.create_user_content(prompt)

    def create_tool_response_content(self, tool_response_parts: list[Any]) -> Any:
        return self.provider.create_tool_response_content(tool_response_parts)

    def create_tool_response_part(self, function_call: Any, response: dict) -> Any:
        return self.provider.create_tool_response_part(function_call, response)

    def generate(self, contents: list[Any], tool_definitions: list[dict]) -> LLMResponse:
        return self.provider.generate(contents, tool_definitions)
