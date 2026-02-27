# AGENTS.md - Galatea Server

## Project Overview

AI Desktop Pet backend: Python 3.13 / FastAPI / LangGraph / PostgreSQL+pgvector.
Package manager: **uv** (not pip). No test suite exists yet.

## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run dev server (with hot reload)
uv run python run.py

# Run directly via uvicorn
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Add a dependency
uv add <package>
```

### Database

PostgreSQL with pgvector extension is required. Tables are auto-created on startup
via `Database.init_db()` (SQLAlchemy `create_all`). No Alembic migrations.

```bash
# DB connection is configured via .env:
# POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
```

### Testing

No test suite exists. If adding tests, use pytest:

```bash
uv add --dev pytest pytest-asyncio
uv run pytest                        # all tests
uv run pytest tests/test_foo.py      # single file
uv run pytest tests/test_foo.py::test_bar  # single test
```

### Linting

No linter is configured. If needed, use ruff:

```bash
uv add --dev ruff
uv run ruff check app/
uv run ruff format app/
```

## Architecture

```
app/
  main.py                  # FastAPI app factory, middleware, router mount
  core/
    config.py              # pydantic-settings BaseSettings, singleton `settings`
    events.py              # FastAPI lifespan (startup/shutdown)
    constants.py           # ErrorCode IntEnum + ERROR_MESSAGES dict
    logger.py              # get_logger(name) factory
  api/
    deps/                  # Dependency injection (module-level singletons)
      database.py          # Database, *Repository providers
      infrastructure.py    # ConnectionManagers, SessionManager, CharacterRegistry
      services.py          # LLM, Agent, TTS, Unity providers
      __init__.py          # init_dependencies(), shutdown_dependencies()
    v1/endpoints/          # Route handlers (session, websocket, tts, unity)
  agents/                  # LangGraph agent classes
    base.py                # BaseAgent ABC with astream_chat()
    galatea_agent.py       # GalateaAgent (START -> generation -> END)
  graphs/
    state.py               # AgentState TypedDict (messages with add_messages reducer)
    workflow_graph.py       # build_chat_graph() assembles StateGraph
    nodes/generation.py     # LLM generation node
  models/                  # SQLAlchemy ORM models (Base from DeclarativeBase)
    session.py             # DBSession (BigInteger PK autoincrement)
    message.py             # DBMessage (FK -> sessions, CASCADE delete)
    memory.py              # DBMemory (pgvector Vector(1536), importance 1-10)
  repositories/            # Data access layer (async, each takes session_factory)
  services/                # Business logic (agent_service, session_service, tts_*)
  schemas/                 # Pydantic models for API request/response
  infrastructure/
    database.py            # Database class (async engine + session_factory)
    managers/              # WebConnectionManager, UnityConnectionManager, SessionManager
    processes/             # TTSServer, UnityProcess (external process management)
  characters/              # Character data dirs (config.json, persona.toml, expressions.json)
  exceptions/              # GalateaException hierarchy with ErrorCode
  utils/                   # Helpers (prompts, audio, text_buffer, message_utils)
```

## Code Style

### Imports

Order: stdlib, third-party, local app. No blank lines between groups (project
convention). Prefer explicit imports over star imports (`from x import *` exists
in agent_service.py for web_protocol but should not be replicated).

```python
from typing import Optional, Dict, List
from sqlalchemy import BigInteger, String
from app.core.logger import get_logger
from app.models.session import DBSession
```

### Types & Annotations

- Use Python 3.13 built-in generics: `list[str]`, `dict[str, Any]`, `str | None`
- Use `Mapped[T]` with `mapped_column()` for SQLAlchemy models
- Use `TypedDict` for LangGraph state, `BaseModel` for Pydantic schemas
- Return type annotations on all public functions

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase` - `DBSession`, `SessionManager`, `GalateaAgent`
- **DB models**: Prefix with `DB` - `DBSession`, `DBMessage`, `DBMemory`
- **Repositories**: Suffix with `Repository` - `SessionRepository`
- **Exceptions**: Suffix with `Exception` - `SessionNotFoundException`
- **Functions/methods**: `snake_case` - `get_session`, `astream_chat`
- **Async functions**: Prefix with `a` only for LangChain convention (`ainvoke`, `astream_chat`)
- **Constants**: `UPPER_SNAKE_CASE` - `ERROR_MESSAGES`, `LOG_FORMAT`
- **Private/internal**: Prefix with `_` - `_sf`, `_database`, `_SENTENCE_ENDINGS`
- **Character dirs**: `snake_case` - `silver_wolf/`

### Dependency Injection

Module-level singletons in `app/api/deps/`. Each sub-module has:
- `_foo: Foo | None = None` private global
- `init_*()` function called once at startup
- `get_foo() -> Foo` provider function used with `Depends()`

```python
# In endpoint:
async def my_endpoint(
    session_manager: SessionManager = Depends(get_session_manager),
    session_repo: SessionRepository = Depends(get_session_repo),
):
```

### Error Handling

All business exceptions inherit from `GalateaException` (in `app/exceptions/base.py`).
Each domain has its own exception module (`session.py`, `tts.py`, `llm.py`).

```python
class SessionNotFoundException(SessionException):
    status_code = 404
    default_code = ErrorCode.SESSION_NOT_FOUND
```

Raise typed exceptions in service layer; FastAPI exception handlers convert them
to `UnifiedResponse` JSON.

### API Response Format

All REST endpoints return `UnifiedResponse[T]`:

```python
{"code": 200, "message": "success", "data": { ... }}
```

Use `UnifiedResponse.success(data=..., message=...)` to construct responses.

### Logging

Use `get_logger(__name__)` at module level. Log messages may use Chinese.
Emojis in log messages cause `UnicodeEncodeError` on Windows terminals (GBK encoding).

```python
logger = get_logger(__name__)
logger.info(f"Session created: {session_id}")
```

### Database

- Session IDs are `BigInteger` autoincrement in DB, converted to `str` in application code
- Repositories accept `async_sessionmaker` in constructor, manage their own sessions
- Each repo method opens its own `async with self._sf() as session:` block
- Use `ondelete="CASCADE"` for child tables, `ondelete="SET NULL"` for optional refs

### LangGraph Conventions

- State: `AgentState(TypedDict)` with `messages: Annotated[list[BaseMessage], add_messages]`
- Graph nodes: factory functions returning async closures (`create_generation_node(llm)`)
- Agent classes: inherit `BaseAgent`, implement `_build_graph() -> CompiledStateGraph`
- Streaming: use `graph.astream(..., stream_mode="messages")` and yield `AIMessageChunk.content`

## Critical Constraints

- **Do NOT change DB schema for `DBSession.id`** - it must remain `BigInteger` autoincrement
- **Do NOT rename**: `run.py` to `__main__.py`, `graphs/` to merge with `agents/`, or flatten `infrastructure/`
- **Do NOT fix**: Chinese filenames in character assets (intentional)
- **Windows platform**: paths use backslashes, terminal is GBK-encoded
- **Character config**: `config.json` uses `id` field matching directory name (e.g., `silver_wolf`)
