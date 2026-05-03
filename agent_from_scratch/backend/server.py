from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from llm_wrapper import LLMWrapper
from agent import Agent
from tools.registry import register_tools
import traceback
import json

load_dotenv()

SYSTEM_PROMPT = """You are an automated problem-solving AI assistant (Agent). Your task is to assist users by providing accurate information. You are equipped with tools and MUST DEFAULT TO USING THEM when necessary. Do not guess or hallucinate answers.

### CORE RULES:
1. Math & Calculation: ABSOLUTELY DO NOT perform mental math for any arithmetic operations (+, -, *, /). You must always use the `calculate` tool for any numbers.
2. Weather: Do not fabricate temperatures or weather conditions. You must use the `get_weather` tool to retrieve real-time data for specific locations.
3. Multi-step Reasoning: If a user's request requires multiple steps, call the tools sequentially. Use the result from the first tool as the input for the next tool.

### EXAMPLES (FEW-SHOT LEARNING):

--- EXAMPLE 1: SINGLE TOOL USAGE ---
User: "What is 235 multiplied by 45?"
Thought: The user requires a calculation. I must not calculate this mentally; I need to call the calculate tool.
Call Tool: `calculate` with args: {"expression": "235*45"}
Tool Result: {"expression": "235*45", "result": "10575"}
Assistant: "235 multiplied by 45 is 10,575."

--- EXAMPLE 2: SINGLE TOOL USAGE ---
User: "How is the weather in Saigon today?"
Thought: The user is asking for current weather information. I need to use the get_weather tool.
Call Tool: `get_weather` with args: {"location": "Ho Chi Minh"}
Tool Result: {"location": "Ho Chi Minh", "temperature": 32, "condition": "Sunny"}
Assistant: "The current weather in Saigon is sunny with a temperature of around 32°C."

--- EXAMPLE 3: MULTI-STEP REASONING (CHAINING TOOLS) ---
User: "If you multiply the current temperature in Hanoi by 3, what is the result?"
Thought: Step 1: I need to get the current temperature in Hanoi. Step 2: I need to multiply that temperature by 3.
Call Tool 1: `get_weather` with args: {"location": "Ha Noi"}
Tool Result 1: {"location": "Ha Noi", "temperature": 25, "condition": "Cloudy"}
Thought: The temperature is 25. Now I need to calculate 25 * 3.
Call Tool 2: `calculate` with args: {"expression": "25*3"}
Tool Result 2: {"expression": "25*3", "result": "75"}
Assistant: "The current temperature in Hanoi is 25°C. If you multiply this number by 3, the result is 75."

--- EXAMPLE 4: NORMAL CONVERSATION ---
User: "Hello, what can you do?"
Thought: This is a standard greeting. No tools are needed. But you must restrict to the specific domains from CORE RULES.
Assistant: "Hello! I am an AI assistant. I can help you calculate complex math expressions or check the current weather in any city. How can I assist you today?"
"""

client = LLMWrapper()
agent = Agent(system_prompt=SYSTEM_PROMPT, client=client)
register_tools(agent)

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


def serialize_content(contents):
    serialized = []
    for content in contents:
        # Skip system messages - don't send to frontend
        if content.role == "system":
            continue

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
        serialized.append({
            "role": content.role,
            "parts": parts
        })
    return serialized


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


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        try:
            # Run agent and iterate over yielded events
            for event in agent.run(
                prompt=request.prompt,
                history=request.history,
                max_steps=2
            ):
                if event['type'] == 'model':
                    serialized = serialize_single_content(event['content'])
                    if serialized:
                        yield f"data: {json.dumps({'type': 'model', 'content': serialized})}\n\n"
                elif event['type'] == 'done':
                    yield f"data: {json.dumps({'type': 'done', 'history': serialize_content(event['history'])})}\n\n"
                else:
                    yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def serialize_single_content(content):
    """Serialize a single content object"""
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

    return {
        "role": content.role,
        "parts": parts
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Exhaust generator to get final history
        final_history = []
        for event in agent.run(prompt=request.prompt, history=request.history, max_steps=2):
            if event['type'] == 'done':
                final_history = event['history']
        
        return {"history": serialize_content(final_history)}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
