"""
Application Dependency Injection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

所有单例在 app 启动时由 init_dependencies() 统一创建。
Endpoint 通过 get_xxx() + FastAPI Depends() 获取依赖。
"""
from app.core.config import settings
from app.infrastructure.managers.web_connection import WebConnectionManager
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.infrastructure.managers.session_manager import SessionManager
from app.infrastructure.processes.tts_server import TTSServer
from app.infrastructure.processes.unity_process import UnityProcess
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.services.tts_service import TTSService
from app.services.llm_service import LLMService
from app.infrastructure.database import Database
from app.repositories import SessionRepository, MessageRepository, MemoryRepository


# Module-level singletons — 由 init_dependencies() 初始化
_web_manager: WebConnectionManager | None = None
_unity_manager: UnityConnectionManager | None = None
_character_registry: CharacterRegistry | None = None
_tts_server: TTSServer | None = None
_unity_process: UnityProcess | None = None
_session_manager: SessionManager | None = None
_tts_service: TTSService | None = None
_llm_service: LLMService | None = None

# Database
_database: Database | None = None
_session_repo: SessionRepository | None = None
_message_repo: MessageRepository | None = None
_memory_repo: MemoryRepository | None = None

# LangGraph
_checkpointer_conn = None  # psycopg.AsyncConnection
_checkpointer = None        # AsyncPostgresSaver
_chat_graph = None           # CompiledStateGraph


async def init_dependencies() -> None:
    """
    初始化所有应用级单例。在 app lifespan startup 阶段调用一次。
    """
    global _web_manager, _unity_manager, _character_registry
    global _tts_server, _unity_process
    global _session_manager, _tts_service, _llm_service
    global _database, _session_repo, _message_repo, _memory_repo
    global _checkpointer_conn, _checkpointer, _chat_graph

    # ---- Database ----
    _database = Database(settings.DATABASE_URL)
    await _database.init_db()

    _session_repo = SessionRepository(_database.session_factory)
    _message_repo = MessageRepository(_database.session_factory)
    _memory_repo = MemoryRepository(_database.session_factory)

    # ---- LangGraph Checkpointer (PostgreSQL) ----
    from psycopg import AsyncConnection
    from psycopg.rows import dict_row
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    _checkpointer_conn = await AsyncConnection.connect(
        settings.DATABASE_URL_PSYCOPG,
        autocommit=True,
        row_factory=dict_row,
    )
    _checkpointer = AsyncPostgresSaver(_checkpointer_conn)
    await _checkpointer.setup()  # 首次运行时创建 checkpoint 表

    # ---- LangGraph Chat Graph ----
    from langchain_openai import ChatOpenAI
    from app.graphs.workflow_graph import build_chat_graph

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.7,
        streaming=True,
    )
    _chat_graph = build_chat_graph(llm, _checkpointer)

    # ---- Infrastructure（无依赖）----
    _web_manager = WebConnectionManager()
    _unity_manager = UnityConnectionManager()
    _character_registry = CharacterRegistry()

    # ---- 外部进程（无依赖）----
    _tts_server = TTSServer()
    _unity_process = UnityProcess()

    # ---- Services（依赖 infrastructure）----
    _session_manager = SessionManager(character_registry=_character_registry)
    _tts_service = TTSService(
        character_registry=_character_registry,
        unity_manager=_unity_manager,
        web_manager=_web_manager,
    )
    _llm_service = LLMService()

    # ---- 从 DB 恢复会话到内存 ----
    await _restore_sessions_from_db()


async def shutdown_dependencies() -> None:
    """清理资源。在 app lifespan shutdown 阶段调用。"""
    if _checkpointer_conn:
        await _checkpointer_conn.close()
    if _database:
        await _database.close()


async def _restore_sessions_from_db() -> None:
    """从数据库恢复已有会话到内存 SessionManager"""
    from app.core.logger import get_logger
    logger = get_logger(__name__)

    db_sessions = await _session_repo.get_all_ordered()  # last_active DESC
    if not db_sessions:
        logger.info("🗄️  No sessions to restore from database")
        return

    for db_session in db_sessions:
        # 加载该会话的 system prompt + 最近 20 条消息
        db_messages = await _message_repo.get_recent_with_system(db_session.id, limit=20)
        messages = [{"role": m.role, "content": m.content} for m in db_messages]

        _session_manager.load_session(
            session_id=str(db_session.id),  # DB int → 内存 str
            character_id=db_session.character_id,
            messages=messages,
            created_at=db_session.created_at,
            last_active=db_session.last_active,
        )

    logger.info(f"✅ Restored {len(db_sessions)} sessions from database")


# ---- Dependency provider functions (FastAPI Depends()) ----

def get_session_manager() -> SessionManager:
    return _session_manager

def get_web_manager() -> WebConnectionManager:
    return _web_manager

def get_unity_manager() -> UnityConnectionManager:
    return _unity_manager

def get_character_registry() -> CharacterRegistry:
    return _character_registry

def get_tts_server() -> TTSServer:
    return _tts_server

def get_unity_process() -> UnityProcess:
    return _unity_process

def get_tts_service() -> TTSService:
    return _tts_service

def get_llm_service() -> LLMService:
    return _llm_service

def get_database() -> Database:
    return _database

def get_session_repo() -> SessionRepository:
    return _session_repo

def get_message_repo() -> MessageRepository:
    return _message_repo

def get_memory_repo() -> MemoryRepository:
    return _memory_repo

def get_chat_graph():
    """获取编译后的 LangGraph 聊天图（CompiledStateGraph）"""
    return _chat_graph
