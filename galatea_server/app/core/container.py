from app.infrastructure.managers.web_connection import WebConnectionManager
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.infrastructure.managers.session_manager import SessionManager
from app.infrastructure.processes.tts_server import TTSServer
from app.infrastructure.processes.unity_process import UnityProcess
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.services.tts_service import TTSService


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
