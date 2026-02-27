"""
Infrastructure 依赖注入（连接管理器、角色注册表）
"""
from app.infrastructure.managers.web_connection import WebConnectionManager
from app.infrastructure.managers.unity_connection import UnityConnectionManager
from app.infrastructure.managers.character_registry import CharacterRegistry

_web_manager: WebConnectionManager | None = None
_unity_manager: UnityConnectionManager | None = None
_character_registry: CharacterRegistry | None = None


def init_infrastructure() -> None:
    """初始化基础设施组件"""
    global _web_manager, _unity_manager, _character_registry

    _web_manager = WebConnectionManager()
    _unity_manager = UnityConnectionManager()
    _character_registry = CharacterRegistry()


def get_web_manager() -> WebConnectionManager:
    return _web_manager


def get_unity_manager() -> UnityConnectionManager:
    return _unity_manager


def get_character_registry() -> CharacterRegistry:
    return _character_registry
