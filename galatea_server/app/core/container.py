from app.infrastructure.managers.web_connection import WebConnectionManager
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.infrastructure.managers.session_manager import SessionManager
from app.infrastructure.processes.tts_server import TTSServer
from app.infrastructure.processes.unity_process import UnityProcess
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.services.tts_service import TTSService
from app.core.config import settings


# 创建底层的 Infrastructure (无依赖)
web_manager = WebConnectionManager()
unity_manager = UnityConnectionManager()
character_registry = CharacterRegistry()

# 创建外部 Process (无依赖)
tts_server = TTSServer()
unity_process = UnityProcess()

# 创建 Service (依赖 character_registry 等)
session_manager = SessionManager(character_registry=character_registry)
tts_service = TTSService(character_registry=character_registry, unity_manager=unity_manager, web_manager=web_manager)


# ============================================================
# LangGraph Checkpointer (会话状态持久化)
# ============================================================
from app.memory.checkpointer import checkpointer_manager

# ============================================================
# Memory Store (向量数据库)
# ============================================================
def _create_memory_store():
    """根据配置创建 Memory Store"""
    backend = settings.MEMORY_BACKEND
    
    if backend == "chroma":
        from app.memory.chroma_store import ChromaMemoryStore
        return ChromaMemoryStore()
    elif backend == "none":
        return None
    else:
        # 默认使用 Chroma
        from app.memory.chroma_store import ChromaMemoryStore
        return ChromaMemoryStore()


# 延迟初始化，避免启动时就加载向量库
_memory_store = None


def get_memory_store():
    """获取 Memory Store 实例（延迟初始化）"""
    global _memory_store
    if _memory_store is None and settings.MEMORY_BACKEND != "none":
        _memory_store = _create_memory_store()
    return _memory_store
