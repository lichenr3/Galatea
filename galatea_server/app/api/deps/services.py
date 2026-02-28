"""
Services 依赖注入（TTS、Unity 进程、Agent）
"""
from app.infrastructure.processes.tts_server import TTSServer
from app.infrastructure.processes.unity_process import UnityProcess
from app.services.tts_service import TTSService

_tts_server: TTSServer | None = None
_unity_process: UnityProcess | None = None
_tts_service: TTSService | None = None

# LangChain / Agent
_llm = None  # ChatOpenAI
_agent = None  # GalateaAgent
_embeddings = None  # OpenAIEmbeddings
_mini_llm = None  # ChatOpenAI (for query rewrite/memory extraction)



def init_services(
    *,
    character_registry,
    unity_manager,
    web_manager,
    llm_model,
    llm_api_key,
    llm_base_url,
    embedding_model: str = "text-embedding-3-small",
    embedding_api_key: str | None = None,
    embedding_base_url: str | None = None,
    mini_llm_model: str | None = None,
    mini_llm_api_key: str | None = None,
    mini_llm_base_url: str | None = None,
) -> None:
    """初始化服务层组件"""
    global _tts_server, _unity_process, _tts_service, _llm, _agent, _embeddings, _mini_llm

    # ---- LangChain LLM 客户端 ----
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    _llm = ChatOpenAI(
        model=llm_model,
        api_key=llm_api_key,
        base_url=llm_base_url,
        temperature=0.7,
        streaming=True,
    )

    # ---- Embeddings（用于向量检索）----
    _embeddings = OpenAIEmbeddings(
        model=embedding_model,
        api_key=embedding_api_key,
        base_url=embedding_base_url,
    )

    # ---- Mini LLM (用于小任务如 Query Rewrite) ----
    if mini_llm_model and mini_llm_api_key:
        _mini_llm = ChatOpenAI(
            model=mini_llm_model,
            api_key=mini_llm_api_key,
            base_url=mini_llm_base_url,
            temperature=0.3,
            streaming=False,
        )
    else:
        # Fallback to main LLM if mini is not configured
        _mini_llm = _llm

    # ---- Agent（需要 LLM + Embeddings + MemoryRepo + Mini LLM）----
    from app.agents import GalateaAgent
    from app.api.deps.database import get_memory_repo

    memory_repo = get_memory_repo()
    _agent = GalateaAgent(llm=_llm, mini_llm=_mini_llm, embeddings=_embeddings, memory_repo=memory_repo)

    # ---- 外部进程 ----
    _tts_server = TTSServer()
    _unity_process = UnityProcess()

    # ---- Services ----
    _tts_service = TTSService(
        character_registry=character_registry,
        unity_manager=unity_manager,
        web_manager=web_manager,
    )


def get_tts_server() -> TTSServer:
    return _tts_server


def get_unity_process() -> UnityProcess:
    return _unity_process


def get_tts_service() -> TTSService:
    return _tts_service


def get_llm():
    """获取 LangChain LLM 客户端（ChatOpenAI 单例）"""
    return _llm


def get_embeddings():
    """获取 OpenAI Embeddings 实例"""
    return _embeddings


def get_agent():
    """获取主聊天 Agent（GalateaAgent）"""
    return _agent

def get_mini_llm():
    """获取 Mini LLM 客户端（用于后台小任务）"""
    return _mini_llm
