import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
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
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_payload(prompt: str, api_style: str) -> dict:
    model = os.getenv("GPT55_MODEL", DEFAULT_MODEL)

    if api_style == "chat":
        return {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

    return {
        "model": model,
        "input": prompt,
    }


def post_json(url: str, payload: dict, api_key: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url=url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AI-agent-demo/1.0",
        },
    )

    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_text(response: dict) -> str | None:
    if response.get("output_text"):
        return response["output_text"]

    choices = response.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        if message.get("content"):
            return message["content"]
        if choices[0].get("text"):
            return choices[0]["text"]

    output = response.get("output") or []
    text_parts = []
    for item in output:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                text_parts.append(content["text"])

    return "\n".join(text_parts) if text_parts else None


def main() -> int:
    load_env_file(Path(__file__).with_name(".env"))

    parser = argparse.ArgumentParser(description="Call the GPT-5.5 endpoint.")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Say hello in one short sentence.",
        help="Prompt to send to GPT-5.5.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("GPT55_BASE_URL", DEFAULT_BASE_URL),
        help="OpenAI-compatible base URL, usually ending in /v1.",
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("GPT55_ENDPOINT"),
        help="Full endpoint URL. Overrides --base-url.",
    )
    parser.add_argument(
        "--api-style",
        choices=["responses", "chat"],
        default=os.getenv("GPT55_API_STYLE", "responses"),
        help="Payload style to send.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the full JSON response.",
    )
    args = parser.parse_args()

    api_key = os.getenv("GPT55_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Missing API key. Set GPT55_API_KEY or OPENAI_API_KEY.", file=sys.stderr)
        return 1

    payload = build_payload(args.prompt, args.api_style)
    if args.endpoint:
        url = args.endpoint
    else:
        route = "chat/completions" if args.api_style == "chat" else "responses"
        url = f"{args.base_url.rstrip('/')}/{route}"

    try:
        response = post_json(url, payload, api_key)
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8')}", file=sys.stderr)
        return 1
    except URLError as error:
        print(f"Request failed: {error.reason}", file=sys.stderr)
        return 1

    if args.raw:
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return 0

    text = extract_text(response)
    print(text if text else json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
