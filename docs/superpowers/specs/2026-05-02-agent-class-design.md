# Agent Class Design with In-Memory SQLite Short-Term Memory

## Goal
Design an `Agent` class that owns orchestration logic (system prompt, LLM usage, tool execution, and short-term SQLite memory) while staying beginner-friendly and aligned with the minimal-churn backend layout. The first version uses SQLite `":memory:"`, so memory exists only during the current process.

## Architecture

### `Agent` class (`backend/agent.py`)
- Orchestrates the agent loop: system prompt, tool calls, LLM interaction
- Stores conversation history in SQLite via a small internal helper
- Exposes a simple public API: `Agent(system_prompt, llm, session_id)` and `agent.run(user_input)`

### SQLite short-term memory (internal to `Agent`)
- Single `messages` table storing role, content, message_type, session_id, timestamp
- Loads recent messages for context window
- Uses SQLite `":memory:"`, so the conversation history is kept only while the process is running

### Tool registry (`backend/agent_tools/__init__.py`)
- Already exists in the folder reorganization spec
- `Agent` imports `TOOLS` from here

## Class Structure

```python
class Agent:
    def __init__(
        self,
        system_prompt: str,
        llm: LLMWrapper,
        session_id: str = "default"
    ):
        self.system_prompt = system_prompt
        self.llm = llm
        self.session_id = session_id
        self._init_db()
    
    def run(self, user_input: str, max_steps: int = 5) -> str:
        """Main entry point: run agent loop and return final text."""
        pass
    
    def _init_db(self):
        """Create messages table if it doesn't exist."""
        pass
    
    def _load_history(self, limit: int = 20) -> list:
        """Load recent messages from SQLite for this session."""
        pass
    
    def _save_message(self, role: str, content: Any, message_type: str = "text"):
        """Save a message to SQLite."""
        pass
    
    def _build_contents(self, user_input: str) -> list:
        """Build LLM context: system prompt + history + new user input."""
        pass
    
    def _execute_tools(self, function_calls: list) -> list:
        """Execute tool calls and return tool response parts."""
        pass
```

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_created 
ON messages(session_id, created_at);
```

**Fields:**
- `session_id`: groups messages by conversation session
- `role`: "user", "assistant", "tool"
- `content`: JSON-serialized message content
- `message_type`: "text", "function_call", "function_response"
- `created_at`: timestamp for ordering

## Data Flow

1. User calls `agent.run("What is 15 * 3?")`
2. Agent loads recent history from SQLite for this session
3. Agent builds context: system prompt + history + new user message
4. Agent calls `llm.generate(contents, tool_definitions)`
5. If function calls exist:
   - Execute tools via tool registry
   - Save tool calls and responses to SQLite
   - Append to context and call LLM again
6. Repeat until no more function calls or max_steps reached
7. Save final assistant message to SQLite
8. Return final text to caller
9. When the process exits, the in-memory SQLite history is discarded

## Integration with Existing Code

**Changes to `backend/main.py`:**
- Replace `agent_loop()` with `Agent` class usage
- Keep tool registry decorator pattern or migrate to `agent_tools/__init__.py`

**Changes to `backend/agent.py`:**
- Replace stub with full `Agent` implementation

**No changes to:**
- `llm_wrapper.py`
- `agent_tools/calculator.py`

## Out of Scope

- Long-term memory
- Memory summarization
- Vector search or embeddings
- Multi-session management UI
- Memory cleanup/pruning
- Persistence across runs

## Success Criteria

- `Agent` class encapsulates orchestration logic cleanly
- SQLite `":memory:"` stores conversation history during the process lifetime
- Tool execution integrates with the existing tool registry
- Public API is simple: `agent.run("prompt")` returns final text
- Implementation stays within `backend/agent.py`
