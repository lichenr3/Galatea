"""
Application Dependency Injection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

所有单例在 app 启动时由 init_dependencies() 统一创建。
Endpoint 通过 get_xxx() + FastAPI Depends() 获取依赖。
"""
from app.core.config import settings
from app.infrastructure.managers.web_connection import WebConnectionManager
from app.infrastructure.managers.unity_connection import UnityConnectionManager
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
_tts_service: TTSService | None = None
_llm_service: LLMService | None = None

# Database
_database: Database | None = None
_session_repo: SessionRepository | None = None
_message_repo: MessageRepository | None = None
_memory_repo: MemoryRepository | None = None

# LangChain / Agent
_llm = None    # ChatOpenAI — LangChain LLM 客户端单例
_agent = None  # GalateaAgent — 主聊天 Agent


async def init_dependencies() -> None:
    """
    初始化所有应用级单例。在 app lifespan startup 阶段调用一次。
    """
    global _web_manager, _unity_manager, _character_registry
    global _tts_server, _unity_process
    global _tts_service, _llm_service
    global _database, _session_repo, _message_repo, _memory_repo
    global _llm, _agent

    # ---- Database ----
    _database = Database(settings.DATABASE_URL)
    await _database.init_db()

    _session_repo = SessionRepository(_database.session_factory)
    _message_repo = MessageRepository(_database.session_factory)
    _memory_repo = MemoryRepository(_database.session_factory)

    # ---- LangChain LLM 客户端 ----
    from langchain_openai import ChatOpenAI

    _llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.7,
        streaming=True,
    )

    # ---- Agent ----
    from app.agents import GalateaAgent

    _agent = GalateaAgent(llm=_llm)

    # ---- Infrastructure（无依赖）----
    _web_manager = WebConnectionManager()
    _unity_manager = UnityConnectionManager()
    _character_registry = CharacterRegistry()

    # ---- 外部进程（无依赖）----
    _tts_server = TTSServer()
    _unity_process = UnityProcess()

    # ---- Services（依赖 infrastructure）----
    _tts_service = TTSService(
        character_registry=_character_registry,
        unity_manager=_unity_manager,
        web_manager=_web_manager,
    )
    _llm_service = LLMService()


async def shutdown_dependencies() -> None:
    """清理资源。在 app lifespan shutdown 阶段调用。"""
    if _database:
        await _database.close()


# ---- Dependency provider functions (FastAPI Depends()) ----

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

def get_llm():
    """获取 LangChain LLM 客户端（ChatOpenAI 单例）"""
    return _llm

def get_agent():
    """获取主聊天 Agent（GalateaAgent）"""
    return _agent
