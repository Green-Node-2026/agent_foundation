import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://r8h87rt.9router.com/v1"
DEFAULT_MODEL = "cx/gpt-5.5"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip().strip("\"'")


@dataclass
class ChatCompletionProvider:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL

    def complete(self, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
        }
        request = Request(
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data["choices"][0]["message"]["content"]


class ReActChatAgent:
    def __init__(self, llm: ChatCompletionProvider, max_steps: int = 5):
        self.llm = llm
        self.max_steps = max_steps

    def run(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a ReAct agent with one tool.\n"
                    "Tool: calculator(expression: string) -> number\n\n"
                    "Use this exact format:\n"
                    "Thought: reason about what to do next\n"
                    "Action: calculator(\"expression\")\n"
                    "or\n"
                    "Thought: reason about the final answer\n"
                    "Final: final answer to the user\n\n"
                    "After an Observation, continue with another Thought."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        for _ in range(self.max_steps):
            assistant_text = self.llm.complete(messages)
            print(f"\nAssistant:\n{assistant_text}")
            messages.append({"role": "assistant", "content": assistant_text})

            final_answer = self._parse_final(assistant_text)
            if final_answer:
                return final_answer

            action_expression = self._parse_calculator_action(assistant_text)
            if not action_expression:
                return assistant_text

            observation = self._calculate(action_expression)
            print(f"\nObservation: {observation}")
            messages.append(
                {
                    "role": "user",
                    "content": f"Observation: {observation}",
                }
            )

        return "Reached maximum ReAct steps before a final answer."

    def _parse_final(self, text: str) -> str | None:
        match = re.search(r"Final:\s*(.+)", text, flags=re.DOTALL)
        return match.group(1).strip() if match else None

    def _parse_calculator_action(self, text: str) -> str | None:
        match = re.search(
            r"Action:\s*calculator\((?P<quote>['\"])(?P<expr>.*?)(?P=quote)\)",
            text,
            flags=re.DOTALL,
        )
        return match.group("expr").strip() if match else None

    def _calculate(self, expression: str) -> str:
        allowed = set("0123456789+-*/(). ")
        if any(char not in allowed for char in expression):
            return f"Tool error: unsupported character in expression {expression!r}"

        try:
            return str(eval(expression, {"__builtins__": {}}, {}))
        except Exception as exc:
            return f"Tool error: {exc}"


def main() -> int:
    load_env_file(Path(__file__).with_name(".env"))

    api_key = os.getenv("GPT55_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing GPT55_API_KEY or OPENAI_API_KEY")

    llm = ChatCompletionProvider(
        api_key=api_key,
        base_url=os.getenv("GPT55_BASE_URL", DEFAULT_BASE_URL),
        model=os.getenv("GPT55_MODEL", DEFAULT_MODEL),
    )
    agent = ReActChatAgent(llm)
    answer = agent.run("What is (20 + 5) * 2? Think step by step and use the tool.")
    print(f"\nFinal answer:\n{answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
