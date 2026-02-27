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
_llm = None    # ChatOpenAI
_agent = None  # GalateaAgent


def init_services(*, character_registry, unity_manager, web_manager, llm_model, llm_api_key, llm_base_url) -> None:
    """初始化服务层组件"""
    global _tts_server, _unity_process, _tts_service, _llm, _agent

    # ---- LangChain LLM 客户端 ----
    from langchain_openai import ChatOpenAI

    _llm = ChatOpenAI(
        model=llm_model,
        api_key=llm_api_key,
        base_url=llm_base_url,
        temperature=0.7,
        streaming=True,
    )

    # ---- Agent ----
    from app.agents import GalateaAgent

    _agent = GalateaAgent(llm=_llm)

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


def get_agent():
    """获取主聊天 Agent（GalateaAgent）"""
    return _agent
