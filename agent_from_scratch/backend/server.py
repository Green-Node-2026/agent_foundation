from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from llm_wrapper import LLMWrapper, TokenUsage
from agent import Agent
from tools.registry import register_tools
from db import SessionStore, SessionNotFound
import traceback
import json
import asyncio
import threading
import shutil
import os
from collections import defaultdict
from datetime import date
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Header
from queue import Queue

load_dotenv()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are an automated problem-solving AI assistant (Agent). Your task is to assist users by providing accurate information. You are equipped with tools and MUST DEFAULT TO USING THEM when necessary. Do not guess or hallucinate answers.

### CORE RULES:
1. Math & Calculation: ABSOLUTELY DO NOT perform mental math for any arithmetic operations (+, -, *, /). You must always use the `calculate` tool for any numbers.
2. Weather: Do not fabricate temperatures or weather conditions. You must use the `get_weather` tool to retrieve real-time data for specific locations.
3. File System Awareness:
   - You have access to a local file system located at `./backend/uploads/`.
   - When a user's prompt contains a `[Attached File: filename.ext]` marker, it means a new file has been placed in that directory.
   - You MUST use the `process_file` tool to read the content of these files before answering.
   - If you are unsure what files are available, use the `list_files` tool.
4. Multi-step Reasoning: If a user's request requires multiple steps, call the tools sequentially. Use the result from the first tool as the input for the next tool.
4. City Name Extraction: When users mention cities, extract and normalize the name:
   - Common abbreviations: HCM/Saigon → Ho Chi Minh, HN → Hanoi, DN → Da Nang
   - If the city name is ambiguous or unclear, make your best guess based on context
   - If you cannot determine the city at all, ask the user to clarify

### EXAMPLES (FEW-SHOT LEARNING):

--- EXAMPLE 1: SINGLE TOOL USAGE ---
User: "What is 235 multiplied by 45?"
Thought: The user requires a calculation. I must not calculate this mentally; I need to call the calculate tool.
Call Tool: `calculate` with args: {"expression": "235*45"}
Tool Result: {"expression": "235*45", "result": "10575"}
Assistant: "235 multiplied by 45 is 10,575."

--- EXAMPLE 2: SINGLE TOOL USAGE ---
User: "How is the weather in Saigon today?"
Thought: The user is asking for current weather information. "Saigon" refers to Ho Chi Minh City. I need to use the get_weather tool.
Call Tool: `get_weather` with args: {"location": "Ho Chi Minh"}
Tool Result: {"location": "Ho Chi Minh", "country": "Vietnam", "temperature": 32, "windspeed": 15}
Assistant: "The current weather in Saigon (Ho Chi Minh City) is 32°C with a wind speed of 15 km/h."

--- EXAMPLE 3: CITY NAME NORMALIZATION ---
User: "What's the weather in HCM?"
Thought: "HCM" is a common abbreviation for Ho Chi Minh City. I should expand it.
Call Tool: `get_weather` with args: {"location": "Ho Chi Minh"}
Tool Result: {"location": "Ho Chi Minh", "country": "Vietnam", "temperature": 30, "windspeed": 12}
Assistant: "The weather in HCM (Ho Chi Minh City) is 30°C with a wind speed of 12 km/h."

--- EXAMPLE 4: MULTI-STEP REASONING (CHAINING TOOLS) ---
User: "If you multiply the current temperature in Hanoi by 3, what is the result?"
Thought: Step 1: I need to get the current temperature in Hanoi. Step 2: I need to multiply that temperature by 3.
Call Tool 1: `get_weather` with args: {"location": "Hanoi"}
Tool Result 1: {"location": "Hanoi", "country": "Vietnam", "temperature": 25, "windspeed": 10}
Thought: The temperature is 25. Now I need to calculate 25 * 3.
Call Tool 2: `calculate` with args: {"expression": "25*3"}
Tool Result 2: {"expression": "25*3", "result": "75"}
Assistant: "The current temperature in Hanoi is 25°C. If you multiply this number by 3, the result is 75."

--- EXAMPLE 5: AMBIGUOUS CITY - ASK FOR CLARIFICATION ---
User: "What's the weather in Springfield?"
Thought: "Springfield" is ambiguous - there are many cities with this name. I should ask for clarification.
Assistant: "There are multiple cities named Springfield. Could you specify which one? For example, Springfield, Illinois or Springfield, Massachusetts?"

--- EXAMPLE 6: NORMAL CONVERSATION ---
User: "Hello, what can you do?"
Thought: This is a standard greeting. No tools are needed. But you must restrict to the specific domains from CORE RULES.
Assistant: "Hello! I am an AI assistant. I can help you calculate complex math expressions or check the current weather in any city. How can I assist you today?"
"""

client = LLMWrapper()
agent = Agent(system_prompt=SYSTEM_PROMPT, client=client)
register_tools(agent)


class UsageTracker:
    def __init__(self):
        self._data: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: {"prompt_tokens": 0, "completion_tokens": 0, "requests": 0}
        )

    def record(self, user_id: str, usage: TokenUsage | None) -> None:
        if usage is None:
            return
        key = (user_id, date.today().isoformat())
        bucket = self._data[key]
        bucket["prompt_tokens"] += usage.prompt_tokens
        bucket["completion_tokens"] += usage.completion_tokens
        bucket["requests"] += 1

    def today(self, user_id: str) -> dict:
        today = date.today().isoformat()
        bucket = self._data[(user_id, today)]
        return {
            "user_id": user_id,
            "date": today,
            "prompt_tokens": bucket["prompt_tokens"],
            "completion_tokens": bucket["completion_tokens"],
            "total_tokens": bucket["prompt_tokens"] + bucket["completion_tokens"],
            "requests": bucket["requests"],
        }


usage_tracker = UsageTracker()


try:
    session_store: SessionStore | None = SessionStore()
    print("[sessions] Redis connected")
except Exception as e:
    session_store = None
    print(f"[sessions] disabled: {e}")


def require_sessions() -> SessionStore:
    if session_store is None:
        raise HTTPException(status_code=503, detail="Session storage unavailable")
    return session_store


def serialize_usage(usage: TokenUsage | None) -> dict | None:
    if usage is None:
        return None
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str
    history: list[dict] | None = None


class SessionCreateRequest(BaseModel):
    title: str = ""


class SessionUpdateRequest(BaseModel):
    messages: list[dict]
    title: str | None = None


def parse_part(content):
    if content.role == "system":
        return None

    parts = []
    for part in content.parts:
        p = {}
        if part.text:
            p["text"] = part.text
        if part.function_call:
            p["function_call"] = {
                "name": part.function_call.name,
                "args": part.function_call.args,
                "call_id": part.function_call.call_id
            }
        if part.function_response:
            p["function_response"] = {
                "name": part.function_response.name,
                "response": part.function_response.response,
                "call_id": part.function_response.call_id
            }
        parts.append(p)
    return parts


def serialize_content(contents):
    serialized = []
    for content in contents:
        parts = parse_part(content)
        serialized.append({
            "role": content.role,
            "parts": parts
        })
    return serialized


def serialize_single_content(content):
    parts = parse_part(content)
    return {
        "role": content.role,
        "parts": parts
    }
    

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.get("/api/tools")
async def list_tools():
    """Return all available tools with their schemas"""
    tools = []
    for tool_def in agent.tool_definition:
        tools.append({
            "name": tool_def["name"],
            "description": tool_def["description"],
            "parameters": tool_def["parameters_json_schema"]
        })
    return {"tools": tools}


@app.get("/api/usage")
async def get_usage(x_user_id: str = Header(default="anonymous")):
    return usage_tracker.today(x_user_id)


@app.get("/api/sessions/health")
async def sessions_health():
    if session_store is None:
        return {"ok": False, "reason": "not configured"}
    return {"ok": session_store.health_check()}


@app.post("/api/sessions")
async def create_session(
    body: SessionCreateRequest,
    x_user_id: str = Header(default="anonymous"),
):
    return require_sessions().create(x_user_id, title=body.title)


@app.get("/api/sessions")
async def list_sessions(x_user_id: str = Header(default="anonymous")):
    return {"sessions": require_sessions().list_for_user(x_user_id)}


@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    x_user_id: str = Header(default="anonymous"),
):
    store = require_sessions()
    try:
        record = store.get(session_id)
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    if record["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return record


@app.patch("/api/sessions/{session_id}")
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    x_user_id: str = Header(default="anonymous"),
):
    store = require_sessions()
    try:
        record = store.get(session_id)
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    if record["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return store.update_messages(session_id, body.messages, title=body.title)


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    x_user_id: str = Header(default="anonymous"),
):
    store = require_sessions()
    try:
        record = store.get(session_id)
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    if record["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    store.delete(session_id)
    return {"deleted": True}


def _resolve_session_history(
    x_user_id: str,
    x_session_id: str | None,
    request_history: list[dict] | None,
) -> tuple[list[dict] | None, str | None]:
    """If X-Session-Id is provided, load that session's stored messages and use them
    as history (ignoring whatever the client sent in the request body). Returns
    (history, session_id_to_save_to). When no session id is provided, falls back to
    the stateless flow."""
    if not x_session_id:
        return request_history, None

    store = require_sessions()
    try:
        record = store.get(x_session_id)
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    if record["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return record["messages"], x_session_id


def _derive_title_from_history(messages: list[dict]) -> str | None:
    """First user message text → session title. Strips file-attachment markers."""
    for m in messages:
        if m.get("role") != "user":
            continue
        for p in (m.get("parts") or []):
            if not isinstance(p, dict):
                continue
            text = p.get("text")
            if not text:
                continue
            cleaned = text.split("[Attached File:")[0].strip()
            if cleaned:
                return cleaned[:50]
    return None


def _persist_session_history(session_id: str, serialized_history: list[dict]) -> None:
    # System prompt is reattached fresh every turn — don't store it.
    persistable = [m for m in serialized_history if m.get("role") != "system"]

    title = None
    try:
        existing = session_store.get(session_id)
        if not existing.get("title"):
            title = _derive_title_from_history(persistable)
    except SessionNotFound:
        return  # session deleted mid-turn

    session_store.update_messages(session_id, persistable, title=title)


@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
    x_session_id: str | None = Header(default=None),
):
    history, save_to_session = _resolve_session_history(
        x_user_id, x_session_id, request.history
    )

    async def generate():
        try:
            for event in agent.run(
                prompt=request.prompt,
                history=history,
                max_steps=5
            ):
                if event['type'] == 'model':
                    serialized = serialize_single_content(event['content'])
                    if serialized:
                        yield f"data: {json.dumps({'type': 'model', 'content': serialized})}\n\n"
                elif event['type'] == 'done':
                    turn_usage = event.get('usage')
                    usage_tracker.record(x_user_id, turn_usage)
                    serialized_history = serialize_content(event['history'])

                    if save_to_session:
                        _persist_session_history(save_to_session, serialized_history)

                    payload = {
                        'type': 'done',
                        'history': serialized_history,
                        'usage': serialize_usage(turn_usage),
                        'session_id': save_to_session,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                else:
                    yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
    x_session_id: str | None = Header(default=None),
):
    history, save_to_session = _resolve_session_history(
        x_user_id, x_session_id, request.history
    )

    try:
        final_history = []
        turn_usage = None
        for event in agent.run(prompt=request.prompt, history=history, max_steps=2):
            if event['type'] == 'done':
                final_history = event['history']
                turn_usage = event.get('usage')

        usage_tracker.record(x_user_id, turn_usage)
        serialized_history = serialize_content(final_history)

        if save_to_session:
            _persist_session_history(save_to_session, serialized_history)

        return {
            "history": serialized_history,
            "usage": serialize_usage(turn_usage),
            "daily_usage": usage_tracker.today(x_user_id),
            "session_id": save_to_session,
        }
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
